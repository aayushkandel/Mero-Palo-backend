from fastapi import APIRouter,Depends,status,Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.token.dtos import CreateToken,GetByDate
from src.utils.db import get_db
from src.token import controller
from src.utils import is_auth
from src.users.models import User
from src.hospitals.models import Hospital
from src.departments.models import Department
from src.utils.is_auth import is_department_authenticated,is_user_authenticated

token_routes=APIRouter(prefix="/tokens")

@token_routes.post("/create/{hospital_id}/{department_id}",status_code=status.HTTP_201_CREATED)
async def create_token_route(body: CreateToken,hospital_id: int,department_id: int,db: AsyncSession = Depends(get_db),user: User = Depends(is_user_authenticated)):
    return await controller. create_token(body,hospital_id,department_id,db,user)

@token_routes.get("/token_service",status_code=status.HTTP_200_OK)
async def get_waiting_token(body:GetByDate,db:AsyncSession=Depends(get_db),department:Department=Depends(is_department_authenticated)):
    return await controller.get_first_waiting_token(body,db,department)

@token_routes.put("/complete/{token_id}")
async def complete_token_route(
    token_id:int,
    db: AsyncSession = Depends(get_db),
    department: Department = Depends(is_department_authenticated)
):

    return await controller.complete_token(
        token_id,
        db,
        department,
    )