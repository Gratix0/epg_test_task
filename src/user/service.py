from fastapi import  HTTPException, status
from passlib.context import CryptContext

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from .models import Users
from .schemas import UserCreate, UserInDB
from ..database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ===========================
# User Operations
# ===========================

async def create_user(user: UserCreate, db: AsyncSession):
    new_user = Users(**user.dict())
    # new_user.password = get_password_hash(new_user.password)
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this login already exists."
        )
    return {"status": 201, "data": new_user}


async def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user(db: AsyncSession, email: str):
    result = await db.execute(select(Users).where(Users.email == email))
    return result.scalars().first()

async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user(db, username)
    if not user:
        return False
    if not await verify_password(password, user.password):
        return False
    return user
