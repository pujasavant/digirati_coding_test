from pydantic import BaseModel


class CommonResponse(BaseModel):
    status_code: str
    message: str
