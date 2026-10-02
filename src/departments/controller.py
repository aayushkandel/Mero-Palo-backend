from src.departments.dtos import DepartmentRegister,DepartmentLogin
from src.departments.models import Department
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.hospitals.models import Hospital
from fastapi import HTTPException,status
from src.utils.password_hash import get_password_hash,verify_password
import jwt
from datetime import datetime, timedelta,timezone
from src.utils.settings import settings
from zoneinfo import ZoneInfo



async def login_department(body:DepartmentLogin,db:AsyncSession):
        if not body.phone or not body.phone.strip():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Enter phone number"
                    )
        if not body.password or not body.password.strip():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Enter password"
                    )

        result=await db.execute(select(Department).where(Department.phone==body.phone,Department.deleted_at.is_(None)))
        department=result.scalar_one_or_none()

        if not department:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Phone number is invalid")

        if not verify_password(body.password,department.password):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Password is incorrect")

        if department.deleted_at is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Department not found")

        exp_time=datetime.now()+timedelta(minutes=settings.EXP_TIME)

        token=jwt.encode({"_id":department.id,"phone":department.phone,"exp":exp_time},settings.SECRET_KEY,settings.ALGORITHM)

        return {"token":token}

# get department profile

def get_department_profile(department:Department):
   
      if department.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="department not found")
      return {
        
            "name":department.name,
            "phone":department.phone,
            "department_room_no":department.department_room_no,
            "duid":department.duid
      }
        