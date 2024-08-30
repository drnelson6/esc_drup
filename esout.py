# -*- coding: utf-8 -*-


import requests
import os
from dotenv import load_dotenv
from urllib.parse import urljoin
import json

# environmental variables
load_dotenv()
api_key = str(os.getenv('ESCRIPT_API'))
base_url = 'https://transcription.amphilsoc.org'

headers = {'Accept': 'application/json', 'Authorization': f'Token {api_key}'}

# load project directories
with open('projects.json', 'r') as f:
    project_dirs = json.load(f)


def dump_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, default=lambda o: o.__dict__, indent=4) 


# classes to represent eScriptorium data structures
class Project:
    def __init__(self, pk, nid, slug, name):
        self.pk = pk
        self.nid = nid
        self.slug = slug
        self.name = name
        self.folder = project_dirs[str(pk)]
        self.documents = []

    def add_docs(self, doc_list):
        for d in doc_list:
            self.documents.append(d)


class Document:
    def __init__(self, pk, nid, name):
        self.pk = pk
        self.nid = nid
        self.name = name
        self.parts = []

    def add_parts(self, part_list):
        for part in part_list:
            self.parts.append(part)


class Part:
    def __init__(self, pk, file):
        self.pk = pk
        self.file = file
        # transcription metadata is on the transcription, but the actual transcription is
        # called from the part metadata
        self.transcriptions = []
        self.exclude = True

    def add_transcriptions(self, trans_list):
        for t in trans_list:
            self.transcriptions.append(t)


class Transcription:
    def __init__(self, pk, name):
        self.pk = pk
        self.name = name
        self.is_canonical = False


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


def get_raw_projects():
    '''Returns a list of dictionaries with key metadata for all projects'''
    url = urljoin(base_url, 'api/projects/')
    payload = paginate(True, url)
    return payload


def get_raw_documents():
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


def get_doc_transcriptions(doc_num):
    url = urljoin(base_url, f'api/documents/{doc_num}/transcriptions/')
    payload = requests.get(url, headers=headers).json()
    return payload


def get_part_lines(doc_num, part_num):
    url = urljoin(base_url, f'api/documents/{doc_num}/parts/{part_num}/lines/')
    payload = paginate(True, url)
    return payload


def get_part_transcription(doc_num, part_num):
    url = urljoin(base_url, f'api/documents/{doc_num}/parts/{part_num}/transcriptions/')
    payload = paginate(True, url)
    return payload


def search_for_matches(data, meta):
    '''Search for matches and update data with Drupal NIDs.
    Prints any non-matches.

    Input:
    - data: document data dump from eScriptorium
    -meta: collection metadata from Drupal

    Output: data updated with Drupal NIDs
    '''
    for d in data:
        title = d['name']
        for m in meta:
            if m['title'] == title:
                d.update({'nid': m['nid']})
                break
        else:
            print(f'No match for {title}.')
    return data


def create_docs_from_dict(docs, from_api=False):
    doc_list = []
    for d in docs:
        pk = d['pk']
        nid = d['nid']
        name = d['name']
        doc = Document(pk, nid, name)
        part_list = []
        for p in d['parts']:
            part_pk = p['pk']
            if from_api is True:
                file = p['filename']
                exclude = True
            else:
                file = p['file']
                exclude = p['exclude']
            part = Part(part_pk, file)
            part.exclude = exclude
            trans_list = []
            for t in p['transcriptions']:
                trans_pk = t['pk']
                trans_name = t['name']
                if from_api is True:
                    canon = False
                else:
                    canon = t['is_canonical']
                trans = Transcription(trans_pk, trans_name)
                trans.is_canonical = canon
                trans_list.append(trans)
            part.add_transcriptions(trans_list)
            part_list.append(part)
        doc.add_parts(part_list)
        doc_list.append(doc)

    return doc_list


def create_projs_from_dict(projs):
    proj_list = []
    for p in projs:
        pk = p['pk']
        nid = p['nid']
        slug = p['slug']
        name = p['name']
        project = Project(pk, nid, slug, name)
        raw_docs = p['documents']
        docs = create_docs_from_dict(raw_docs)
        project.add_docs(docs)
        proj_list.append(project)

    return proj_list


def load_json(path):
    with open(path, 'r') as f:
        data = json.load(f)
    projects = create_projs_from_dict(data)
    return projects


def find_project_by_folder(folder, projects):
    for project in projects:
        if project.folder == folder:
            target = project

    return target

def search_for_doc(project, pk):
    docs = project.documents
    for doc in docs:
        if doc.pk == pk:
            target = doc

    return target


def update_part_status(part, transcription):
    part.exclude = False
    for trans in part.transcriptions:
        if trans.name == transcription:
            trans.is_canonical = True


def update_doc_transcriptions(doc, transcription, exclude=None):
    parts = doc.parts
    if exclude is None:
        exclude = []
    for part in parts:
        if part.pk not in exclude:
            update_part_status(part, transcription)


def update_selected_parts(doc, transcription, parts):
    all_parts = doc.parts
    exclude = [p.pk for p in all_parts if p.pk not in parts]
    update_doc_transcriptions(doc, transcription, exclude=exclude)
