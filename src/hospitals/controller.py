from src.hospitals.dtos import HospitalRegister,HospitalLogin,HospitalProfileUpdate,ChangePassword
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.departments.dtos import DepartmentRegister,DepartmentUpdate
from src.departments.models import Department
from src.hospitals.models import Hospital
from fastapi import HTTPException,status
from src.utils.password_hash import get_password_hash,verify_password
import jwt
from datetime import datetime, timedelta,timezone
from src.utils.settings import settings
from zoneinfo import ZoneInfo


# hospital register
async def register(body:HospitalRegister,db:AsyncSession):

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

    result =await db.execute(select(Hospital).where(Hospital.phone == body.phone))
    exist_phone=result.scalar_one_or_none()

    if exist_phone:
          if exist_phone.deleted_at is not None:

                exist_phone.name=body.name
                exist_phone.password=get_password_hash(body.password)
                exist_phone.email=None
                exist_phone.address=None
                exist_phone.deleted_at=None

                await db.commit()
                await db.refresh(exist_phone)

                return exist_phone
          
          raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{body.phone} already exist"
          )

    hash_password=get_password_hash(body.password)

    new_hospital=Hospital(
          name=body.name,
          phone=body.phone,
          registration_no=body.registration_no,
          password=hash_password,
          is_authorized=False,
          deleted_at=None
    )
    db.add(new_hospital)
    await db.commit()
    await db.refresh(new_hospital)

    return new_hospital



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

async def depart_register(body:DepartmentRegister,db:AsyncSession,hospital:Hospital):

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
        hospital_exist= await db.execute(select(Hospital).where(Hospital.id==hospital.id))

        hospital=hospital_exist.scalar_one_or_none()

        if not hospital:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="you are authorized to create the departments")

        result =await db.execute(select(Department).where(Department.phone == body.phone))
        exist_phone=result.scalar_one_or_none()
        
        if exist_phone:
                  if exist_phone.deleted_at is not None:
        
                        exist_phone.name=body.name
                        exist_phone.password=get_password_hash(body.password)
                        exist_phone.department_room_no=None
                        exist_phone.deleted_at=None
        
                        await db.commit()
                        await db.refresh(exist_phone)
        
                        return exist_phone
                  
                  raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"{body.phone} already exist"
                  )

        name_result=await db.execute(select(Department).where(Department.hospital_id==hospital.id,Department.name==body.name,Department.deleted_at.is_(None)))
        exist_name=name_result.scalar_one_or_none()

        if exist_name:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Department {body.name} already exist for {hospital.name}")

        room_result= await db.execute(select(Department).where(Department.hospital_id==hospital.id,Department.department_room_no==body.department_room_no,Department.deleted_at.is_(None)))
        exist_department_room_no=room_result.scalar_one_or_none()

        if exist_department_room_no:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Department room number {body.department_room_no} already exist for {hospital.name}")

       
        hash_password = get_password_hash(body.password)

        new_department=Department(
                name=body.name,
                phone=body.phone,
                hospital_id=hospital.id,
                department_room_no=body.department_room_no,
                password=hash_password,
                deleted_at=None
        )
        db.add(new_department)
        await db.commit()
        await db.refresh(new_department)

        return new_department

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


async def update_department_profile(
    department_id: int,
    body: DepartmentUpdate,
    db: AsyncSession,
    hospital: Hospital
):

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

    # --------------------------------------------------
    # PHONE CHECK
    # Phone must be unique across ALL active departments
    # --------------------------------------------------

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

    # --------------------------------------------------
    # DEPARTMENT NAME CHECK
    # Name must be unique within this hospital
    # Case-insensitive
    # --------------------------------------------------

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

    # --------------------------------------------------
    # ROOM NUMBER CHECK
    # Room number must be unique within this hospital
    # Case-insensitive
    # --------------------------------------------------

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

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

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
      