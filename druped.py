# -*- coding: utf-8 -*-


import requests
from PIL import Image
import time
import io
import os
import click
import csv

REV_CITY = 'https://therevolutionarycity.org'
DIG_LIB = 'https://diglib.amphilsoc.org'


def connect_drupal(auth):
    s = requests.session()
    s.auth = auth
    return s


def get_metadata(session, nid, host):
    '''Return NID and title for all items in collection'''
    url = f'{host}/metadata-export-api/'
    json_request = session.get(url + str(nid))
    json_request.raise_for_status()
    metadata = json_request.json()
    output = [{'nid': m['nid'], 'title': m['title']} for m in metadata]
    return output


def fetch_child_nids(session, host, nid):
    '''Return NID, title and MID for all pages in book object'''
    url = f'{host}/show-children-api/'
    request = session.get(url + str(nid))
    request.raise_for_status()
    data = request.json()
    if len(data) == 0:
        raise ValueError("Invalid NID")
    else:
        return data


def fetch_file_paths(session, host, data):
    '''Return list of media URLs in page order for book object'''
    output = []
    url = f'{host}/media/'
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


def download_collection(nid, auth, path, host):
    if host == 'diglib':
        host = DIG_LIB
    elif host == 'revcity':
        host = REV_CITY
    else:
        raise ValueError('Unknown host.')
    base_path = 'U:\\htr_revcity\\image_files'
    path = os.path.join(base_path, path)
    if not os.path.isdir(path):
        os.makedirs(path)
    session = connect_drupal(auth)
    collection_metadata = get_metadata(session, str(nid), host)
    output_files = {}
    for book in collection_metadata:
        book_data = fetch_child_nids(session, host, book['nid'])
        files = fetch_file_paths(session, host, book_data)
        output_files.update({book['nid']: files})
        download_book(session, files, os.path.join(path, book['nid']))
        click.echo(f'Downloaded {book["nid"]}.')
    return collection_metadata, output_files


def get_file_metadata(s, host, nid):
    children = fetch_child_nids(s, host, nid)
    file_paths = fetch_file_paths(s, host, children)
    sorted_children = sorted(children, key=lambda x: int(x['field_weight_value']))
    result = []
    for i, j in zip(sorted_children, file_paths):
        r = [nid, i['nid'], i['mid'], j]
        result.append(r)
    print(f'Processed {nid}.')
    return result


def generate_file_csv(nids, auth, host, output_file):
    s = connect_drupal(auth)
    payload = []
    for nid in nids:
        print(nid)
        result = get_file_metadata(s, host, nid)
        payload = payload + result
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['parent_nid', 'nid', 'mid', 'file'])
        for row in payload:
            writer.writerow(row)


def get_hocr_files(session, nids, host):
    '''For an object that already has hOCR files in Drupal, get the media ID'''
    # TODO: test behavior when not all pages have hOCR files
    url = f'{host}/show-hocr-api'
    payload = []
    for nid in nids:
        request = session.get(url + str(nid))
        request.raise_for_status()
        data = request.json()
        payload.append(data)

    return payload
