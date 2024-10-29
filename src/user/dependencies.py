from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from epg_test_task.src.database import get_db
from epg_test_task.src.user.models import Users
from epg_test_task.src.user.schemas import UserCreate

async def check_unique_email(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Проверка на наличие пользователя с таким же email
    result = await db.execute(select(Users).where(Users.email == user.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже зарегистрирован в базе данных."
        )
