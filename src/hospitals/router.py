from fastapi import APIRouter,Depends,status,Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.hospitals.dtos import HospitalRegister,HospitalLogin,HospitalProfileUpdate,ChangePassword
from src.utils.db import get_db
from src.departments.dtos import DepartmentRegister,DepartmentUpdate,ScheduleCreate,ScheduleDate
from src.hospitals import controller
from src.utils import is_auth
from src.hospitals.models import Hospital
from src.utils.is_auth import is_hospital_authenticated


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

# department register route
@hospital_routes.post("/depart_register",status_code=status.HTTP_201_CREATED)
async def department_register(body:DepartmentRegister,db:AsyncSession=Depends(get_db),hospital:Hospital=Depends(is_hospital_authenticated)):
    return await controller.depart_register(body, db, hospital)


# get single department profile
@hospital_routes.get("/{department_id}/profile",status_code=status.HTTP_200_OK)
async def get_department(department_id: int,hospital: Hospital = Depends(is_hospital_authenticated),db: AsyncSession = Depends(get_db)):
    return await controller.get_department_profile(department_id,hospital,db)

# get all department
@hospital_routes.get("/all_department",status_code=status.HTTP_200_OK)
async def get_all_department(hospital:Hospital=Depends(is_hospital_authenticated),db:AsyncSession=Depends(get_db)):
    return await controller.get_all_department(hospital,db)

# update a single department data

@hospital_routes.put("/update_department/{department_id}",status_code=status.HTTP_200_OK)
async def update_department(department_id:int, body:DepartmentUpdate, db:AsyncSession=Depends(get_db),hospital:Hospital=Depends(is_hospital_authenticated)):
    return await controller.update_department_profile(department_id,body,db,hospital)

@hospital_routes.delete("/delete_department/{department_id}",status_code=status.HTTP_200_OK)
async def delete_department(department_id:int,db:AsyncSession=Depends(get_db),hospital:Hospital=Depends(is_hospital_authenticated)):
    return await controller.delete_department(department_id,db,hospital)

# change department password by hospital
@hospital_routes.put("/change_depart_password/{department_id}",status_code=status.HTTP_200_OK)
async def change_department_password(body:ChangePassword,department_id:int, db:AsyncSession=Depends(get_db),hospital:Hospital=Depends(is_hospital_authenticated)):
    return await  controller.change_depart_password(body,department_id,db,hospital)

# creating department monthly schedule
@hospital_routes.post("/schedule/{department_id}",status_code=status.HTTP_201_CREATED)
async def create_schedule(body:ScheduleCreate,department_id:int,db:AsyncSession=Depends(get_db),hospital:Hospital=Depends(is_hospital_authenticated)):
    return await controller.create_schedule(body,department_id,db,hospital)

# get single schedule of a department by date

@hospital_routes.get("/single_schedule/{department_id}",status_code=status.HTTP_200_OK)
async def get_single_schedule(body:ScheduleDate,department_id:int,db:AsyncSession=Depends(get_db),hospital:Hospital=Depends(is_hospital_authenticated)):
    return await controller.get_schedule_by_date(body,department_id,db,hospital)

@hospital_routes.get("/all_schedules/{department_id}",status_code=status.HTTP_200_OK)
async def all_schedule(department_id:int,db:AsyncSession=Depends(get_db),hospital:Hospital=Depends(is_hospital_authenticated)):
    return await controller.get_all_schedules(department_id,db,hospital)