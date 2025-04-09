# -*- coding: utf-8 -*-


import druped
from dotenv import load_dotenv
import os
import click
import csv


load_dotenv()

rev_username = str(os.getenv('REVCITY_USERNAME'))
rev_password = str(os.getenv('REVCITY_PASSWORD'))


@click.command()
@click.argument('nid', nargs=-1)
def cli(nid: tuple[str, ...]):
    host = 'https://therevolutionarycity.org'
    auth = (rev_username, rev_password)
    s = druped.connect_drupal(auth)
    node_ids = []
    file_paths = []
    for n in nid:
        meta = druped.fetch_child_nids(s, host, n)
        meta = sorted(meta, key=lambda x: int(x['field_weight_value']))
        nid = [n['nid'] for n in meta]
        node_ids = node_ids + nid
        files = druped.fetch_file_paths(s, host, meta)
        for file in files:
            file_name = file.rsplit('/', 1)[-1]
            file_name = file_name.replace('.jp2', '')
            file_name = file_name.replace('.tiff', '')
            file_name = file_name.replace('.tif', '')
            file_name = 'hocr/' + file_name + '.xml'
            file_paths.append(file_name)
        click.echo(f'Processed {n}.')

    with open('wb_output.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['media_id', 'file', 'field_media_use'])
        for i, j in zip(node_ids, file_paths):
            writer.writerow([i, j, '1453'])
    click.echo('Done!')


if __name__ == '__main__':
    cli()
