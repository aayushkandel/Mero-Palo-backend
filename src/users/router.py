from fastapi import APIRouter,Depends,status
from sqlalchemy.orm import Session
from src.users.dtos import UserRegistration
from src.utils.db import get_db
from src.users import controller

user_routes= APIRouter(prefix="/users")

@user_routes.post("/register", status_code=status.HTTP_201_CREATED)
def register(body:UserRegistration,db:Session=Depends(get_db)):
    return controller.register(body,db)