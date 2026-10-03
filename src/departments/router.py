from fastapi import APIRouter,Depends,status,Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.departments.dtos import DepartmentRegister,DepartmentLogin
from src.utils.db import get_db
from src.departments import controller
from src.utils import is_auth
from src.hospitals.models import Hospital
from src.departments.models import Department
from src.utils.is_auth import is_hospital_authenticated,is_department_authenticated


department_routes=APIRouter(prefix="/departments")



@department_routes.post("/login",status_code=status.HTTP_200_OK)
async def department_login(body:DepartmentLogin,db:AsyncSession=Depends(get_db)):
    return await controller.login_department(body,db)

@department_routes.get("/is_department_auth",status_code=status.HTTP_200_OK)
async def admin_authenticate(request:Request, db:AsyncSession = Depends(get_db)):
    return await is_auth.is_department_authenticated(request,db)

@department_routes.get("/profile",status_code=status.HTTP_200_OK)
async def get_department_profile(department:Department=Depends(is_department_authenticated)):
    return controller.get_department_profile(department)

