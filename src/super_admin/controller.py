from src.super_admin.dtos import HospitalAuthorization
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.users.models import User
from fastapi import HTTPException,status
from src.utils.password_hash import get_password_hash,verify_password
import jwt
from datetime import datetime, timedelta,timezone
from src.utils.settings import settings
from zoneinfo import ZoneInfo
from src.hospitals.models import Hospital


async def auth_hospital(hospital_id:int,db:AsyncSession):


    result= await db.execute(select(Hospital).where(Hospital.id==hospital_id))

    hospital_exist=result.scalar_one_or_none()

    if not hospital_exist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Hospital not found")


    if hospital_exist.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Hospital is already deleted")

    if hospital_exist.is_authorized:
        raise HTTPException (status_code=status.HTTP_400_BAD_REQUEST,detail="Hospital is already authorized")


    hospital_exist.is_authorized=True
    await db.commit()
    await db.refresh(hospital_exist)
    return{
        "id":hospital_exist.id,
        "name":hospital_exist.name,
        "is_authorized":hospital_exist.is_authorized,
        
    }

    
