# -*- coding: utf-8 -*-


import requests
import os
from dotenv import load_dotenv
from urllib.parse import urljoin


load_dotenv()
api_key = str(os.getenv('ESCRIPT_API'))
base_url = 'https://transcription.amphilsoc.org'

headers = {'Accept': 'application/json', 'Authorization': f'Token {api_key}'}

projects = {
    'bella':,
    'drinker':,
    'eastwick':,
    'ed_workshops':,
    'fisher':,
    'gratz':,
    
}


def paginate(loop, url):
    results = []
    while loop is True:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        r = r.json()
        payload = [item for item in r['results']]
        results = results + payload
        status = r['next']
        if status == None:
            loop = False
        else:
            url = status
    return results


def get_all_projects():
    '''Returns a list of dictionaries with key metadata for all projects'''
    url = urljoin(base_url, 'api/projects/')
    payload = paginate(True, url)
    return payload


def get_all_documents():
    url = urljoin(base_url, 'api/documents/')
    payload = paginate(True, url)
    return payload


def get_proj_metadata(proj_num):
    url = urljoin(base_url, f'api/projects/{proj_num}/')
    payload = requests.get(url, headers=headers)
    return payload


def get_doc_parts(doc_num):
    url = urljoin(base_url, f'api/documents/{doc_num}/parts/')
    payload = paginate(True, url)
    return payload


def get_part_lines(doc_num, part_num):
    url = urljoin(base_url, 'fapi/documents/{doc_num}/parts/{part_num}/lines/')
    payload = paginate(True, url)
    return payload


def update_transcription_data(docs, exclude, new=False):
    for d in docs:
        pk = d['pk']
        transcriptions = d['transcriptions']
        if new is True:
            for p in d['parts']:
                p.update({'exclude': True})
        else:
            for t in transcriptions:
                if 'manual' in t.values():
                    canon = list(t.keys())[0]
            if pk not in exclude.keys():
                for p in d['parts']:
                    p.update({'canonical_transcription': canon, 'exclude': False})
            else:
                exclude_list = exclude[pk]
                for p in d['parts']:
                    part_pk = p['pk']
                    if part_pk in exclude_list:
                        p.update({'canonical_transcription': canon, 'exclude': True})
                    else:
                        p.update({'canonical_transcription': canon, 'exclude': False})
    return docs
