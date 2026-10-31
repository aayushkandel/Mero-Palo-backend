
import os
import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException


UPLOAD_ROOT = Path("uploads")

THUMBNAIL_DIR = UPLOAD_ROOT / "thumbnails"
GALLERY_DIR = UPLOAD_ROOT / "hospital_gallery"

DEPARTMENT_THUMBNAIL_DIR = UPLOAD_ROOT / "department_thumbnails"
DEPARTMENT_GALLERY_DIR = UPLOAD_ROOT / "department_gallery"


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


for directory in [
    THUMBNAIL_DIR,
    GALLERY_DIR,
    DEPARTMENT_THUMBNAIL_DIR,
    DEPARTMENT_GALLERY_DIR
]:
    directory.mkdir(parents=True, exist_ok=True)


async def upload_image(file: UploadFile, upload_dir: Path):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, JPEG, PNG and WEBP images are allowed"
        )

    # Read file content
    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty"
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Image size must not exceed 5 MB"
        )

    # Generate unique filename
    filename = f"{uuid.uuid4().hex}{extension}"

    file_path = upload_dir / filename

    try:
        with open(file_path, "wb") as f:
            f.write(content)

    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Unable to save image"
        )

    # Return relative path for database storage
    return str(file_path).replace("\\", "/")


def delete_uploaded_file(file_path: str):

    if not file_path:
        return

    try:
        # Resolve the path to prevent deleting files outside uploads
        root = UPLOAD_ROOT.resolve()
        target = Path(file_path).resolve()

        if os.path.commonpath([str(root), str(target)]) != str(root):
            return

        if target.is_file():
            target.unlink()

    except (OSError, ValueError):
        pass
