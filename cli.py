import click
import druped
import escnt
from dotenv import load_dotenv
import os

load_dotenv()

username = str(os.getenv('REVCITY_USERNAME'))
password = str(os.getenv('REVCITY_PASSWORD'))
auth = (username, password)
api_key = str(os.getenv('ESCRIPT_API'))

@click.command()
@click.argument('nid')
@click.argument('path')
@click.argument('project_name')
def xfer_collection(nid, path, project_name):
    click.echo('Downloading the collection...')
    meta, out = druped.download_collection(nid, auth, path)
    click.echo('Collection downloaded.')
    click.echo('Uploading collection...')
    escnt.dump_collection(project_name, meta, path, out)
    click.echo('Success.')


if __name__ == '__main__':
    xfer_collection()