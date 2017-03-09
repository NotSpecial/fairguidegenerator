# -*- coding: utf-8 -*-

"""The app."""

from os import path
from ruamel import yaml

from flask import (Flask, send_file, url_for)

from fairguidegenerator.tex import render_tex
from fairguidegenerator.soapclient import CRMImporter

# Find the directory where the script is placed
root_dir = path.dirname(path.realpath(__file__))

app = Flask('fairguidegenerator')
app.config.from_object('fairguidegenerator.settings')

# Load User config
try:
    with open('config.yml', 'r') as f:
        app.config.from_mapping(yaml.load(f))
except:
    raise Exception("No config found! Use `python init.py` to create.")

# Get CRM connection
CRM = CRMImporter(app)


# Routes

@app.route('/')
def main():
    """Main view.

    Includes output format and yearly settings.
    """
    def link(item):
        return "<a href=%s>%s</a>" % (url_for('companypage', id=item[1]),
                                      item[0])

    return "<br>".join([link(item) for item in CRM.get_companies().items()])


@app.route('/<id>')
def companypage(id):
    """Return the rendered page for a single company."""
    companydata = CRM.get_company_data(id)
    filename = render_tex(app.config['STORAGE_DIR'], **companydata)
    return send_file(filename)
