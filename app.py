# -*- coding: utf-8 -*-
# pylint: disable=locally-disabled, invalid-name

"""The app."""
from io import BytesIO
from flask import Flask, send_file, url_for, abort, make_response

from fairguidegenerator.tex import render_tex
from fairguidegenerator.importer import Importer


app = Flask('fairguidegenerator')
app.config.from_object('config')
# If STORAGE_DIR has not been defined, use '.cache' in current working dir
app.config.setdefault('STORAGE_DIR', './.cache')


# Get CRM connection
CRM = Importer(app.config['SOAP_USERNAME'], app.config['SOAP_PASSWORD'])


def send(data):
    """Send data as file with headers to disable caching.

    We want the preview to be refreshed, so need to avoid browser caching.
    """
    response = make_response(send_file(BytesIO(data),
                                       mimetype='application/pdf',
                                       cache_timeout=0))
    response.headers['Content-Length'] = len(data)
    return response


# Routes
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
    return send(compiled)


@app.route('/list')
def list_companies():
    """Main view. Show links to companies."""
    def _link(item):
        url = url_for('companypage', company_id=item[1])
        return "<a href=%s>%s</a>" % (url, item[0])

    # Super simple demo
    companies = CRM.get_companies()
    return "<br>".join(_link(item) for item in companies.items())


@app.route('/all')
def all_companies():
    """Create all pages."""
    companies = (CRM.get_company(_id)
                 for _id in CRM.get_companies().values())

    compiled = render_tex(companies)
    return send(compiled)
