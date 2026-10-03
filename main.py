from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.utils.db import Base, engine

from src.hospitals.models import Hospital
from src.departments.models import Department
from src.users.models import User
from src.token.models import Token

from src.users.router import user_routes
from src.hospitals.router import hospital_routes
from src.departments.router import department_routes
from src.super_admin.router import super_admin_routes
from src.token.router import token_routes

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(user_routes)
app.include_router(hospital_routes)
app.include_router(department_routes)
app.include_router(super_admin_routes)
app.include_router(token_routes)