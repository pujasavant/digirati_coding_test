from fastapi.testclient import TestClient

from main import app

"""
Unit test cases for the main app

@author: Pooja Savant
"""
test_client = TestClient(app)


def test_get_people_info():
    request_json = {
        "url": "https://www.gutenberg.org/cache/epub/345/pg345.txt",
        "author": "Bram Stoker",
        "title": "Dracula"
    }
    response = test_client.post("/entity_extraction/people_info",
                                json=request_json)
    assert response.status_code == 200
    resp_json = response.json()
    assert len(resp_json) == 4
    assert resp_json['url'] == request_json['url']
    assert resp_json['author'] == request_json['author']
    assert resp_json['title'] == request_json['title']
    assert len(resp_json['people']) == 497
