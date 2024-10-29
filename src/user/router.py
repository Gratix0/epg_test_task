
from pathlib import Path

from typing import Optional


from fastapi import APIRouter, Depends, UploadFile, HTTPException, File
from pydantic import EmailStr
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from epg_test_task.src.database import get_db
from epg_test_task.src.user.dependencies import check_unique_email
from epg_test_task.src.user.schemas import UserInApi, AvatarUser, UserCreate
from epg_test_task.src.user.service import create_user, allowed_file, watermark_my_image

router = APIRouter(prefix="/api/clients")

@router.post("/create", summary="Register a new user", description="Creates a new user account with the provided data.")
async def add_user(first_name: str,
                   last_name: str,
                   email: EmailStr,
                   password: str,
                   gender: str,
                   db: Session = Depends(get_db),
                   _ = Depends(check_unique_email),
                   avatar: UploadFile = File(None)):
    """
    Registers a new user.

    - **first_name**: First name of the user.
    - **last_name**: Last name of the user.
    - **email**: Email address of the user.
    - **password**: Password for the user account.
    - **gender**: Gender of the user.
    - **db**: Database session, extracted from the dependency.
    - **_**: Dependency to check if the username is unique.

    **Returns**:
    - The created user object.
    """
    user_data = UserInApi(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        gender=gender
    )

    local_avatar_path = "None"
    if avatar:
        local_avatar_path = await watermark_my_image(user_data.email, avatar)

    user_data = UserCreate(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        gender=gender,
        pic_url=local_avatar_path
    )

    new_user = await create_user(user_data, db)
    return new_user

