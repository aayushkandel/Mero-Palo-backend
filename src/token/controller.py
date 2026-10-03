from src.token.dtos import CreateToken
from src.departments.models import Department
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.users.models import User
from src.hospitals.models import Hospital
from fastapi import HTTPException,status
from datetime import datetime, timedelta,timezone
from zoneinfo import ZoneInfo
from src.departments.models import Schedule
from src.utils import generate_token, calculate_expected_time
from src.token.models import Token

async def create_token(body: CreateToken,hospital_id: int,department_id: int,db: AsyncSession,user: User):

    # ==========================================
    # 1. Validate patient information
    # ==========================================

    if not body.dates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please select a date"
        )

    if not body.patient_name or not body.patient_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter patient name"
        )

    if not body.patient_address or not body.patient_address.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter patient address"
        )

    if body.patient_age is None or body.patient_age <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter valid patient age"
        )

    if not body.patient_phone or not body.patient_phone.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter patient phone"
        )


    # ==========================================
    # 2. Check hospital
    # ==========================================

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


    # ==========================================
    # 3. Check department
    # ==========================================

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


    # ==========================================
    # 4. Get schedule for selected date
    # ==========================================

    schedule_result = await db.execute(
        select(Schedule).where(
            Schedule.hospital_id == hospital_id,
            Schedule.department_id == department_id,
            Schedule.date == body.dates
        )
    )

    schedule = schedule_result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found for this department and date"
        )


    # ==========================================
    # 5. Check token service start time
    # ==========================================

    if schedule.token_start is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token service start time is not configured"
        )


    # ==========================================
    # 6. Generate token
    #
    # Example:
    # BH-R-001
    #
    # token_number:
    # 1
    # ==========================================

    token, token_number = await generate_token(
        hospital_id=hospital_id,
        department_id=department_id,
        dates=body.dates,
        db=db
    )


    # ==========================================
    # 7. Calculate expected time
    #
    # 001 -> 09:00
    # 002 -> 09:03
    # 003 -> 09:06
    # ==========================================

    expected_time = calculate_expected_time(
        schedule.token_start,
        token_number
    )


    # ==========================================
    # 8. Create token
    # ==========================================

    new_token = Token(

        user_id=user.id,

        hospital_id=hospital_id,

        department_id=department_id,

        patient_name=body.patient_name.strip(),

        patient_address=body.patient_address.strip(),

        patient_age=body.patient_age,

        patient_phone=body.patient_phone.strip(),

        token=token,

        dates=body.dates,

        expected_time=expected_time,

        # These will be calculated later
        started_at=None,
        ended_at=None,
        actual_time=None,
        waiting_time=None,

        # Initial status
        token_status="waiting",

        # Not deleted
        deleted_by_user=None,
        deleted_by_department=None
    )


    # ==========================================
    # 9. Save to database
    # ==========================================

    db.add(new_token)

    await db.commit()

    await db.refresh(new_token)


    return new_token