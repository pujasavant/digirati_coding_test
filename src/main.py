import uvicorn
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from entity_extraction.person_entity_extraction import PersonEntityExtractor
from http_models.common_http_models import CommonResponse
from http_models.entity_extraction_http_models import PersonInfoRequest, PersonInfoResponse

"""
Main class with API routes

@author Pooja Savant
"""
app = FastAPI(
    title="Digirati Entity Extraction POC",
    description="API documentation of services incorporated in Digirati Entity Extraction POC\nAuthor: Pooja Savant",
    version="0.0.1"
)
person_entity_extractor = PersonEntityExtractor()


@app.get("/")
def get_app_status():
    return CommonResponse(status_code=200, message="App started")


@app.post("/entity_extraction/people_info", response_model=PersonInfoResponse | CommonResponse,
          response_model_exclude_none=True)
def get_people_info(person_info_request: PersonInfoRequest):
    return person_entity_extractor.get_all_people_details(person_info_request)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
