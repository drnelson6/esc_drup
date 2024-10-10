import esout
import json
import requests
from bs4 import BeautifulSoup
import math
import os
from dotenv import load_dotenv
from time import sleep
import zipfile
import shutil
import click


load_dotenv()
api_key = str(os.getenv('ESCRIPT_API'))
base_url = 'https://transcription.amphilsoc.org'

headers = {'Accept': 'application/json', 'Authorization': f'Token {api_key}'}

# spoof user-agent by following answer two here
# https://stackoverflow.com/questions/23102833/how-to-scrape-a-website-which-requires-login-using-python-and-beautifulsoup
# Credentials must be periodically updated

def download_zips(num):
    with open('credentials.json', 'r') as f:
        creds = json.load(f)

    cookies = creds['cookies']
    headers = creds['headers']

    headers.pop('cookie')

    url = 'https://transcription.amphilsoc.org/profile/files/'

    pages = math.ceil(num / 25)

    remainder = num % 25
    for p in range(pages):
        if p != 0:
            params = {'page': p + 1}
            response = requests.get(url, cookies=cookies, headers=headers, params=params)
        else:
            response = requests.get(url, cookies=cookies, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.select('#infos-tab > a')
        cleaned_links = [link['href'] for link in links]

        # then download each link and write content to file
        if p == range(pages)[-1]:
            cleaned_links = cleaned_links[0:remainder]
        for link in cleaned_links:
            r = requests.get(link)
            # need to assign filenames
            filename = 'xml_output/' + link.split('/')[-1]
            with open(filename, 'wb') as f:
                f.write(r.content)
            print(f'Downloading {filename}...')


def get_canonical_transcriptions(document):
    parts = document.parts
    part_dict = {}
    for part in parts:
        if part.exclude is False:
            part_pk = part.pk
            transcriptions = part.transcriptions
            for t in transcriptions:
                if t.is_canonical is True:
                    if t.pk in part_dict:
                        part_dict[t.pk].append(part_pk)
                    else:
                        part_dict.update({t.pk: [part_pk]})

    return part_dict


def get_valid_regions(doc_pk):
    url = f'https://transcription.amphilsoc.org/api/documents/{doc_pk}/'
    r = requests.get(url, headers=headers)
    regions = [i['pk'] for i in r.json()['valid_block_types']]
    return regions


def generate_zip_exports(doc_pk, part_dict, include_images=False):
    url = f'https://transcription.amphilsoc.org/api/documents/{doc_pk}/export/'
    regions = get_valid_regions(doc_pk) + ['Undefined', 'Orphan']
    n = len(part_dict.keys())
    for i in part_dict.keys():
        payload = {
            'file_format': 'alto',
            'parts': part_dict[i],
            'transcription': i,
            'include_images': include_images,
            'region_types': regions
        }
        r = requests.post(url, data=payload, headers=headers)
        r.raise_for_status()
        # exports named after time of export to the minute, so need to wait one minute
        if n > 1:
            sleep(60)
    
    return n


def check_export_status():
    url = 'https://transcription.amphilsoc.org/api/tasks/'
    r = requests.get(url, headers=headers)
    r.raise_for_status
    results = r.json()['results']
    if results[0]['done_at'] == None:
        return False
    else:
        return True


def generate_exports(include_images=False):
    n = 0
    projects = esout.load_json('data.json')
    for project in projects:
        documents = project.documents
        for doc in documents:
            doc_pk = doc.pk
            parts = get_canonical_transcriptions(doc)
            if parts:
                out = generate_zip_exports(doc_pk, parts, include_images=include_images)
                print(f'Generating export for {doc.name}...')
                n = n + out
    
    print(f'Generated {n} exports.')
    status = False
    while status is False:
        status = check_export_status()
        sleep(5)
    download_zips(n)

def unzip_downloads(base_dir, files):
    dest_dir = os.path.join(base_dir, 'unzipped')
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    for file in files:
        dest_name = file.replace('.zip', '')
        with zipfile.ZipFile(os.path.join(base_dir, file), 'r') as f:
            f.extractall(os.path.join(dest_dir, dest_name))
            print(f'Extracting {file}...')


def remove_zips(base_dir, files):
    for file in files:
        if file.endswith('.zip'):
            os.remove(os.path.join(base_dir, file))
    print('Zip files deleted.')


def move_xml_files(input_dir):
    files = os.walk(input_dir)
    dest_dir = '../data'
    for direc, _, paths in files:
        if len(paths) == 0:
            continue
        for p in paths:
            if p == 'METS.xml':
                os.remove(os.path.join(direc, p))
                continue
            source_path = os.path.join(direc, p)
            dest_path = os.path.join(dest_dir, p)
            shutil.move(source_path, dest_path)
        os.rmdir(direc)


def process_zips():
    base_dir = 'xml_output'
    files = [f for f in os.listdir(base_dir) if f.endswith('.zip')]
    print(f'Total files to process: {len(files)}')
    unzip_downloads(base_dir, files)
    remove_zips(base_dir, files)
    move_xml_files(os.path.join(base_dir, 'unzipped'))


@click.command()
@click.option('--images', is_flag=True)
def cli(images):
    if images:
        generate_exports(include_images=True)
    else:
        generate_exports()
    process_zips()


if __name__ == '__main__':
    cli()
