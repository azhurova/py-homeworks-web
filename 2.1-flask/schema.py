from typing import Optional

import pydantic


class DefaultValidateSchema(pydantic.BaseModel):
    pass


class CreateUser(pydantic.BaseModel):
    name: str
    password: str

    @classmethod
    @pydantic.field_validator('password')
    def secure_password(cls, value: str) -> str:
        min_len = 8
        max_len = 32
        if len(value) < min_len:
            raise ValueError(f'Минимальная длина пароля {min_len} символов')
        if len(value) > max_len:
            raise ValueError(f'Максимальная длина пароля {max_len} символов')
        return value


class PatchUser(CreateUser):
    name: Optional[str] = None
    password: Optional[str] = None


class CreateSticker(pydantic.BaseModel):
    title: str
    description: str
    owner_id: int


class PatchSticker(CreateSticker):
    title: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None
