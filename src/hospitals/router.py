from fastapi import APIRouter,Depends,status,Request, UploadFile, File
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
@hospital_routes.get("/depart_profile/{department_id}",status_code=status.HTTP_200_OK)
async def get_department(department_id: int,hospital: Hospital = Depends(is_hospital_authenticated),db: AsyncSession = Depends(get_db)):
    return await controller.get_department_profile(department_id,hospital,db)

# get all department
@hospital_routes.get("/all_department",status_code=status.HTTP_200_OK)
async def get_all_department(db:AsyncSession=Depends(get_db),hospital:Hospital=Depends(is_hospital_authenticated)):
    return await controller.get_all_department(db,hospital)

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

@hospital_routes.put("/update_schedule/{department_id}",status_code=status.HTTP_200_OK)
async def update_schedule(body:ScheduleCreate, department_id:int,db:AsyncSession=Depends(get_db),hospital:Hospital=Depends(is_hospital_authenticated)):
    return await controller.schedule_update(body,department_id,db,hospital)

# get single schedule of a department by date

@hospital_routes.post("/single_schedule/{department_id}",status_code=status.HTTP_200_OK)
async def get_single_schedule(body:ScheduleDate,department_id:int,db:AsyncSession=Depends(get_db),hospital:Hospital=Depends(is_hospital_authenticated)):
    return await controller.get_schedule_by_date(body,department_id,db,hospital)

@hospital_routes.get("/all_schedules/{department_id}",status_code=status.HTTP_200_OK)
async def all_schedule(department_id:int,db:AsyncSession=Depends(get_db),hospital:Hospital=Depends(is_hospital_authenticated)):
    return await controller.get_all_schedules(department_id,db,hospital)

# Update hospital thumbnail
@hospital_routes.put("/update_thumbnail/{gallery_id}",status_code=status.HTTP_200_OK)
async def update_hospital_thumbnail(gallery_id: int,db: AsyncSession = Depends(get_db),hospital: Hospital = Depends(is_hospital_authenticated)):
    return await controller.update_hospital_thumbnail(gallery_id,db,hospital)

# Upload hospital gallery images
@hospital_routes.post("/upload_gallery",status_code=status.HTTP_201_CREATED)
async def upload_gallery(files: list[UploadFile] = File(...),db: AsyncSession = Depends(get_db),hospital: Hospital = Depends(is_hospital_authenticated)):
    return await controller.upload_hospital_gallery(files,db,hospital)


# Delete hospital gallery image
@hospital_routes.delete("/delete_gallery/{gallery_id}",status_code=status.HTTP_200_OK)
async def delete_gallery(gallery_id: int,db: AsyncSession = Depends(get_db),hospital: Hospital = Depends(is_hospital_authenticated)):
    return await controller.delete_hospital_gallery(gallery_id,db,hospital)

# get thumbnail
@hospital_routes.get("/get_thumbnail", status_code=status.HTTP_200_OK)
async def get_thumbnail(db: AsyncSession = Depends(get_db),hospital: Hospital = Depends(is_hospital_authenticated)):
    return await controller.get_hospital_thumbnail(db, hospital)

#Get hospital images
@hospital_routes.get("/get_gallery", status_code=status.HTTP_200_OK)
async def get_gallery(db: AsyncSession = Depends(get_db),hospital: Hospital = Depends(is_hospital_authenticated)):
    return await controller.get_hospital_gallery(db, hospital)

# Update department thumbnail
@hospital_routes.put(
    "/department/{department_id}/update_thumbnail/{gallery_id}",
    status_code=status.HTTP_200_OK
)
async def update_department_thumbnail(
    department_id: int,
    gallery_id: int,
    db: AsyncSession = Depends(get_db),
    hospital: Hospital = Depends(is_hospital_authenticated)
):
    return await controller.update_department_thumbnail(
        gallery_id, department_id, db, hospital
    )


# Get department thumbnail
@hospital_routes.get(
    "/department/{department_id}/get_thumbnail",
    status_code=status.HTTP_200_OK
)
async def get_department_thumbnail(
    department_id: int,
    db: AsyncSession = Depends(get_db),
    hospital: Hospital = Depends(is_hospital_authenticated)
):
    return await controller.get_department_thumbnail(
        department_id, db, hospital
    )


# Upload department gallery
@hospital_routes.post(
    "/department/{department_id}/upload_gallery",
    status_code=status.HTTP_201_CREATED
)
async def upload_department_gallery(
    department_id: int,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    hospital: Hospital = Depends(is_hospital_authenticated)
):
    return await controller.upload_department_gallery(
        files, department_id, db, hospital
    )


# Get department gallery
@hospital_routes.get(
    "/department/{department_id}/get_gallery",
    status_code=status.HTTP_200_OK
)
async def get_department_gallery(
    department_id: int,
    db: AsyncSession = Depends(get_db),
    hospital: Hospital = Depends(is_hospital_authenticated)
):
    return await controller.get_department_gallery(
        department_id, db, hospital
    )


# Delete department gallery image
@hospital_routes.delete(
    "/department/{department_id}/delete_gallery/{gallery_id}",
    status_code=status.HTTP_200_OK
)
async def delete_department_gallery(
    department_id: int,
    gallery_id: int,
    db: AsyncSession = Depends(get_db),
    hospital: Hospital = Depends(is_hospital_authenticated)
):
    return await controller.delete_department_gallery(
        gallery_id, department_id, db, hospital
    )