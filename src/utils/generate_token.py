from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.hospitals.models import Hospital
from src.departments.models import Department
from fastapi  import HTTPException,status
from src.token.models import Token


async def generate_token(
    hospital_id: int,
    department_id: int,
    dates,
    db: AsyncSession
):

    # Get hospital
    hospital_result = await db.execute(
        select(Hospital).where(
            Hospital.id == hospital_id,
            Hospital.deleted_at.is_(None)
        )
    )

    hospital = hospital_result.scalar_one_or_none()

    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital not found"
        )


    # Get department
    department_result = await db.execute(
        select(Department).where(
            Department.id == department_id,
            Department.hospital_id == hospital_id,
            Department.deleted_at.is_(None)
        )
    )

    department = department_result.scalar_one_or_none()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )


    # Hospital prefix
    hospital_words = hospital.name.strip().split()

    if len(hospital_words) >= 2:
        hospital_prefix = (
            hospital_words[0][0] +
            hospital_words[1][0]
        ).upper()
    else:
        hospital_prefix = hospital_words[0][:2].upper()


    # Department prefix
    department_prefix = department.name.strip()[0].upper()


    # Get last token for this department on this date
    result = await db.execute(
        select(Token)
        .where(
            Token.hospital_id == hospital_id,
            Token.department_id == department_id,
            Token.dates == dates
        )
        .order_by(Token.id.desc())
        .limit(1)
    )

    last_token = result.scalar_one_or_none()


    # Generate next number
    if last_token:
        last_number = int(last_token.token.split("-")[-1])
        next_number = last_number + 1
    else:
        next_number = 1


    # Maximum 999 tokens per day
    if next_number > 999:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 999 tokens allowed for this department today"
        )


    # Final token
    token_number = f"{next_number:03d}"
    token_value= f"{hospital_prefix}-{department_prefix}-{token_number}"

    return token_value,next_number