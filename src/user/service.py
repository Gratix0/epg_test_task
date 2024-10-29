from PIL import Image
import os
from datetime import datetime
from fastapi import HTTPException, status, UploadFile, File
from passlib.context import CryptContext

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from .models import Users
from .schemas import UserInApi, UserCreate

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


watermark = Image.open("user/watermark/b7655b5c-a529-41ab-91c4-0c86c6797ff3.png").convert("RGBA")

async def watermark_my_image(email: str, background_image: UploadFile = File(...)) -> None:
    bg_image = Image.open(background_image.file).convert("RGBA")

    bg_width, bg_height = bg_image.size
    ov_width, ov_height = watermark.size

    x_offset = (bg_width - ov_width) // 2
    y_offset = (bg_height - ov_height) // 2

    bg_image.paste(watermark, (x_offset, y_offset), watermark)

    output_filename = f"combined_image_{email}.png"
    output_path = os.path.join(os.getcwd(), "user/avatars", output_filename)
    bg_image.save(output_path, format="PNG")

    return output_path



async def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
