"""Users API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, generate_api_key
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserWithApiKey
from app.schemas.auth import ChangePasswordRequest
from app.api.dependencies import get_current_active_user

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse: Current user info
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user information.

    Args:
        user_data: Updated user data
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserResponse: Updated user

    Raises:
        HTTPException: If email or username already taken
    """
    # Check if email is being changed and is already taken
    if user_data.email and user_data.email != current_user.email:
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_data.email

    # Check if username is being changed and is already taken
    if user_data.username and user_data.username != current_user.username:
        result = await db.execute(select(User).where(User.username == user_data.username))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        current_user.username = user_data.username

    # Update other fields
    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name
    if user_data.avatar_url is not None:
        current_user.avatar_url = user_data.avatar_url

    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.post("/me/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change current user password.

    Args:
        password_data: Password change data
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If current password is incorrect
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )

    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)

    await db.commit()

    return {"message": "Password updated successfully"}


@router.post("/me/regenerate-api-key", response_model=UserWithApiKey)
async def regenerate_api_key(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Regenerate API key for current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserWithApiKey: User with new API key
    """
    current_user.api_key = generate_api_key()

    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.get("/me/api-key", response_model=UserWithApiKey)
async def get_api_key(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's API key.

    Args:
        current_user: Current authenticated user

    Returns:
        UserWithApiKey: User with API key
    """
    return current_user
