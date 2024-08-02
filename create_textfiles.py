# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 11:10:03 2024

@author: dnelson
"""

from bs4 import BeautifulSoup
import os


def extract_lines(soup):
    lines = []
    xml_lines = soup.find_all('String')
    for line in xml_lines:
        cleaned_line = line.get('CONTENT')
        lines.append(cleaned_line)
    return lines


def parse_xml(file_path):
    with open(file_path) as f:
        soup = BeautifulSoup(f, 'lxml-xml')
    return soup


def get_xml_files(direc):
    dirs = os.listdir(direc)
    transcriptions = {}
    for d in dirs:
        xml_files = [f for f in os.listdir(os.path.join(direc, d)) if f.endswith('xml')]
        if len(xml_files) > 0:
            transcriptions.update({d: xml_files})
    return transcriptions


def generate_plain_transcriptions(direc):
    transcriptions = get_xml_files(direc)
    texts = {}
    for i in transcriptions.keys():
        files = transcriptions[i]
        for f in files:
            file_name = f.replace('.xml', '')
            soup = parse_xml(os.path.join(direc, i, f))
            lines = extract_lines(soup)
            texts.update({file_name: lines})
    return(texts)


def write_textfiles(transcriptions, direc):
    for i in transcriptions.keys():
        path = os.path.join(direc, f'{i}.txt')
        with open(path, 'w') as f:
            lines = map(lambda x: x + '\n', transcriptions[i])
            f.writelines(lines)

def cli():
    source_dir = 'U:/htr_revcity/image_files'
    target_dir = 'U:/htr_revcity/textfiles'
    transcriptions = generate_plain_transcriptions(source_dir)
    write_textfiles(transcriptions, target_dir)

if __name__ == '__main__':
    cli()
