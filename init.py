"""Setup script."""

import os
from hashlib import md5
from ruamel import yaml
import click

# Find the directory where the script is placed
app_root = os.path.dirname(os.path.realpath(__file__))


@click.command()
@click.option('--soappass',
              prompt="Enter the soap password (plain, NOT md5 hashed)")
def init(soappass):
    """Create user config and directories needed.

    Args:
        soappass (str): Password for soap login
    """
    config = {
        'SOAP_PASSWORD': md5(soappass.encode('UTF-8')).hexdigest(),
    }

    config_file = os.path.join(app_root, 'config.yml')

    with open(config_file, 'w') as f:
        # setting default_flow_style to False will make the file more readable
        yaml.dump(config, f, default_flow_style=False)

if __name__ == '__main__':
    init()
