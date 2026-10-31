from src.hospitals.dtos import HospitalRegister,HospitalLogin,HospitalProfileUpdate,ChangePassword
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from src.departments.dtos import DepartmentRegister,DepartmentUpdate,ScheduleCreate,OpenStatus,ScheduleDate
from src.departments.models import Department,Schedule,DepartmentGallary
from src.hospitals.models import Hospital,HospitalGallary
from fastapi import HTTPException,status,UploadFile
from src.utils.password_hash import get_password_hash,verify_password
import jwt
from datetime import datetime, timedelta,timezone
from src.utils.settings import settings
from zoneinfo import ZoneInfo

from src.utils.image_uploader import (
    upload_image,
    delete_uploaded_file,
    DEPARTMENT_THUMBNAIL_DIR,
    DEPARTMENT_GALLERY_DIR
)

# hospital register
async def register(body: HospitalRegister, db: AsyncSession):

    if not body.name or not body.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter hospital name"
        )

    if not body.phone or not body.phone.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter phone number"
        )

    if not body.registration_no or not body.registration_no.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter registeration number"
        )

    if not body.password or not body.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter password"
        )

    if not body.confirm_password or not body.confirm_password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter confirm password"
        )

    if body.password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password didn't matched"
        )

    # Store hospital name and registration number in lowercase
    hospital_name = body.name.strip().lower()
    registration_no = body.registration_no.strip().lower()
    phone = body.phone.strip()

    result = await db.execute(
        select(Hospital).where(
            Hospital.phone == phone
        )
    )

    exist_phone = result.scalar_one_or_none()

    if exist_phone:

        if exist_phone.deleted_at is not None:

            exist_phone.name = hospital_name
            exist_phone.password = get_password_hash(body.password)
            exist_phone.registration_no = registration_no
            exist_phone.deleted_at = None
            exist_phone.is_authorized=False
            exist_phone.thumbnail=None

            await db.commit()
            await db.refresh(exist_phone)

            return {
                "id": exist_phone.id,
                "huid": exist_phone.huid,
                "name": exist_phone.name.title(),
                "phone": exist_phone.phone,
                "registration_no": exist_phone.registration_no.upper(),
                "is_authorized": exist_phone.is_authorized,
                "thumbnail":exist_phone.thumbnail
            }

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{phone} already exist"
        )

    result = await db.execute(
        select(Hospital).where(
            func.lower(Hospital.name) == hospital_name,
            Hospital.deleted_at.is_(None)
        )
    )

    exist_name = result.scalar_one_or_none()

    if exist_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Hospital {body.name} already exist"
        )

    result = await db.execute(
        select(Hospital).where(
            func.lower(Hospital.registration_no) == registration_no,
            Hospital.deleted_at.is_(None)
        )
    )

    exist_registration_no = result.scalar_one_or_none()

    if exist_registration_no:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration number {body.registration_no} already exist"
        )

    hash_password = get_password_hash(body.password)

    new_hospital = Hospital(
        name=hospital_name,
        phone=phone,
        registration_no=registration_no,
        password=hash_password,
        is_authorized=False,
        deleted_at=None,
        thumbnail=None
    )

    db.add(new_hospital)

    await db.commit()
    await db.refresh(new_hospital)

    return {
        "id": new_hospital.id,
        "huid": new_hospital.huid,
        "name": new_hospital.name.title(),
        "phone": new_hospital.phone,
        "registration_no": new_hospital.registration_no.upper(),
        "is_authorized": new_hospital.is_authorized,
        "thumbnail":new_hospital.thumbnail
    }



 # hospital login   
async def login(body:HospitalLogin,db:AsyncSession):

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

    result= await db.execute(select(Hospital).where(Hospital.phone == body.phone))

    hospital=result.scalar_one_or_none()


    if not hospital:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Phone number invalid")

    if not verify_password(body.password, hospital.password):
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Password is invalid")

    if hospital.deleted_at is not None:
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Hospital not found ")

    if hospital.is_authorized != True:
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Your hospital {hospital.name} is not authorized by admin yet, please wait!")
    
    exp_time=datetime.now()+timedelta(minutes=settings.EXP_TIME)

    token= jwt.encode({"_id":hospital.id,"phone":hospital.phone,"exp":exp_time},settings.SECRET_KEY, settings.ALGORITHM)

    return {"token":token}


# get hospital profile
def get_hospital_profile(hospital:Hospital):
   
      if hospital.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Hospital not found")
      return {
            "name":hospital.name,
            "email":hospital.email,
            "address":hospital.address,
            "phone":hospital.phone,
            "registration_no":hospital.registration_no
      }

# update hospital profile
async def update_profile(body:HospitalProfileUpdate, db:AsyncSession,hospital:Hospital):
      if hospital.deleted_at is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Hospital is deleted")
      data=body.model_dump()
      
      for field,value in data.items():
                  setattr(hospital,field,value)
      
      await db.commit()
      await db.refresh(hospital)
      
      return hospital

# delete hospital

async def delete_hospital(db:AsyncSession,hospital:Hospital):
    result= await db.execute(select(Hospital).where(Hospital.id==hospital.id))
    hospital=result.scalar_one_or_none()

    if not hospital:
          raise HTTPException (
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hospital not found"
          )

    if hospital.deleted_at is not None:
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Hospital is already deleted")

    hospital.deleted_at=datetime.now(ZoneInfo("Asia/Kathmandu"))
    await db.commit()

    return {
          "message":"Hospital deleted",
          "deleted_at":hospital.deleted_at
    }

# change Password

async def change_password(body:ChangePassword,db:AsyncSession,hospital:Hospital):
       if not body.old_password or not body.old_password.strip():
                  raise HTTPException(
                      status_code=status.HTTP_400_BAD_REQUEST,
                      detail="Enter your password"
                  )
       if not body.new_password or not body.new_password.strip():
                   raise HTTPException(
                       status_code=status.HTTP_400_BAD_REQUEST,
                       detail="Enter new password"
                   )
       if not body.confirm_new_password or not body.confirm_new_password.strip():
                   raise HTTPException(
                       status_code=status.HTTP_400_BAD_REQUEST,
                       detail="Enter confirm new password"
                   )
       if hospital.deleted_at is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="hospital not found")
      
       if not verify_password(body.old_password,hospital.password):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Old password is invalid")
      
       if body.confirm_new_password != body.new_password:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Confirm New password doesn't match")
      
      
       hospital.password=get_password_hash(body.new_password)
       await db.commit()
       await db.refresh(hospital)
      
       return{
                "message":"Password changed successfully",
                "name":hospital.name
          }
      


# register new department through hospital dashboard

async def depart_register(body: DepartmentRegister,db: AsyncSession,hospital: Hospital):

    if not body.name or not body.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter Department name"
        )

    if not body.phone or not body.phone.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter Department phone number"
        )

    if not body.department_room_no or not body.department_room_no.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter Department room number"
        )

    if not body.password or not body.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter password"
        )

    if not body.confirm_password or not body.confirm_password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter confirm password"
        )

    if body.password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password didn't matched"
        )

    department_name = body.name.strip().lower()
    department_room_no = body.department_room_no.strip().lower()
    phone = body.phone.strip()


    hospital_exist = await db.execute(select(Hospital).where(Hospital.id == hospital.id,Hospital.deleted_at.is_(None)))

    hospital = hospital_exist.scalar_one_or_none()

    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to create the departments"
        )


    result = await db.execute(select(Department).where(Department.phone == phone,Department.hospital_id==hospital.id))

    exist_phone = result.scalar_one_or_none()

    if exist_phone:

        if exist_phone.deleted_at is not None:

            exist_phone.name=department_name
            exist_phone.password=get_password_hash(body.password)
            exist_phone.department_room_no=department_room_no
            exist_phone.deleted_at=None
            exist_phone.thumbnail=None

            await db.commit()
            await db.refresh(exist_phone)

            return{
                   "id": exist_phone.id,
                   "duid": exist_phone.duid,
                   "name": exist_phone.name.title(),
                    "phone": exist_phone.phone,
                    "department_room_no":exist_phone.department_room_no,
                    "thumbnail":exist_phone.thumbnail
            }
        raise HTTPException(
              status_code=status.HTTP_400_BAD_REQUEST,
              detail=f"{phone} already exist"
        )

            # Check department name in this hospital
    name_result = await db.execute(
                select(Department).where(
                    Department.hospital_id == hospital.id,
                    func.lower(Department.name) == department_name,
                    Department.deleted_at.is_(None)
                )
            )

    exist_name = name_result.scalar_one_or_none()

    if exist_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Department {body.name} already exist for {hospital.name}"
                )

            # Check room number in this hospital
    room_result = await db.execute(
                select(Department).where(
                    Department.hospital_id == hospital.id,
                    func.lower(Department.department_room_no) == department_room_no,
                    Department.deleted_at.is_(None)
                )
            )

    exist_department_room_no = room_result.scalar_one_or_none()

    if exist_department_room_no:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Department room number {body.department_room_no} already exist for {hospital.name}"
                )



    hash_password = get_password_hash(body.password)

    new_department = Department(
        name=department_name,
        phone=phone,
        hospital_id=hospital.id,
        department_room_no=department_room_no,
        password=hash_password,
        deleted_at=None,
        thumbnail=None,
    )

    db.add(new_department)

    await db.commit()
    await db.refresh(new_department)

    return {
          "id":new_department.id,
          "duid":new_department.duid,
          "hospital_id":new_department.hospital_id,
          "name":new_department.name.title(),
          "phone":new_department.phone,
          "department_room_no":new_department.department_room_no,
          "thumbnail":new_department.thumbnail,
    }
# get department profile

async def get_department_profile(department_id: int,hospital: Hospital,db: AsyncSession):
    if hospital.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hospital not found"
        )

    result = await db.execute(
        select(Department).where(
            Department.id == department_id,
            Department.hospital_id == hospital.id
        )
    )

    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found in this hospital"
        )

    if department.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department not found"
        )

    return {
        "id": department.id,
        "name": department.name,
        "phone": department.phone,
        "department_room_no": department.department_room_no,
        "hospital_id": department.hospital_id
    }

async def get_all_department(hospital:Hospital,db:AsyncSession):
       if hospital.deleted_at is not None:
               raise HTTPException(
                   status_code=status.HTTP_400_BAD_REQUEST,
                   detail="Hospital not found"
               )

       result=await db.execute(select(Department).where(Department.hospital_id==hospital.id,Department.deleted_at.is_(None)))

       departments=result.scalars().all()

       if not departments:
               raise HTTPException(
                   status_code=status.HTTP_404_NOT_FOUND,
                   detail="Department not found in this hospital"
               )
       
       
       
       return [
          {
            "id": department.id,
            "name": department.name,
            "phone": department.phone,
            "department_room_no": department.department_room_no,
            "hospital_id": department.hospital_id
          }
          for department in departments
    ]


async def update_department_profile(department_id: int,body: DepartmentUpdate,db: AsyncSession,hospital: Hospital):

    if hospital.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hospital is deleted"
        )

    if not body.name or not body.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter department name"
        )

    if not body.phone or not body.phone.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter phone number"
        )

    if not body.department_room_no or not body.department_room_no.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter department room number"
        )

    # Convert entered name and room number to lowercase
    department_name = body.name.strip().lower()
    department_room_no = body.department_room_no.strip().lower()
    phone = body.phone.strip()

    # Find the department
    result = await db.execute(
        select(Department).where(
            Department.id == department_id,
            Department.hospital_id == hospital.id,
            Department.deleted_at.is_(None)
        )
    )

    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found in this hospital"
        )

    result = await db.execute(
        select(Department).where(
            Department.phone == phone,
            Department.id != department_id,
            Department.deleted_at.is_(None)
        )
    )

    exist_phone = result.scalar_one_or_none()

    if exist_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{phone} already exist"
        )


    result = await db.execute(
        select(Department).where(
            Department.hospital_id == hospital.id,
            func.lower(Department.name) == department_name,
            Department.id != department_id,
            Department.deleted_at.is_(None)
        )
    )

    exist_name = result.scalar_one_or_none()

    if exist_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department {body.name} already exist for {hospital.name}"
        )

    result = await db.execute(
        select(Department).where(
            Department.hospital_id == hospital.id,
            func.lower(Department.department_room_no) == department_room_no,
            Department.id != department_id,
            Department.deleted_at.is_(None)
        )
    )

    exist_room = result.scalar_one_or_none()

    if exist_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department room number {body.department_room_no} already exist for {hospital.name}"
        )


    department.name = department_name
    department.phone = phone
    department.department_room_no = department_room_no

    await db.commit()
    await db.refresh(department)

    return {
        "message": "Department profile updated successfully",
        "department": {
            "id": department.id,
            "name": department.name,
            "phone": department.phone,
            "department_room_no": department.department_room_no,
            "hospital_id": department.hospital_id
        }
    }

# delete department by hospital

async def delete_department(department_id,db:AsyncSession,hospital:Hospital):
    result=await db.execute(select(Department).where(Department.id==department_id,Department.hospital_id==hospital.id))

    department=result.scalar_one_or_none()

    if not department:
           raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Department not found")

    if department.deleted_at is not None:
           raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Department is already deleted")

    department.deleted_at=datetime.now(ZoneInfo("Asia/Kathmandu"))
    await db.commit()

    return {
          "message":"department deleted",
          "deleted_at":department.deleted_at
    }

# change password for department

async def change_depart_password(body:ChangePassword,department_id:int,db:AsyncSession, hospital:Hospital):
      if not body.old_password or not body.old_password.strip():
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Enter your password")

      if not body.new_password or not body.new_password.strip():
                         raise HTTPException(
                             status_code=status.HTTP_400_BAD_REQUEST,
                             detail="Enter new password"
                         )
      if not body.confirm_new_password or not body.confirm_new_password.strip():
                         raise HTTPException(
                             status_code=status.HTTP_400_BAD_REQUEST,
                             detail="Enter confirm new password"
                         )

      result= await db.execute(select(Department).where(Department.id==department_id,Department.hospital_id==hospital.id))
      department=result.scalar_one_or_none()

      if not department:
              raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="department not found")

      if department.deleted_at is not None:
              raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Department is already deleted")

      if not verify_password(body.old_password,department.password):
                      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Old password is invalid")
            
      if body.confirm_new_password != body.new_password:
                      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Confirm New password doesn't match"
                      )
      department.password=get_password_hash(body.new_password)
      await db.commit()
      await db.refresh(hospital)

      return{
              "message":"Password changed successfully",
              "name":department.name
      }


# creating controller for monthly schedule of department by hospital

async def create_schedule(body:ScheduleCreate,department_id:int,db:AsyncSession,hospital:Hospital):

       if  not body.dates :
                          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Enter Dates")
       if body.open_status == OpenStatus.Open:
       
            if not body.registration_start :
                          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Enter Registration start Time")

            if not body.registration_close:
                          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Enter Registration close time")

            if not body.token_start :
                          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Enter Token start time")
            
            if body.registration_start>= body.registration_close :
              raise HTTPException(
                     status_code=status.HTTP_400_BAD_REQUEST,
                     detail="Registration close time must be after  registration open time"
              )

       elif body.open_status == OpenStatus.Close:

           body.registration_start = None
           body.registration_close = None
           body.token_start = None

       result= await db.execute(select(Department).where(
              Department.id==department_id,
              Department.hospital_id==hospital.id,
              Department.deleted_at.is_(None)
       ))

       department=result.scalar_one_or_none()

       if not department:
              raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Department not found for hospital {hospital.name} with department id {department_id}")


       schedules=[ ]

       for schedule_dates in body.dates:

              # checking dublicate schedule for single day by department of a hospital
              result= await db.execute(select(Schedule).where(
                     Schedule.department_id==department_id,
                     Schedule.hospital_id== hospital.id,
                     Schedule.date==schedule_dates,
              ))

              existing_schedule=result.scalar_one_or_none()

              if existing_schedule:
                     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                         detail=f"Schedule already exist for {schedule_dates}")

              schedule=Schedule(
                     hospital_id=hospital.id,
                     department_id=department_id,
                     date=schedule_dates,
                     open_status=body.open_status,
                     registration_start=body.registration_start,
                     registration_close=body.registration_close,
                     token_start=body.token_start
              )
              db.add(schedule)
              schedules.append(schedule)

       await db.commit()

       return{
              "message":"Schedule created successfully",
              "department_id":department_id,
              "open_status":body.open_status,
              "total_schedules":len(schedules),
              "dates":body.dates
       }


# get single schedule of a department by date

async def get_schedule_by_date(
    body: ScheduleDate,
    department_id: int,
    db: AsyncSession,
    hospital: Hospital
):

    if not body.dates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Give Dates"
        )

    result = await db.execute(
        select(Schedule).where(
            Schedule.date.in_(body.dates),
            Schedule.department_id == department_id,
            Schedule.hospital_id == hospital.id
        ).order_by(Schedule.date)
    )

    schedules = result.scalars().all()

    if not schedules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found for the selected dates"
        )

    return schedules

async def get_all_schedules(department_id:int, db:AsyncSession,hospital:Hospital):
    result=await db.execute(select(Department).where(
           Department.id==department_id,
           Department.hospital_id==hospital.id,
           Department.deleted_at.is_(None)
    ))

    department=result.scalar_one_or_none()

    if not department:
           raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Department not found")

    result=await db.execute(select(Schedule).where(
           Schedule.department_id==department_id,
           Schedule.hospital_id==hospital.id
    )
    .order_by(Schedule.date)
    )

    schedules=result.scalars().all()

    return{
        "department_id": department_id,
        "total_schedules": len(schedules),
        "schedules": [
            {
                "id": schedule.id,
                "suid": schedule.suid,
                "date": schedule.date,
                "open_status": schedule.open_status,
                "registration_start": schedule.registration_start,
                "registration_close": schedule.registration_close,
                "token_start": schedule.token_start,
                "created_at": schedule.created_at,
                "updated_at": schedule.updated_at
            }
            for schedule in schedules
        ]
    }





async def schedule_update(
    body: ScheduleCreate,
    department_id: int,
    db: AsyncSession,
    hospital: Hospital
):

    if not body.dates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter Dates"
        )

    # Check duplicate dates in request
    if len(body.dates) != len(set(body.dates)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate dates are not allowed"
        )

    # Validate schedule times
    if body.open_status == OpenStatus.Open:

        if not body.registration_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enter Registration start Time"
            )

        if not body.registration_close:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enter Registration close time"
            )

        if not body.token_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enter Token start time"
            )

        if body.registration_start >= body.registration_close:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration close time must be after registration open time"
            )

    elif body.open_status == OpenStatus.Close:

        body.registration_start = None
        body.registration_close = None
        body.token_start = None

    # Check department
    result = await db.execute(
        select(Department).where(
            Department.id == department_id,
            Department.hospital_id == hospital.id,
            Department.deleted_at.is_(None)
        )
    )

    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department not found for hospital {hospital.name} with department id {department_id}"
        )

    # Find existing schedules for selected dates
    result = await db.execute(
        select(Schedule).where(
            Schedule.department_id == department_id,
            Schedule.hospital_id == hospital.id,
            Schedule.date.in_(body.dates),
            
        )
    )

    existing_schedules = result.scalars().all()

    # Check whether every selected date has a schedule
    existing_dates = {item.date for item in existing_schedules}

    missing_dates = [
        selected_date
        for selected_date in body.dates
        if selected_date not in existing_dates
    ]

    if missing_dates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No schedule found for dates: {missing_dates}"
        )

    # Update schedules
    for existing_schedule in existing_schedules:

        existing_schedule.open_status = body.open_status
        existing_schedule.registration_start = body.registration_start
        existing_schedule.registration_close = body.registration_close
        existing_schedule.token_start = body.token_start

    await db.commit()

    return {
        "message": "Schedule updated successfully",
        "department_id": department_id,
        "open_status": body.open_status,
        "total_schedules": len(existing_schedules),
        "dates": [item.date for item in existing_schedules]
    }



# hospital thumbnail uploader




async def update_hospital_thumbnail(
    file: UploadFile,
    db: AsyncSession,
    hospital: Hospital
):

    old_thumbnail = hospital.thumbnail
    new_thumbnail = None

    try:

        # Upload new thumbnail
        new_thumbnail = await upload_image(
            file,
            THUMBNAIL_DIR
        )

        # Update hospital thumbnail
        hospital.thumbnail = new_thumbnail

        await db.commit()
        await db.refresh(hospital)

        # Delete old thumbnail only after successful commit
        if old_thumbnail:
            delete_uploaded_file(old_thumbnail)

        return {
            "message": "Hospital thumbnail updated successfully",
            "thumbnail": hospital.thumbnail
        }

    except Exception:
        await db.rollback()

        # Remove newly uploaded image if database update fails
        if new_thumbnail:
            delete_uploaded_file(new_thumbnail)

        raise

# hospital gallary controller

async def upload_hospital_gallery(
    files: list[UploadFile],
    db: AsyncSession,
    hospital: Hospital
):

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please select at least one image"
        )

    uploaded_paths = []
    gallery_records = []

    try:

        for file in files:

            image_path = await upload_image(
                file,
                GALLERY_DIR
            )

            uploaded_paths.append(image_path)

            gallery = HospitalGallary(
                hospital_id=hospital.id,
                image=image_path
            )

            gallery_records.append(gallery)

        db.add_all(gallery_records)

        await db.commit()

        for gallery in gallery_records:
            await db.refresh(gallery)

        return {
            "message": "Hospital gallery images uploaded successfully",
            "total_images": len(gallery_records),
            "images": [
                {
                    "id": gallery.id,
                    "hguid": gallery.hguid,
                    "image": gallery.image
                }
                for gallery in gallery_records
            ]
        }

    except Exception:

        await db.rollback()

        # Delete uploaded files if database operation fails
        for image_path in uploaded_paths:
            delete_uploaded_file(image_path)

        raise


# delete the hospital gallary image


async def delete_hospital_gallery(
    gallery_id: int,
    db: AsyncSession,
    hospital: Hospital
):

    result = await db.execute(
        select(HospitalGallary).where(
            HospitalGallary.id == gallery_id,
            HospitalGallary.hospital_id == hospital.id
        )
    )

    gallery = result.scalar_one_or_none()

    if not gallery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery image not found"
        )

    image_path = gallery.image

    try:

        await db.delete(gallery)

        await db.commit()

        # Delete physical image after successful database deletion
        delete_uploaded_file(image_path)

        return {
            "message": "Gallery image deleted successfully",
            "gallery_id": gallery_id
        }

    except Exception:

        await db.rollback()

        raise




# get hospital thumbnail
async def get_hospital_thumbnail(db: AsyncSession, hospital: Hospital):

    if not hospital.thumbnail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital thumbnail not found"
        )

    return {
        "message": "Thumbnail fetched successfully",
        "thumbnail": hospital.thumbnail
    }


# get hospital gallary
async def get_hospital_gallery(db: AsyncSession, hospital: Hospital):

    result = await db.execute(
        select(HospitalGallary).where(
            HospitalGallary.hospital_id == hospital.id
        )
    )

    images = result.scalars().all()

    return {
        "message": "Gallery images fetched successfully",
        "images": [
            {
                "id": image.id,
                "hguid": image.hguid,
                "image": image.image
            }
            for image in images
        ]
    }

# update department thumbnail
async def update_department_thumbnail(
    file: UploadFile,
    department_id: int,
    db: AsyncSession,
    hospital: Hospital
):
    department = await get_hospital_department(
        department_id, db, hospital
    )

    old_thumbnail = department.thumbnail

    new_thumbnail = await upload_image(
        file,
        DEPARTMENT_THUMBNAIL_DIR
    )

    try:
        department.thumbnail = new_thumbnail

        await db.commit()
        await db.refresh(department)

    except Exception:
        await db.rollback()
        delete_uploaded_file(new_thumbnail)
        raise

    if old_thumbnail:
        delete_uploaded_file(old_thumbnail)

    return {
        "message": "Department thumbnail updated successfully",
        "thumbnail": department.thumbnail
    }

# get department thumbnail

async def get_department_thumbnail(
    department_id: int,
    db: AsyncSession,
    hospital: Hospital
):
    department = await get_hospital_department(
        department_id, db, hospital
    )

    if not department.thumbnail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department thumbnail not found"
        )

    return {
        "message": "Department thumbnail fetched successfully",
        "thumbnail": department.thumbnail
    }


# Upload images in department gallary
async def upload_department_gallery(
    files: list[UploadFile],
    department_id: int,
    db: AsyncSession,
    hospital: Hospital
):
    department = await get_hospital_department(
        department_id, db, hospital
    )

    uploaded_images = []

    try:
        for file in files:
            image_path = await upload_image(
                file,
                DEPARTMENT_GALLERY_DIR
            )

            uploaded_images.append(image_path)

            gallery_image = DepartmentGallary(
                department_id=department.id,
                image=image_path
            )

            db.add(gallery_image)

        await db.commit()

    except Exception:
        await db.rollback()

        for image_path in uploaded_images:
            delete_uploaded_file(image_path)

        raise

    return {
        "message": "Department gallery images uploaded successfully"
    }

# get department gallary images
async def get_department_gallery(
    department_id: int,
    db: AsyncSession,
    hospital: Hospital
):
    department = await get_hospital_department(
        department_id, db, hospital
    )

    result = await db.execute(
        select(DepartmentGallary).where(
            DepartmentGallary.department_id == department.id
        )
    )

    images = result.scalars().all()

    return {
        "message": "Department gallery fetched successfully",
        "images": [
            {
                "id": image.id,
                "dguid": image.dguid,
                "image": image.image
            }
            for image in images
        ]
    }

# delete department gallary images
async def delete_department_gallery(
    gallery_id: int,
    department_id: int,
    db: AsyncSession,
    hospital: Hospital
):
    department = await get_hospital_department(
        department_id, db, hospital
    )

    result = await db.execute(
        select(DepartmentGallary).where(
            DepartmentGallary.id == gallery_id,
            DepartmentGallary.department_id == department.id
        )
    )

    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery image not found"
        )

    image_path = image.image

    await db.delete(image)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    delete_uploaded_file(image_path)

    return {
        "message": "Department gallery image deleted successfully"
    }