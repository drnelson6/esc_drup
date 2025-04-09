import click
import druped
import escnt
from dotenv import load_dotenv
import os

load_dotenv()

rev_username = str(os.getenv('REVCITY_USERNAME'))
rev_password = str(os.getenv('REVCITY_PASSWORD'))
dig_username = str(os.getenv('DIGLIB_USERNAME'))
dig_password = str(os.getenv('DIGLIB_PASSWORD'))
api_key = str(os.getenv('ESCRIPT_API'))


@click.command()
@click.option('-h', '--host', default='revcity')
@click.argument('nid')
@click.argument('path')
@click.argument('project_name')
def xfer_collection(nid, host, path, project_name):
    click.echo('Downloading the collection...')
    if host == 'diglib':
        username = dig_username
        password = dig_password
    elif host == 'revcity':
        username = rev_username
        password = rev_password
    auth = (username, password)
    meta, out = druped.download_collection(nid, auth, path, host)
    click.echo('Collection downloaded.')
    click.echo('Uploading collection...')
    escnt.dump_collection(project_name, meta, path, out)
    click.echo('Success.')


if __name__ == '__main__':
    xfer_collection()
