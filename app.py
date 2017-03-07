# -*- coding: utf-8 -*-

"""The app."""

from os import path
from ruamel import yaml

from flask import (Flask, render_template, send_file, redirect, url_for,
                   session, request)

# from fairguidegenerator.tex import render_tex
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
    return str(CRM.get_company_data(id))


'''
@app.route('/contracts')
@app.route('/contracts/<int:id>')
@protected
def send_contracts(id=None):
    """Contract creation."""
    if id is None:
        selection = CRM.data
    else:
        selection = [CRM.data[id]]

    # Get output format, mail is default
    output = session.get("output_format", "mail")

    # Check if only tex is requested
    return_tex = (output == "tex")

    # Check if output format is email -> only single contract
    contract_only = (output == "email")

    # Get yearly settings
    yearly = load_yearly_settings()

    filepath = render_tex(
        # Data
        letterdata=selection,

        # Yearly settings
        fairtitle=yearly['fairtitle'],
        president=yearly['president'],
        sender=yearly['sender'],
        days=yearly['days'],
        prices=yearly['prices'],

        # Output options
        contract_only=contract_only,
        return_tex=return_tex,

        # Tex source (in git submodule) and storage (from config)
        texpath=path.join(root_dir, 'amivtex'),
        output_dir=app.config['STORAGE_DIR']
    )

    return send_file(filepath, as_attachment=True)
'''
