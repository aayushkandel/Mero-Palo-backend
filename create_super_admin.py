import asyncio
import getpass

from sqlalchemy import select
from src.token.models import Token
from src.departments.models import Department
from src.hospitals.models import Hospital
from src.utils.db import SessionLocal
from src.users.models import User
from src.utils.password_hash import get_password_hash


async def create_admin():

    async with SessionLocal() as db:

        name = input("Enter name: ")

        phone = input("Enter phone: ")

        password = getpass.getpass("Enter password: ")


        result = await db.execute(
            select(User).where(User.phone == phone)
        )

        existing_admin = result.scalar_one_or_none()

        if existing_admin:

            print(f"Username {phone} already exists.")

            return




        new_admin = User(

            name=name,

            phone=phone,

            password=get_password_hash(password),

            role="superAdmin",
            deleted_at=None

        )


        db.add(new_admin)

        await db.commit()

        await db.refresh(new_admin)


        print("Admin created successfully.")

        print("name:", new_admin.name)

        print("phone:", new_admin.phone)

        print("Role:", new_admin.role)


if __name__ == "__main__":
    asyncio.run(create_admin())