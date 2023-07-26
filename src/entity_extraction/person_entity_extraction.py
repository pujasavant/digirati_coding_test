import re

import requests
import spacy

from http_models.common_http_models import CommonResponse
from http_models.entity_extraction_http_models import PersonInfoRequest, PersonInfoResponse, Person


class PersonEntityExtractor:
    """
    Class with method implementations for extracting details from text related to PERSON entity

    @author Pooja Savant
    """

    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.nlp.disable_pipes(["tagger", "parser", "attribute_ruler", "lemmatizer"])
        print("NLP Model setup:", self.nlp.analyze_pipes())

    def get_all_people_details(self, person_info_request: PersonInfoRequest) -> PersonInfoResponse | CommonResponse:
        """
        Identify and sort by count all the people in the text document and create a list of places that
        are associated with each of the person in the document.
        Return any metadata fields sent in the initial request
        :param person_info_request: PersonInfoRequest
        :return: PersonInfoResponse | CommonResponse
        """
        doc_text = self.fetch_text_from_url(person_info_request.url)
        if not isinstance(doc_text, str):
            return doc_text
        people_loc_list = self.get_people_places_details(doc_text, lookup_location_by=100)
        response_dict = person_info_request.dict()
        response_dict['people'] = [Person(**people_loc_dict) for people_loc_dict in people_loc_list]
        return PersonInfoResponse.parse_obj(response_dict)

    def fetch_text_from_url(self, url: str) -> str | CommonResponse:
        """
        Fetch the clean text from the URL
        :param url:
        :return:
        """
        resp = requests.get(url)
        if resp.status_code == 200:
            text = resp.text
            text = self.clean_text(text)
            return text
        else:
            return CommonResponse(status_code=500, message="Error while fetching text from url")

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Basic steps to clean the text
        :param text:
        :return:
        """
        cleaned_text = text.replace('\r\n', '. ')
        cleaned_text = re.sub(r'[\.\s]{2,}', '. ', cleaned_text)
        return cleaned_text

    def get_people_places_details(self, doc_text: str, lookup_location_by: int = 100) -> list[dict]:
        """
        Method to extract person entities and locations that are around the person along with
        count of entities
        :param doc_text: str
        :param lookup_location_by: int
        :return: list of people with their frequency and location details
        """
        spacy_doc = self.nlp(doc_text)
        token_spans = self.get_all_tokens(spacy_doc)
        location_dict, people_dict = self.extract_person_location_entities(spacy_doc)
        people_dict = self.accumulate_locations_near_person(people_dict, location_dict,
                                                            token_spans, lookup_location_by)

        people_details_list = []
        for person, value in people_dict.items():
            person_details_dict = {'name': person, 'count': len(value['spans'])}
            place_detail_list = []
            if 'location' in value:
                for loc, loc_count in value['location'].items():
                    place_detail_list.append({
                        'name': loc,
                        'count': loc_count
                    })
                place_detail_list = sorted(place_detail_list, key=lambda d: d['count'], reverse=True)
            person_details_dict['associated_places'] = place_detail_list
            people_details_list.append(person_details_dict)
        people_details_list = sorted(people_details_list, key=lambda d: d['count'], reverse=True)
        return people_details_list

    @staticmethod
    def get_all_tokens(spacy_doc) -> list:
        """
        Method to get list of tokens from the spacy doc object along with the token span
        :param spacy_doc:
        :return: list of tokens with corresponding character span
        """
        token_spans = []
        prev_span = -1
        for token in spacy_doc:
            end_span = prev_span + len(token.text_with_ws)
            token_spans.append(((prev_span + 1, end_span), token.text))
            prev_span = end_span
        return token_spans

    @staticmethod
    def extract_person_location_entities(spacy_doc):
        """
        Method to extract 'PERSON' and 'GPE' (Geographical locations) from text using Spacy
        :param spacy_doc:
        :return: dict containing people name and their span tags,
                dict containing locations and their span tags
        """
        people_dict, location_dict = {}, {}
        for entity in spacy_doc.ents:
            if entity.label_ == 'PERSON':
                if entity.text not in people_dict:
                    people_dict[entity.text] = {'spans': [(entity.start_char, entity.end_char)]}
                else:
                    people_dict[entity.text]['spans'].append((entity.start_char, entity.end_char))
            elif entity.label_ == 'GPE':
                if entity.text not in location_dict:
                    location_dict[entity.text] = [(entity.start_char, entity.end_char)]
                else:
                    location_dict[entity.text].append((entity.start_char, entity.end_char))
        return location_dict, people_dict

    @staticmethod
    def accumulate_locations_near_person(people_dict: dict, location_dict: dict, token_spans: list,
                                         lookup_location_by: int) -> dict:
        """
        Method to gather location mentioned around a person in the text along with it's frequency
        :param people_dict:
        :param location_dict:
        :param token_spans:
        :param lookup_location_by:
        :return: dict containing people with location details
        """
        for person, spans in people_dict.items():
            for person_span in spans['spans']:
                search_start_span = -1
                search_end_span = -1
                if person_span[0] == 0:
                    search_start_span = 0
                for i, token in enumerate(token_spans):
                    if search_start_span < 0 and token[0][0] == person_span[0]:
                        if i - lookup_location_by < 0:
                            search_start_span = 0
                        else:
                            search_start_span = token_spans[i - lookup_location_by][0][0]
                    if search_end_span < 0 and token[0][1] == person_span[1]:
                        if i + lookup_location_by >= len(token_spans):
                            search_end_span = token_spans[-1][0][1]
                        else:
                            search_end_span = token_spans[i + lookup_location_by][0][1]
                    if search_start_span >= 0 and search_end_span > 0:
                        break
                for loc, loc_span_list in location_dict.items():
                    for loc_span in loc_span_list:
                        if search_start_span <= loc_span[0] < search_end_span:
                            if 'location' not in people_dict[person]:
                                people_dict[person]['location'] = {}
                            if loc not in people_dict[person]['location']:
                                people_dict[person]['location'][loc] = 1
                            else:
                                people_dict[person]['location'][loc] = people_dict[person]['location'][loc] + 1
        return people_dict
