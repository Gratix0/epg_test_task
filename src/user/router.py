from sys import base_prefix

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from epg_test_task.src.database import get_db
from epg_test_task.src.user.dependencies import check_unique_email
from epg_test_task.src.user.schemas import UserCreate
from epg_test_task.src.user.service import create_user

router = APIRouter(base_prefix="clients/")

@router.post("/create", summary="Register a new user", description="Creates a new user account with the provided data.")
async def add_user(user: UserCreate, db: Session = Depends(get_db), _ = Depends(check_unique_email)):
    """
    Registers a new user.

    - **user**: Data for creating a new user account.
    - **db**: Database session, extracted from the dependency.
    - **_**: Dependency to check if the username is unique.

    **Returns**:
    - The created user object.
    """
    return await create_user(user, db)