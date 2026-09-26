import os
import uuid
from fastapi import UploadFile, HTTPException


UPLOAD_DIR = "uploads/thumbnails"

os.makedirs(UPLOAD_DIR, exist_ok=True)


async def upload_thumbnail(file: UploadFile):

    allowed_extensions = [".jpg", ".jpeg", ".png", ".webp"]

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, JPEG, PNG and WEBP images are allowed"
        )

    filename = f"{uuid.uuid4()}{extension}"

    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    return file_path