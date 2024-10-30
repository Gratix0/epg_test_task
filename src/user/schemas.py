from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    email: EmailStr

class UserInApiForCreate(User):
    first_name: str
    last_name: str
    password: str
    gender: str

class UserCreate(UserInApiForCreate):
    pic_url: Optional[str] = Field(None)

class UserDB(UserCreate):
    id: int

class UserAuth(User):
    password: str



# ===========================
# JWT and Auth
# ===========================

class Token(BaseModel):
    access_token: str  # Поле для токена доступа
    token_type: str  # Тип токена (например, Bearer)

class TokenData(BaseModel):
    username: Optional[str] = None  # Имя пользователя из токена (может отсутствовать)

# ===========================
# Match point
# ===========================

class MatchBase(BaseModel):
    user_id: int
    matched_user_id: int
    liked: bool = False
    user: User
    matched_user: User

class MatchCreate(MatchBase):
    pass

class Match(MatchBase):
    id: int

    class Config:
        orm_mode = True