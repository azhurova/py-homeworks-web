import json
from typing import Type

from aiohttp import web
from aiohttp_basicauth import BasicAuthMiddleware
import bcrypt
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models import User, Sticker, Session, init_db, engine
from schema import DefaultValidateSchema, CreateUser, PatchUser, CreateSticker, PatchSticker


class CustomBasicAuth(BasicAuthMiddleware):
    async def check_credentials(self, username, password, request):
        async with Session() as session:
            query_result = await session.execute(select(User).where(User.name == username).limit(1))
            if not query_result.closed:
                user = query_result.scalar()
        if not user or not check_password(password, user.password):
            request.user_id = None
            return False

        request.user_id = user.id
        return True


auth = CustomBasicAuth()
app = web.Application()


async def orm_context(app: web.Application):
    await init_db()
    async with Session() as session:
        query_result = await session.execute(select(User).where(User.name == 'user1').limit(1))
        if not query_result.closed:
            user = query_result.scalar()
        if not user:
            user = User(name='user1', password=hash_password('user1'))
            session.add(user)
            await session.commit()
    yield
    await engine.dispose()


@web.middleware
async def session_middleware(request: web.Request, handler):
    async with Session() as session:
        request.session = session
        response = await handler(request)
        return response


app.cleanup_ctx.append(orm_context)
app.middlewares.append(auth)
app.middlewares.append(session_middleware)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def get_http_error(error_class: Type[web.HTTPClientError], message: str):
    return error_class(text=json.dumps({'error': message}), content_type='application/json')


def validate(model, data):
    try:
        return model.model_validate(data).model_dump(exclude_unset=True)
    except ValidationError as err:
        error = err.errors()[0]
        error.pop('ctx', None)
        raise get_http_error(web.HTTPBadRequest, error)


class ObjectView(web.View):
    @property
    def session(self) -> Session:
        return self.request.session

    def object_description(self) -> str:
        return ''

    def object_model(self):
        return None

    async def get_object(self, object_id):
        model = self.object_model()
        obj = await self.session.get(model, object_id)
        if obj is None:
            desc = self.object_description()
            if not desc:
                desc = self.__name__
            raise get_http_error(web.HTTPNotFound, f'{desc} [id={object_id}] не найден')
        return obj

    def get_object_json_response(self, instance):
        return None

    async def commit_object(self, instance):
        try:
            self.session.add(instance)
            await self.session.commit()
        except IntegrityError as err:
            desc = self.object_description()
            if not desc:
                desc = self.__name__
            raise get_http_error(web.HTTPBadRequest, f'{desc} уже существует')
        return instance

    async def get(self):
        object_id = int(self.request.match_info.get('object_id'))
        obj = await self.get_object(object_id)
        return self.get_object_json_response(obj)

    def validate_shema(self) -> dict:
        return {'post': DefaultValidateSchema, 'patch': DefaultValidateSchema}

    def post_after_validate(self, data):
        return data

    def post_after_create(self, obj):
        return obj

    # @auth.required
    async def post(self):
        object_data = validate(self.validate_shema()['post'], await self.request.json())
        object_data = self.post_after_validate(object_data)
        model_class = self.object_model()
        new_object = model_class(**object_data)
        new_object = self.post_after_create(new_object)
        await self.commit_object(new_object)
        return self.get_object_json_response(new_object)

    def patch_after_validate(self, data):
        return data

    def before_patch(self, obj):
        return obj

    @auth.required
    async def patch(self):
        object_id = int(self.request.match_info.get('object_id'))
        object_data = validate(self.validate_shema()['patch'], await self.request.json())
        object_data = self.patch_after_validate(object_data)
        obj = await self.get_object(object_id)
        obj = self.before_patch(obj)
        for key, value in object_data.items():
            setattr(obj, key, value)
        await self.commit_object(obj)
        return self.get_object_json_response(obj)

    def before_delete(self, data):
        return data

    @auth.required
    async def delete(self):
        object_id = int(self.request.match_info.get('object_id'))
        obj = await self.get_object(object_id)
        obj = self.before_delete(obj)
        await self.session.delete(obj)
        await self.session.commit()
        return web.json_response({'status': 'ok'})


class UserView(ObjectView):
    def object_description(self) -> str:
        return 'Пользователь'

    def object_model(self):
        return User

    def get_object_json_response(self, instance):
        return web.json_response(
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

    def check_user_access(self, object_id, user_id, action_text):
        if user_id != self.request.user_id:
            raise get_http_error(web.HTTPForbidden,
                                 f'Нельзя {action_text} пользователя [id={object_id}] пользователю [user_id={self.request.user_id}]')
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

    def get_object_json_response(self, instance):
        return web.json_response({'id': instance.id, 'name': instance.title, 'description': instance.description,
                                  'owner_id': instance.owner_id,
                                  'create_datetime': instance.create_datetime.isoformat()})

    def validate_shema(self) -> dict:
        return {'post': CreateSticker, 'patch': PatchSticker}

    def post_after_create(self, obj):
        obj.owner_id = self.request.user_id
        return obj

    def patch_after_validate(self, data):
        if 'owner_id' in data:
            del data['owner_id']
        return data

    def check_owner_access(self, object_id, owner_id, action_text):
        if owner_id != self.request.user_id:
            raise get_http_error(web.HTTPForbidden,
                                 f'Нельзя {action_text} объявление [id={object_id}] пользователю [user_id={self.request.user_id}]')
        return True

    def before_patch(self, obj):
        self.check_owner_access(obj.id, obj.owner_id, 'изменить')
        return obj

    def before_delete(self, data):
        self.check_owner_access(data.id, data.owner_id, 'удалить')
        return data


app.add_routes([web.get('/user/{object_id:\d+}', UserView), web.patch('/user/{object_id:\d+}', UserView),
                web.delete('/user/{object_id:\d+}', UserView), web.post('/user/', UserView),
                web.get('/sticker/{object_id:\d+}', StickerView), web.patch('/sticker/{object_id:\d+}', StickerView),
                web.delete('/sticker/{object_id:\d+}', StickerView), web.post('/sticker/', StickerView), ])

if __name__ == '__main__':
    web.run_app(app)
