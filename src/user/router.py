from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, HTTPException, File, Response, Query
from pydantic import EmailStr
from sqlalchemy.orm import Session
from starlette import status

from epg_test_task.src.config import ACCESS_TOKEN_EXPIRE_MINUTES
from epg_test_task.src.database import get_db
from epg_test_task.src.user.dependencies import check_unique_email
from epg_test_task.src.user.schemas import UserInApiForCreate, UserCreate, Token, UserAuth
from epg_test_task.src.user.service import create_user, watermark_my_image, authenticate_user, \
    create_access_token, get_password_hash, get_current_user, authenticate_Match, create_match_in_db, \
    check_reciprocal_match, get_by_user_filter, check_access_jwt

router = APIRouter(prefix="/api/clients")

@router.post("/create", summary="Register a new user", description="Creates a new user account with the provided data.")
async def add_user(first_name: str,
                   last_name: str,
                   email: EmailStr,
                   password: str,
                   gender: str,
                   longitude: float,
                   latitude: float,
                   # Аватар может быть типа str потому-что при передаче необязательным параметром (отправка пустого файла)
                   # В curl передаётся пустая строчка вместо файла и оне не проходит pydantic валидацию.
                   avatar: Optional[UploadFile] | str = File(None),
                   db: Session = Depends(get_db),
                   _ = Depends(check_unique_email)):
    """
    Registers a new user.

    - **first_name**: First name of the user.
    - **last_name**: Last name of the user.
    - **email**: Email address of the user.
    - **password**: Password for the user account.
    - **gender**: Gender of the user.
    - **avatar**: Avatar of the user.
    - **db**: Database session, extracted from the dependency.
    - **_**: Dependency to check if the username is unique.

    **Returns**:
    - The created user object.
    """
    user_data = UserInApiForCreate(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        gender=gender,
        longitude = longitude,
        latitude = latitude,
    )

    local_avatar_path = "/path/to/default/avatar"
    if avatar:
        local_avatar_path = await watermark_my_image(user_data.email, avatar)

    pass_for_db = get_password_hash(password)
    user_data = UserCreate(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=pass_for_db,
        gender=gender,
        pic_url=local_avatar_path,
        longitude = longitude,
        latitude = latitude,
    )

    new_user = await create_user(user_data, db)
    return new_user

@router.post("/login", response_model=Token, summary="Login", description="Logs in a user and returns an access token.")
async def login_for_access_token(user: UserAuth, response: Response, db=Depends(get_db)):
    """
    Authenticates a user and generates an access token.

    - **user**: User credentials (username and password hash).
    - **response**: The response object to set a cookie.
    - **db**: Database session.

    **Returns**:
    - `Token`: An object containing the access token and token type.

    **Raises**:
    - HTTPException: If the username or password is incorrect.
    """

    user = await authenticate_user(db=db, email=user.email, password=user.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate access token
    access_token_expires = timedelta(minutes=float(ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    response.set_cookie(key="access_token", value=access_token, httponly=True)

    return Token(access_token=access_token, token_type="bearer")

@router.post("/{id}/match", status_code=200)
async def match_user(id: int, db = Depends(get_db), current_user = Depends(get_current_user)):
        second_user = await authenticate_Match(id, db, current_user)
        await create_match_in_db(id, db, current_user)
        return await check_reciprocal_match(second_user, db, current_user)


@router.get("/list")  # Assuming you have UserDB schema
async def get_users(
        db = Depends(get_db),
        first_name: Optional[str] = Query(None, description="Filter by first name"),
        last_name: Optional[str] = Query(None, description="Filter by last name"),
        gender: Optional[str] = Query(None, description="Filter by gender"),
        sort_by: Optional[str] = Query(None, description="Sort by registration date (asc or desc)"),
        radius: Optional[float] = Query(None, description="Radius in kilometers"),
        user_longitude: Optional[float] = None,
        user_latitude: Optional[float] = None,
        _ = Depends(check_access_jwt)
):
    """
    Retrieves a list of users with optional filtering and sorting.
    """
    return await get_by_user_filter(db, first_name, last_name, gender, sort_by, radius, user_longitude, user_latitude)
