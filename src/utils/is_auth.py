from fastapi import HTTPException,Request,Depends,status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.utils.db import get_db
from src.users.models import User
import jwt
from src.departments.models import Department
from src.hospitals.models import Hospital
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
async def is_hospital_authenticated(request: Request,db: AsyncSession = Depends(get_db)):
    try:

        token = request.headers.get("Authorization")

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login First"
            )

        token = token.split(" ")[-1]

        data = jwt.decode(token,settings.SECRET_KEY,algorithms=[settings.ALGORITHM])

        hospital_id = data.get("_id")
        


        # Check role
       

        # Find admin in User table
        result= await db.execute(select(Hospital).where(Hospital.id==hospital_id))
        hospital = result.scalar_one_or_none()

        if not hospital:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Hospital does not exist"
            )

        return hospital

    except InvalidTokenError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hospital token is expired or incorrect"
        )

async def is_department_authenticated(request:Request,db:AsyncSession=Depends(get_db)):
    try:
        token=request.headers.get("Authorization")

        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Login first"
            )

        token = token.split(" ")[-1]

        data= jwt.decode(token,settings.SECRET_KEY,algorithms=[settings.ALGORITHM])

        department_id=data.get("_id")

       

        result= await db.execute(select(Department).where(Department.id==department_id))

        department= result.scalar_one_or_none()

        if not department:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Department doesnot exist")

        return department

    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Department token is expired or incorrect")