# -*- coding: utf-8 -*-


import requests
import os
from dotenv import load_dotenv
from urllib.parse import urljoin
import click

load_dotenv()
api_key = str(os.getenv('ESCRIPT_API'))
base_url = 'https://transcription.amphilsoc.org'

headers = {'Accept': 'application/json', 'Authorization': f'Token {api_key}'}


def connect_escr(headers):
    session = requests.Session()
    session.headers.update(headers)
    return session


def create_project(session, project_name):
    url = urljoin(base_url, 'api/projects/')
    projects = session.get(url).json()['results']
    project_names = [n['name'] for n in projects]
    if project_name in project_names:
        raise RuntimeError("Project already exists.")
    else:
        data = {
            "name": project_name,
            "guidelines": "",
            "tags": []
        }
        response = session.post(url, json=data)
        return response


def create_document(session, document_name, project_name):
    url = urljoin(base_url, 'api/documents/')
    project_name = project_name.lower()
    project_name = project_name.replace(' ', '-')
    project_name = project_name.replace("'", '')
    data = {
        "name": document_name,
        "project": project_name,
        "main_script": "Latin",
        "read_direction": "ltr",
        "line_offset": 0,
        "show_confidence_viz": "false",
        "tags": []
    }
    response = session.post(url, json=data)
    response.raise_for_status()
    return response


def upload_images(session, doc, collection, nid, files):
    doc_pk = doc.json()['pk']
    url = urljoin(base_url, f'api/documents/{doc_pk}/parts/')
    for f in files:
        # rewrite file to match expected output
        file_name = f.split('/')[-1]
        if file_name.endswith('jp2'):
            file_name = file_name.replace('jp2', 'jpg')
        elif file_name.endswith('tiff'):
            file_name = file_name.replace('tiff', 'jpg')
        else:
            file_name = file_name.replace('tif', 'jpg')
        data = {
            "name": "",
            "typology": None,
            "source": ""
        }
        file_path = f'U:\\htr_revcity\\image_files\\{collection}\\{nid}\\{file_name}'
        response = session.post(url, json=data, files={'image': open(file_path, 'rb')})
        response.raise_for_status()


def dump_collection(project_name, docs, collection, files):
    session = connect_escr(headers)
    create_project(session, project_name)
    for d in docs:
        nid = d['nid']
        manu = files[nid]
        r = create_document(session, d['title'], project_name)
        r.raise_for_status()
        click.echo(f'Created document {nid}.')
        upload_images(session, r, collection, nid, manu)
