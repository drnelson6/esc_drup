# -*- coding: utf-8 -*-

from core import druped
from core import escnt
import csv
import os
from dotenv import load_dotenv
import click


def load_csv(path):
    """Returns CSV data as list of dictionaries"""
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        rows = [r for r in csv_reader][1:]

    return rows


load_dotenv()
username = str(os.getenv('REVCITY_USERNAME'))
password = str(os.getenv('REVCITY_PASSWORD'))
api_key = str(os.getenv('ESCRIPT_API'))
auth = (username, password)
headers = {'Accept': 'application/json', 'Authorization': f'Token {api_key}'}
host = 'https://therevolutionarycity.org'

drupe_sess = druped.connect_drupal(auth)
esc_sess = escnt.connect_escr(headers)

data = load_csv('ed-workshops-uploads.csv')

for row in data:
    nid = row[0]
    title = row[1]
    collection = row[2]
    collection_folder = row[3]
    book_data = druped.fetch_child_nids(drupe_sess, host, nid)
    files = druped.fetch_file_paths(drupe_sess, host, book_data)
    path = f'U:\\htr_revcity\\image_files\\{collection_folder}\\{nid}'
    druped.download_book(drupe_sess, files, path)
    r = escnt.create_document(esc_sess, title, collection)
    escnt.upload_images(esc_sess, r, collection_folder, nid, files)
    click.echo(f'Successfully imported {nid}.')
