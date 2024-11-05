from fastapi import Depends, HTTPException, status
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from epg_test_task.src.database import get_db
from epg_test_task.src.user.models import Users


async def check_unique_email(email: EmailStr, db: AsyncSession = Depends(get_db)):
    # Проверка на наличие пользователя с таким же email
    result = await db.execute(select(Users).where(Users.email == email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже зарегистрирован в базе данных."
        )
