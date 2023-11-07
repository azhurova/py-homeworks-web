import flask
from flask import jsonify, request, Response
from flask.views import MethodView
from http import HTTPStatus
from flask_httpauth import HTTPBasicAuth

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from flask_bcrypt import Bcrypt

from models import Session, User, Sticker
from schema import DefaultValidateSchema, CreateUser, PatchUser, CreateSticker, PatchSticker

app = flask.Flask('app')
auth = HTTPBasicAuth()
bcrypt = Bcrypt(app)


def hash_password(password: str) -> str:
    password = password.encode()
    return bcrypt.generate_password_hash(password).decode()


def check_password(password: str, hashed_password: str) -> bool:
    password = password.encode()
    hashed_password = hashed_password.encode()
    return bcrypt.check_password_hash(password, hashed_password)


class HTTPException(Exception):
    def __init__(self, code: int, description: str):
        self.code = code
        self.description = description


@app.errorhandler(HTTPException)
def error_handler(error):
    response = jsonify({'error': error.description})
    response.status_code = error.code
    return response


@auth.verify_password
def verify_password(username, password):
    user = request.session.query(User).filter(User.name == username).first()
    if not user or not check_password(user.password, password):
        request.user_id = None
        return False

    request.user_id = user.id
    return True


@app.before_request
def before_request():
    session = Session()
    request.session = session


@app.after_request
def after_request(response: Response):
    request.session.close()
    return response


def validate(model, data):
    try:
        return model.model_validate(data).model_dump(exclude_unset=True)
    except ValidationError as err:
        error = err.errors()[0]
        error.pop('ctx', None)
        raise HTTPException(400, error)


class ObjectView(MethodView):
    @property
    def session(self) -> Session:
        return request.session

    def object_description(self) -> str:
        return ''

    def object_model(self):
        return None

    def get_object(self, object_id: int):
        model = self.object_model()
        obj = self.session.get(model, object_id)
        if obj is None:
            desc = self.object_description()
            if not desc:
                desc = self.__name__
            raise HTTPException(HTTPStatus.NOT_FOUND, f'{desc} [id={object_id}] не найден')
        return obj

    def get_object_jsonify(self, instance):
        return None

    def commit_object(self, instance):
        try:
            self.session.add(instance)
            self.session.commit()
        except IntegrityError as err:
            desc = self.object_description()
            if not desc:
                desc = self.__name__
            raise HTTPException(HTTPStatus.BAD_REQUEST, f'{desc} уже существует')
        return instance

    def get(self, object_id: int):
        obj = self.get_object(object_id)
        return self.get_object_jsonify(obj)

    def validate_shema(self) -> dict:
        return {'post': DefaultValidateSchema, 'patch': DefaultValidateSchema}

    def post_after_validate(self, data):
        return data

    def post_after_create(self, obj):
        return obj

    @auth.login_required
    def post(self):
        object_data = validate(self.validate_shema()['post'], request.json)
        object_data = self.post_after_validate(object_data)
        model_class = self.object_model()
        new_object = model_class(**object_data)
        new_object = self.post_after_create(new_object)
        self.commit_object(new_object)
        return self.get_object_jsonify(new_object)

    def patch_after_validate(self, data):
        return data

    def before_patch(self, obj):
        return obj

    @auth.login_required
    def patch(self, object_id: int):
        object_data = validate(self.validate_shema()['patch'], request.json)
        object_data = self.patch_after_validate(object_data)
        obj = self.get_object(object_id)
        obj = self.before_patch(obj)
        for key, value in object_data.items():
            setattr(obj, key, value)
        self.commit_object(obj)
        return self.get_object_jsonify(obj)

    def before_delete(self, data):
        return data

    @auth.login_required
    def delete(self, object_id: int):
        obj = self.get_object(object_id)
        obj = self.before_delete(obj)
        self.session.delete(obj)
        self.session.commit()
        return jsonify({'status': 'ok'})


class UserView(ObjectView):
    def object_description(self) -> str:
        return 'Пользователь'

    def object_model(self):
        return User

    def get_object_jsonify(self, instance):
        return jsonify(
            {'id': instance.id, 'name': instance.name, 'create_datetime': instance.create_datetime.isoformat()})

    def validate_shema(self) -> dict:
        return {'post': CreateUser, 'patch': PatchUser}

    def post_after_validate(self, data):
        data['password'] = hash_password(data['password'])
        return data

    def patch_after_validate(self, data):
        if 'password' in data:
            data['password'] = hash_password(data['password'])
        return data

    @staticmethod
    def check_user_access(object_id, user_id, action_text):
        if user_id != request.user_id:
            raise HTTPException(HTTPStatus.FORBIDDEN,
                                f'Нельзя {action_text} пользователя [id={object_id}] пользователю [user_id={request.user_id}]')
        return True

    def before_patch(self, obj):
        self.check_user_access(obj.id, obj.id, 'изменить')
        return obj

    def before_delete(self, data):
        self.check_user_access(data.id, data.id, 'удалить')
        return data


class StickerView(ObjectView):
    def object_description(self) -> str:
        return 'Объявление'

    def object_model(self):
        return Sticker

    def get_object_jsonify(self, instance):
        return jsonify({'id': instance.id, 'name': instance.title, 'description': instance.description,
                        'owner_id': instance.owner_id, 'create_datetime': instance.create_datetime.isoformat()})

    def validate_shema(self) -> dict:
        return {'post': CreateSticker, 'patch': PatchSticker}

    def post_after_create(self, obj):
        obj.owner_id = request.user_id
        return obj

    def patch_after_validate(self, data):
        if 'owner_id' in data:
            del data['owner_id']
        return data

    @staticmethod
    def check_owner_access(object_id, owner_id, action_text):
        if owner_id != request.user_id:
            raise HTTPException(HTTPStatus.FORBIDDEN,
                                f'Нельзя {action_text} объявление [id={object_id}] пользователю [user_id={request.user_id}]')
        return True

    def before_patch(self, obj):
        self.check_owner_access(obj.id, obj.owner_id, 'изменить')
        return obj

    def before_delete(self, data):
        self.check_owner_access(data.id, data.owner_id, 'удалить')
        return data


user_view = UserView.as_view('user_view')
sticker_view = StickerView.as_view('sticker_view')

app.add_url_rule('/user/<int:object_id>/', view_func=user_view, methods=['GET', 'PATCH', 'DELETE'])
app.add_url_rule('/user/', view_func=user_view, methods=['POST'])

app.add_url_rule('/sticker/<int:object_id>/', view_func=sticker_view, methods=['GET', 'PATCH', 'DELETE'])
app.add_url_rule('/sticker/', view_func=sticker_view, methods=['POST'])

if __name__ == '__main__':
    app.run(debug=True)
