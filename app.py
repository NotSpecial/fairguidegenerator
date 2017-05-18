# -*- coding: utf-8 -*-
# pylint: disable=locally-disabled, invalid-name

"""The app."""
from io import BytesIO
from flask import (Flask, send_file, url_for, abort)

from fairguidegenerator.tex import render_tex
from fairguidegenerator.importer import Importer


app = Flask('fairguidegenerator')
app.config.from_object('config')
# If STORAGE_DIR has not been defined, use '.cache' in current working dir
app.config.setdefault('STORAGE_DIR', './.cache')


# Get CRM connection
CRM = Importer(app.config['SOAP_USERNAME'], app.config['SOAP_PASSWORD'])


# Routes
@app.route('/')
def main():
    """Main view. Show links to companies."""
    def _link(item):
        url = url_for('companypage', company_id=item[1])
        return "<a href=%s>%s</a>" % (url, item[0])

    # Super simple demo
    companies = CRM.get_companies()
    return "<br>".join(_link(item) for item in companies.items())


@app.route('/<company_id>')
def companypage(company_id):
    """Return the rendered page for a single company."""
    # Get Data
    companydata = CRM.get_company(company_id)
    if companydata is None:
        abort(404)

    # Compile
    compiled = render_tex([companydata])

    # Specify mimetype so browsers open it in preview
    return send_file(BytesIO(compiled), mimetype='application/pdf')


@app.route('/all')
def all_companies():
    """Create all pages."""
    companies = (CRM.get_company(_id)
                 for _id in CRM.get_companies().values())

    compiled = render_tex(companies)
    return send_file(BytesIO(compiled), mimetype='application/pdf')
