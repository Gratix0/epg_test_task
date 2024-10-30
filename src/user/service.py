import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

from PIL import Image
from fastapi import HTTPException, status, UploadFile, File, Cookie, Depends
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import and_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .models import Users, Match
from .schemas import UserCreate, UserDB
from ..config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, MY_EMAIL, EMAIL_PASS  # Configuration
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

async def authenticate_user(db: AsyncSession, email: str, password: str):
    user = await get_user(db, email)
    if not user:
        return False
    if not await verify_password(password, user.password):
        return False
    return user

watermark = Image.open("user/watermark/b7655b5c-a529-41ab-91c4-0c86c6797ff3.png").convert("RGBA")

async def watermark_my_image(email: str, background_image: UploadFile = File(...)) -> None:
    try:
        bg_image = Image.open(background_image.file).convert("RGBA")

        bg_width, bg_height = bg_image.size
        ov_width, ov_height = watermark.size

        x_offset = (bg_width - ov_width) // 2
        y_offset = (bg_height - ov_height) // 2

        bg_image.paste(watermark, (x_offset, y_offset), watermark)

        output_filename = f"combined_image_{email}.png"
        output_path = os.path.join(os.getcwd(), "user/avatars", output_filename)
        bg_image.save(output_path, format="PNG")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Uncorrected file. Please try with image. Error message: " + str(e))
    return output_path

async def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ===========================
# User Operations with Match
# ===========================
async def authenticate_Match(id: int, db: AsyncSession, current_user: UserDB):
    # Проверка, существует ли пользователь с id в бд
    matched_user = await db.execute(select(Users).where(Users.id == id))
    matched_user = matched_user.scalars().first()
    if not matched_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверка на самооценку
    if matched_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot match yourself")

    # Проверка на существование матча
    existing_match = await db.execute(select(Match).where(and_(Match.user_id == current_user.id, Match.matched_user_id == id)))
    existing_match = existing_match.scalars().first()
    if existing_match:
        raise HTTPException(status_code=400, detail="Match already exists")

    return matched_user

async def create_match_in_db(id: str, db: AsyncSession, current_user: UserDB):
    # Create Match
    new_match = Match(user_id=current_user.id, matched_user_id=int(id), is_match=True)
    db.add(new_match)
    await db.commit()
    await db.refresh(new_match)

async def update_matches_on_true(db: AsyncSession, user_id1: int, user_id2: int):
    """Updates is_match for two reciprocal matches using ORM (still less efficient than raw SQL)."""
    try:
        await db.execute(
            update(Match)
            .where(and_(Match.user_id == user_id1, Match.matched_user_id == user_id2))
            .values(is_match=True)
        )
        await db.execute(
            update(Match)
            .where(and_(Match.user_id == user_id2, Match.matched_user_id == user_id1))
            .values(is_match=True)
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error updating matches on True: {e}")

async def send_email(first_user: UserDB, second_user: UserDB):
    """Асинхронно отправляет email."""
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(MY_EMAIL, EMAIL_PASS)

        # Создание сообщения с использованием MIMEText для правильной кодировки
        message1 = MIMEText(
            f"It's a Match! \n\n Поздравляем! Вы нашли пару с {second_user.first_name} почта: {second_user.email}!",
            'plain', 'utf-8')
        message1['Subject'] = "It's a Match!"
        message1['From'] = MY_EMAIL
        message1['To'] = first_user.email

        message2 = MIMEText(
            f"It's a Match! \n\n Поздравляем! Вы нашли пару с {first_user.first_name} почта: {first_user.email}!",
            'plain', 'utf-8')
        message2['Subject'] = "It's a Match!"
        message2['From'] = MY_EMAIL
        message2['To'] = second_user.email

        # Отправка писем
        server.send_message(message1)
        server.send_message(message2)

        print(f"Email успешно отправлен на {first_user.email} и {second_user.email}")

    except smtplib.SMTPException as e:
        print(f"Ошибка при отправке email: {e}")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")


async def check_reciprocal_match(matched_user: UserDB, db: AsyncSession, current_user: UserDB):
    async with db as session:
        reciprocal_match = await session.execute(
            select(Match).where(and_(Match.user_id == matched_user.id, Match.matched_user_id == current_user.id, Match.is_match == True))
        )
        reciprocal_match = reciprocal_match.scalars().first()

        if reciprocal_match:
            if reciprocal_match.matched_user: # Проверка на существование matched_user
                await send_email(matched_user, current_user)
                await update_matches_on_true(db, current_user.id, matched_user.id)
                return {"message": "It's a match!"}
            else:
                print(f"Error: Matched user not found for Match ID: {reciprocal_match.id}")
                return {"message": "Error processing match"}
        else:
            return {"message": "Match registered"}

# ===========================
# Tokenization
# ===========================

# Create access token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()  # Copy data for token
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta  # Set expiration time
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # Default
    to_encode.update({"exp": expire})  # Update data with expiration time
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Get current user
async def get_current_user(
        access_token: str = Cookie(None),  # Extract token from cookies
        db: AsyncSession = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not verify credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if access_token is None:
        raise credentials_exception
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])  # Decode token
        email: str = payload.get("sub")  # Get email from payload
        if email is None:
            raise credentials_exception
        # token_data = TokenData(email=email)  # Create TokenData object
    except JWTError:
        raise credentials_exception

    user = await get_user(db=db, email=email)  # Get user by email
    if user is None:
        raise credentials_exception  # If user not found

    return user  # Return current user
