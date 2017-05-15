# -*- coding: utf-8 -*-
# pylint: disable=locally-disabled, invalid-name

"""The app."""
from flask import (Flask, send_file, url_for, abort)

from fairguidegenerator.tex import render_tex
from fairguidegenerator.importer import Importer

app = Flask('fairguidegenerator')
app.config.from_object('config')

# Get CRM connection
CRM = Importer(app.config['SOAP_USERNAME'], app.config['SOAP_PASSWORD'])

# Routes
@app.route('/')
def main():
    """Main view.

    Includes output format and yearly settings.
    """
    def _link(item):
        url = url_for('companypage', company_id=item[1])
        return "<a href=%s>%s</a>" % (url, item[0])

    # Super simple demo
    return "<br>".join(_link(item) for item in CRM.get_companies().items())


@app.route('/<company_id>')
def companypage(company_id):
    """Return the rendered page for a single company."""
    companydata = CRM.get_company(company_id)
    if companydata is None:
        abort(404)
    filename = render_tex([companydata], app.config['STORAGE_DIR'])
    return send_file(filename)

@app.route('/all')
def all_companies():
    """Create all pages."""
    companies = (CRM.get_company(_id)
                 for _id in CRM.get_companies().values())

    filename = render_tex(companies, app.config['STORAGE_DIR'])
    return send_file(filename)
