# -*- coding: utf-8 -*-


import requests
from PIL import Image
import time
import io
import os
import click


def connect_revcity(auth):
    s = requests.session()
    s.auth = auth
    return s


def get_metadata(session, nid):
    '''Return NID and title for all items in collection'''
    url = 'https://therevolutionarycity.org/metadata-export-api/'
    json_request = session.get(url + str(nid))
    json_request.raise_for_status()
    metadata = json_request.json()
    output = [{'nid': m['nid'], 'title': m['title']} for m in metadata]
    return output


def fetch_child_nids(session, nid):
    '''Return NID, title and MID for all pages in book object'''
    url = 'https://therevolutionarycity.org/show-children-api/'
    request = session.get(url + str(nid))
    request.raise_for_status()
    data = request.json()
    if len(data) == 0:
        raise ValueError("Invalid NID")
    else:
        return data


def fetch_file_paths(session, data):
    '''Return list of media URLs in page order for book object'''
    output = []
    url = 'https://therevolutionarycity.org/media/'
    sorted_data = sorted(data, key=lambda x: int(x['field_weight_value']))
    for i in sorted_data:
        mid = i['mid']
        request = session.get(url + mid + '?_format=json').json()
        file = request['field_media_file'][0]['url']
        output.append(file)
    return output


def load_image(url):
    request = requests.get(url, stream=True)
    request.raise_for_status()
    image_data = Image.open(io.BytesIO(request.content))
    time.sleep(1)
    return image_data


def save_image(image, path):
    with open(path, 'w') as f:
        image.save(f)


def download_book(session, data, path):
    '''Download all images in a book object'''
    if not os.path.isdir(path):
        os.makedirs(path)
    for f in data:
        file_name = f.rsplit('/', 1)[-1]
        file_name = file_name.replace('.jp2', '')
        file_name = file_name.replace('.tiff', '')
        file_name = file_name.replace('.tif', '')
        image_data = load_image(f)
        save_image(image_data, os.path.join(path, file_name + '.jpg'))


def download_collection(nid, auth, path):
    base_path = 'U:\\htr_revcity\\image_files'
    path = os.path.join(base_path, path)
    if not os.path.isdir(path):
        os.makedirs(path)
    session = connect_revcity(auth)
    collection_metadata = get_metadata(session, str(nid))
    output_files = {}
    for book in collection_metadata:
        book_data = fetch_child_nids(session, book['nid'])
        files = fetch_file_paths(session, book_data)
        output_files.update({book['nid']: files})
        download_book(session, files, os.path.join(path, book['nid']))
        click.echo(f'Downloaded {book["nid"]}.')
    return collection_metadata, output_files
