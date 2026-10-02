from src.users.dtos import UserRegistration,UserLogin,UpdateUserProfile,ChangePassword
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.users.models import User
from fastapi import HTTPException,status
from src.utils.password_hash import get_password_hash,verify_password
import jwt
from datetime import datetime, timedelta,timezone
from src.utils.settings import settings
from zoneinfo import ZoneInfo


# user registration controller

async def register(body: UserRegistration, db: AsyncSession):

    if not body.name or not body.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter your name"
        )

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

    result= await db.execute(select(User).where( User.phone == body.phone))
    # Check if phone already exists
    exist_phone = result.scalar_one_or_none()

    # User exists
    if exist_phone:

        # User was previously deleted
        if exist_phone.deleted_at is not None:

            # Reactivate the deleted user
            exist_phone.name = body.name
            exist_phone.password = get_password_hash(body.password)
            exist_phone.deleted_at = None
            exist_phone.email=None
            exist_phone.address=None
           

            await db.commit()
            await db.refresh(exist_phone)

            return exist_phone

        # User is already active
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{body.phone} already exist"
        )

    # User does not exist, create a new user
    hash_password = get_password_hash(body.password)

    new_user = User(
        name=body.name,
        phone=body.phone,
        password=hash_password,
        role="user",
        deleted_at=None
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user




#user and super admin login controller

async def login_user(body:UserLogin,db:AsyncSession ):
 

    if not body.phone or not body.phone.strip():
                raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST,detail="Enter phone number")
    
    if not body.password or not body.password.strip():
                    raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST,detail="Enter password " )

    result= await db.execute(select(User).where(User.phone == body.phone))

    user= result.scalar_one_or_none()

    if not user:
           raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="User not found")

    
    if not verify_password(body.password,user.password):
           raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid password")

    
    
    if user.deleted_at is not None:
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User is deleted")
    
    exp_time=datetime.now()+timedelta(minutes=settings.EXP_TIME)
    token=jwt.encode({"_id":user.id,"role":user.role,"exp":exp_time},settings.SECRET_KEY,settings.ALGORITHM)

    return {"token":token,
                "role":user.role
            }
    

    # get user profile
def get_user_profile(user:User):
    if user.deleted_at is not None:
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User not found")
    return {
            "name":user.name,
            "email":user.email,
            "phone":user.phone,
            "address":user.address,
    }

#update the user profile

async def update_profile(body:UpdateUserProfile,db:AsyncSession,user:User):
    if user.deleted_at is not None:
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User not found")
    data=body.model_dump()

    for field,value in data.items():
            setattr(user,field,value)

    await db.commit()
    await db.refresh(user)

    return user


# delete user
async def delete_user(db:AsyncSession,user:User):
    result = await db.execute(select(User).where(User.id==user.id))
    user= result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User already deleted")
            
    user.deleted_at=datetime.now(ZoneInfo("Asia/Kathmandu"))
    await db.commit()

    return {
            "message":"User deleted",
            "deleted at":user.deleted_at
    }


# change password

async def change_password(body:ChangePassword,db:AsyncSession,user:User):

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
    if user.deleted_at is not None:
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    if not verify_password(body.old_password,user.password):
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Old password is invalid")

    if body.confirm_new_password != body.new_password:
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Confirm New password doesn't match")


    user.password=get_password_hash(body.new_password)
    await db.commit()
    await db.refresh(user)

    return{
          "message":"Password changed successfully",
          "name":user.name
    }


    