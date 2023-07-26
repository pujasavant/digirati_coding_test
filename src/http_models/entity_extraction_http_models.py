from pydantic import BaseModel, Extra


class PersonInfoRequest(BaseModel):
    class Config:
        extra = Extra.allow

    url: str


class Person(BaseModel):
    name: str
    count: int
    associated_places: list[dict]


class PersonInfoResponse(BaseModel):
    class Config:
        extra = Extra.allow

    url: str
    people: list[Person]
