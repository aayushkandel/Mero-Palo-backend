from fastapi import APIRouter,Depends,status,Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.db import get_db
from src.super_admin import controller
from src.utils import is_auth
from src.super_admin.dtos import HospitalAuthorization
from src.users.models import User
from src.utils.is_auth import is_superAdmin_authenticated


super_admin_routes=APIRouter(prefix="/superAdmin")

@super_admin_routes.put("/authorized_hospitals/{hospital_id}",status_code=status.HTTP_200_OK)
async def auth_hospital(hospital_id:int,db:AsyncSession=Depends(get_db),superAdmin:User=Depends(is_superAdmin_authenticated)):
    return await controller.auth_hospital(hospital_id,db)