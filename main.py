from fastapi import FastAPI
from src.utils.db import Base, engine
from src.hospitals.models import Hospital
from src.departments.models import Department
from src.users.models import User
from src.token.models import Token


app=FastAPI()

Base.metadata.create_all(engine)


