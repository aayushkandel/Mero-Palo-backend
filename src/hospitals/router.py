from fastapi import APIRouter,Depends,status,Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.hospitals.dtos import HospitalRegister,HospitalLogin,HospitalProfileUpdate,ChangePassword
from src.utils.db import get_db
from src.hospitals import controller
from src.utils import is_auth
from src.hospitals.models import Hospital
from src.utils.is_auth import is_user_authenticated,is_hospital_authenticated


hospital_routes=APIRouter(prefix="/hospitals")


@hospital_routes.post("/register",status_code=status.HTTP_201_CREATED)
async def hospital_register(body:HospitalRegister, db:AsyncSession=Depends(get_db)):
    return await controller.register(body,db)

@hospital_routes.post("/login",status_code=status.HTTP_200_OK)
async def hospital_login(body:HospitalLogin,db:AsyncSession=Depends(get_db)):
    return await controller.login(body, db)

@hospital_routes.get("/is_hospital_auth",status_code=status.HTTP_200_OK)
async def admin_authenticate(request:Request, db:AsyncSession = Depends(get_db)):
    return await is_auth.is_hospital_authenticated(request,db)

@hospital_routes.get("/profile",status_code=status.HTTP_200_OK)
async def get_hospital_profile(hospital:Hospital=Depends(is_hospital_authenticated)):
    return controller.get_hospital_profile(hospital)

@hospital_routes.put("/update",response_model=HospitalProfileUpdate,status_code=status.HTTP_200_OK)
async def update_profile(body:HospitalProfileUpdate,db:AsyncSession=Depends(get_db),hospital:Hospital=Depends(is_hospital_authenticated)):
    return await controller.update_profile(body,db,hospital)

@hospital_routes.delete("/delete",status_code=status.HTTP_200_OK)
async def delete_hospital(db:AsyncSession=Depends(get_db),hospital:Hospital=Depends(is_hospital_authenticated)):
    return await controller.delete_hospital(db,hospital)

@hospital_routes.put("/change_password",status_code=status.HTTP_200_OK)
async def password_change(body:ChangePassword,db:AsyncSession=Depends(get_db),hospital:Hospital=Depends(is_hospital_authenticated)):
    return await controller.change_password(body, db, hospital)