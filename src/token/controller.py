from src.token.dtos import CreateToken,GetByDate
from src.departments.models import Department
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.users.models import User
from src.hospitals.models import Hospital
from fastapi import HTTPException,status
from datetime import datetime, timedelta,timezone
from zoneinfo import ZoneInfo
from src.departments.models import Schedule
from src.utils.generate_token import generate_token
from src.utils.calculate_expected_time import calculate_expected_time
from src.utils.calculate_dynamic_expected_time import calculate_dynamic_expected_times
from src.token.models import Token
from src.utils.calculate_new_token_expected_time import calculate_new_token_expected_time
async def create_token(
    body: CreateToken,
    hospital_id: int,
    department_id: int,
    db: AsyncSession,
    user: User
):

    # =========================================================
    # VALIDATION
    # =========================================================

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

    # =========================================================
    # GET HOSPITAL
    # =========================================================

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

    # =========================================================
    # GET DEPARTMENT
    # =========================================================

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

    # =========================================================
    # GET SCHEDULE
    # =========================================================

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

    if schedule.token_start is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token service start time is not configured"
        )

    # =========================================================
    # GET EXISTING TOKENS FOR THIS DEPARTMENT AND DATE
    # =========================================================

    tokens_result = await db.execute(
        select(Token)
        .where(
            Token.department_id == department_id,
            Token.dates == body.dates,
            Token.deleted_by_department.is_(None)
        )
        .order_by(Token.id.asc())
    )

    existing_tokens = tokens_result.scalars().all()

    # =========================================================
    # CHECK WHETHER ACTUAL TOKEN SERVICE HAS STARTED
    #
    # IMPORTANT:
    #
    # schedule.token_start = planned service start
    #
    # token.started_at = actual service start
    #
    # We use started_at here.
    # =========================================================

    service_started = any(
        token.started_at is not None
        for token in existing_tokens
    )

    # =========================================================
    # GENERATE TOKEN
    # =========================================================

    token, token_number = await generate_token(
        hospital_id=hospital_id,
        department_id=department_id,
        dates=body.dates,
        db=db
    )

    # =========================================================
    # CALCULATE EXPECTED TIME
    # =========================================================

    if service_started:

        # -----------------------------------------------------
        # Service has already started.
        #
        # Do NOT use:
        #
        # calculate_expected_time()
        #
        # because that uses the fixed +3 minute calculation.
        # -----------------------------------------------------

        expected_time = calculate_new_token_expected_time(
            tokens=existing_tokens
        )

        # -----------------------------------------------------
        # Safety check
        # -----------------------------------------------------

        if expected_time is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to calculate dynamic expected time"
            )

    else:

        # -----------------------------------------------------
        # Service has NOT started.
        #
        # Use the original schedule-based prediction.
        # -----------------------------------------------------

        expected_time = calculate_expected_time(
            schedule.token_start,
            token_number
        )

    # =========================================================
    # CREATE TOKEN
    # =========================================================

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

        started_at=None,

        ended_at=None,

        execution_duration=None,

        waiting_time=None,

        token_status="waiting",

        deleted_by_user=None,

        deleted_by_department=None
    )

    # =========================================================
    # SAVE
    # =========================================================

    db.add(new_token)

    await db.commit()

    await db.refresh(new_token)

    return new_token


# get the oldest waiting token of the day

async def get_first_waiting_token(
    body: GetByDate,
    db: AsyncSession,
    department: Department
):

    # ---------------------------------------------------------
    # Get oldest waiting token
    # ---------------------------------------------------------

    result = await db.execute(
        select(Token)
        .where(
            Token.department_id == department.id,
            Token.dates == body.dates,
            Token.token_status == "waiting",
            Token.deleted_by_department.is_(None)
        )
        .order_by(Token.id.asc())
        .limit(1)
        .with_for_update()
    )

    token = result.scalar_one_or_none()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No waiting token found for this date"
        )

    # ---------------------------------------------------------
    # Current actual start time
    # ---------------------------------------------------------

    started_at = datetime.now(timezone.utc)

    # ---------------------------------------------------------
    # Find previous completed token
    # ---------------------------------------------------------

    previous_result = await db.execute(
        select(Token)
        .where(
            Token.department_id == department.id,
            Token.dates == body.dates,
            Token.id < token.id,
            Token.token_status == "completed",
            Token.ended_at.is_not(None),
            Token.deleted_by_department.is_(None)
        )
        .order_by(Token.id.desc())
        .limit(1)
    )

    previous_token = previous_result.scalar_one_or_none()

    # ---------------------------------------------------------
    # Calculate actual waiting time
    # ---------------------------------------------------------

    if previous_token:

        waiting_seconds = int(
            (
                started_at - previous_token.ended_at
            ).total_seconds()
        )

        if waiting_seconds < 0:
            waiting_seconds = 0

        token.waiting_time = waiting_seconds

    else:
        # First token has no previous completed token.
        token.waiting_time = 0

    # ---------------------------------------------------------
    # Start token
    # ---------------------------------------------------------

    token.started_at = started_at

    token.token_status = "serving"

    # Once token actually starts,
    # its expected time becomes its actual start time.

    token.expected_time = started_at.astimezone(
        ZoneInfo("Asia/Kathmandu")
    ).time().replace(microsecond=0)

    await db.commit()

    await db.refresh(token)

    return token

async def complete_token(
    token_id: int,
    db: AsyncSession,
    department: Department
):

    # ---------------------------------------------------------
    # Find serving token
    # ---------------------------------------------------------

    result = await db.execute(
        select(Token)
        .where(
            Token.id == token_id,
            Token.department_id == department.id,
            Token.token_status == "serving",
            Token.deleted_by_department.is_(None)
        )
        .with_for_update()
    )

    token = result.scalar_one_or_none()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Serving token not found"
        )

    # ---------------------------------------------------------
    # Make sure token has started
    # ---------------------------------------------------------

    if token.started_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has not started yet"
        )

    # ---------------------------------------------------------
    # End token
    # ---------------------------------------------------------

    ended_at = datetime.now(timezone.utc)

    token.ended_at = ended_at

    # ---------------------------------------------------------
    # Calculate actual execution duration
    # ---------------------------------------------------------

    execution_seconds = int(
        (
            ended_at - token.started_at
        ).total_seconds()
    )

    if execution_seconds < 0:
        execution_seconds = 0

    token.execution_duration = execution_seconds

    # ---------------------------------------------------------
    # Change status
    # ---------------------------------------------------------

    token.token_status = "completed"

    # ---------------------------------------------------------
    # Get all tokens for this department and date
    # ---------------------------------------------------------

    result = await db.execute(
        select(Token)
        .where(
            Token.department_id == department.id,
            Token.dates == token.dates,
            Token.deleted_by_department.is_(None)
        )
        .order_by(Token.id.asc())
    )

    all_tokens = result.scalars().all()

    # ---------------------------------------------------------
    # Dynamically recalculate expected time
    # for all remaining waiting tokens
    # ---------------------------------------------------------

 

    calculate_dynamic_expected_times(
        all_tokens
    )

    # ---------------------------------------------------------
    # Save everything in one transaction
    # ---------------------------------------------------------

    await db.commit()

    await db.refresh(token)

    return token
