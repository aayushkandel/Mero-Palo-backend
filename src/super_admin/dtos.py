from pydantic import BaseModel


class HospitalAuthorization(BaseModel):
    is_authorized:bool