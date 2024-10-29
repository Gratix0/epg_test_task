from fastapi import UploadFile
from pydantic import BaseModel, EmailStr

class UserInApi(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    gender: str

class UserCreate(UserInApi):
    pic_url: str

class User(BaseModel):
    username: str

class UserInDB(User):
    hashed_password: str

class AvatarUser(BaseModel):
    avatar: UploadFile = None
