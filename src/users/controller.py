from src.users.dtos import UserRegistration
from sqlalchemy.orm import Session
from src.users.models import User
from fastapi import HTTPException,status
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

def get_password_hash(password):
    return password_hash.hash(password)

def register(body:UserRegistration,db:Session):

    if is_email:=db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"{body.email} already exist")

    if is_phone:=db.query(User).filter(User.phone == body.phone).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"{body.phone} already exist")

    hash_password=get_password_hash(body.password)

    new_user=User(
        name= body.name,
        email=body.email,
        phone=body.phone,
        password=hash_password,
        role="user"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user