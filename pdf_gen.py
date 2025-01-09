import os
from dotenv import load_dotenv
import csv
from slugify import slugify
import click

import druped

load_dotenv()
username = str(os.getenv('REVCITY_USERNAME'))
password = str(os.getenv('REVCITY_PASSWORD'))


def load_csv(path):
    """Returns CSV data as list of dictionaries"""
    rows = []
    with open(path, 'r') as f:
        csv_reader = csv.reader(f)
        rows = [r for r in csv_reader][1:]

    return rows


def generate_pdf(s, nid, title):
    data = druped.fetch_child_nids(s, nid)
    output = druped.fetch_file_paths(s, data)
    images = []
    for o in output:
        img = druped.load_image(o)
        images.append(img)
    slug = slugify(title)
    pdf_path = f'{slug}.pdf'
    images[0].save(pdf_path, "PDF", resolution=100.0, save_all=True, append_images=images[1:])
    print(f'Generated pdf for {nid}.')


def batch_gen_pdfs(s, nids, titles):
    for n, t in zip(nids, titles):
        generate_pdf(s, n, t)


@click.command()
@click.argument('filename', type=click.Path(exists=True))
def cli(filename):
    data = load_csv(filename)
    nids = [d[0] for d in data]
    titles = [d[1] for d in data]
    s = druped.connect_revcity((username, password))
    batch_gen_pdfs(s, nids, titles)


if __name__ == '__main__':
    cli()
