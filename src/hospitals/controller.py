from src.hospitals.dtos import HospitalRegister,HospitalLogin,HospitalProfileUpdate,ChangePassword
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from src.departments.dtos import DepartmentRegister,DepartmentUpdate,ScheduleCreate,OpenStatus,ScheduleDate
from src.departments.models import Department,Schedule
from src.hospitals.models import Hospital
from fastapi import HTTPException,status
from src.utils.password_hash import get_password_hash,verify_password
import jwt
from datetime import datetime, timedelta,timezone
from src.utils.settings import settings
from zoneinfo import ZoneInfo


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

            await db.commit()
            await db.refresh(exist_phone)

            return {
                "id": exist_phone.id,
                "huid": exist_phone.huid,
                "name": exist_phone.name.title(),
                "phone": exist_phone.phone,
                "registration_no": exist_phone.registration_no.upper(),
                "is_authorized": exist_phone.is_authorized
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
        deleted_at=None
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
        "is_authorized": new_hospital.is_authorized
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

            await db.commit()
            await db.refresh(exist_phone)

            return{
                   "id": exist_phone.id,
                   "duid": exist_phone.duid,
                   "name": exist_phone.name.title(),
                    "phone": exist_phone.phone,
                    "department_room_no":exist_phone.department_room_no
                    
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
        deleted_at=None
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
          "department_room_no":new_department.department_room_no
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
            
            if body.registration_close >= body.registration_start:
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

async def get_schedule_by_date(body:ScheduleDate,department_id:int,db:AsyncSession,hospital:Hospital):

       if not body.dates:
              raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Give Date")

       result=await db.execute(select(Schedule).where(
              Schedule.date==body.dates,
              Schedule.department_id==department_id,
              Schedule.hospital_id==hospital.id
       ))

       schedule=result.scalar_one_or_none()

       if not schedule:
              raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                  detail=f"Schedule not found for {body.dates}")

       return schedule

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

       