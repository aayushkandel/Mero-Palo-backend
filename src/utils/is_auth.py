from fastapi import HTTPException,Request,Depends,status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.utils.db import get_db
from src.users.models import User
import jwt
from src.utils.settings import settings
from jwt.exceptions import InvalidTokenError




async def is_user_authenticated(request: Request,db: AsyncSession = Depends(get_db)):
    try:

        token = request.headers.get("authorization")

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login First"
            )

        token = token.split(" ")[-1]

        data = jwt.decode(token,settings.SECRET_KEY,algorithms=[settings.ALGORITHM])

        user_id = data.get("_id")
        role=data.get("role")

        if role != "user":
            raise HTTPException(
                    status_code=404,
                    detail="You are not a user"
            )

        result=await db.execute(select(User).where(User.id==user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User does not exist"
            )

        return user

    

    except InvalidTokenError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is expired or incorrect"
        )


# for admin authentication
async def is_admin_authenticated(request: Request,db: AsyncSession = Depends(get_db)):
    try:

        token = request.headers.get("Authorization")

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login First"
            )

        token = token.split(" ")[-1]

        data = jwt.decode(token,settings.SECRET_KEY,algorithms=[settings.ALGORITHM])

        admin_id = data.get("_id")
        role = data.get("role")


        # Check role
        if role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a admin"
            )

        # Find admin in User table
        result= await db.execute(select(User).where(User.id==admin_id))
        admin = result.scalar_one_or_none()

        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin does not exist"
            )

        return admin

    except InvalidTokenError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin token is expired or incorrect"
        )