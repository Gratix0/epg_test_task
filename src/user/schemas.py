from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    gender: str
    pic_url: str = None

class User(BaseModel):
    username: str

class UserInDB(User):
    hashed_password: str
