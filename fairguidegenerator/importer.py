"""Get data from AMIV CRM."""
from os import path, makedirs
from io import BytesIO
from PIL import Image
import requests
from flask import current_app
from amivcrm import AMIVCRM

# Download URLs
LOGO_URL = 'http://www.kontakt.amiv.ethz.ch/data/company-logos/2016'
AD_URL = 'http://www.kontakt.amiv.ethz.ch/data/company-inserat'

# Paths to placeholder logo/ad
BASEPATH = path.join(path.dirname(path.abspath(__file__)), 'tex_templates')
LOGO_MISSING = path.join(BASEPATH, 'logo_missing.png')
AD_MISSING = path.join(BASEPATH, 'ad_missing.png')
AD_AD = path.join(BASEPATH, 'ad_ad.png')


def _download(base_url, company_name, extension):
    """Download Logo or Ad.

    PNGs are converted and saved with pillow to ensure
    that all metadata is present, since TeX relies on this.
    (And sometimes the files on the server don't include it)

    PDFS are directly saved to disk.
    """
    assert extension in ('png', 'pdf')
    url = '%s/%s.%s' % (base_url, company_name, extension)
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        # Prepare directory
        directory = current_app.config['STORAGE_DIR']
        makedirs(directory, exist_ok=True)

        if extension == 'png':
            filepath = path.join(directory, 'logo_%s.png' % company_name)
            logo = Image.open(BytesIO(response.content))
            # We need to ensure the color-space used is supported by png
            logo.convert('RGBA').save(filepath)
        else:
            filepath = path.join(directory, 'ad_%s.pdf' % company_name)
            with open(filepath, 'wb') as file:
                for chunk in response:
                    file.write(chunk)

        return filepath


class Importer(AMIVCRM):
    """Wrapper around CRM class to provide some data parsing."""

    def get_companies(self):
        """Get a list of companies.

        Returns:
            (dict): Company name as key, ID as value
        """
        response = self.get(
            module_name="Accounts",
            query="accounts_cstm.messeteilnahme_c = 1",
            order_by="accounts.name",
            select_fields=['name', 'id'])

        return {item['name']: item['id'] for item in response}

    def get_company(self, company_id):
        """Get and parse data from AMIV CRM for a single company.

        Also try to download image and logo

        Args:
            id (str): The id of the company

        Returns:
            dict: Company data, None if nothing found
        """
        # Required fields
        fields = [
            'id',

            # Booth and fields of interest
            'standplatz11_c',
            'interest_subject11_c',

            # Sidebar
            'name',
            'website',

            'study_contact11_c',

            'employees_ch11_c',
            'employees_world11_c',

            'job_offer11_c',

            # Text
            'about_us11_c',
            'our_industries11_c',

            # Media packet: Do they have an ad?,
            'mediapaket_c',
        ]

        result = self.getentry("Accounts", company_id, select_fields=fields)

        if result is not None:
            def _parse_list(raw):
                """CRM Format is ^something^,^otherthing^,.."""
                if raw is None:
                    return ""
                return [item[1:-1] for item in raw.split(",")]

            parsed = {
                'id': result['id'],

                'booth': result['standplatz11_c'],
                'interested_in': _parse_list(result['interest_subject11_c']),

                'name': result['name'],
                'website': result['website'],

                'contact': result['study_contact11_c'],

                'offering': _parse_list(result['job_offer11_c']),

                'about': result['about_us11_c'],
                'focus': result['our_industries11_c']
            }
            # Employees
            swiss = result['employees_ch11_c']
            swiss = "%s in der Schweiz" % swiss if swiss else ""
            world = result['employees_world11_c']
            world = "%s weltweit" % world if world else ""

            parsed['employees'] = '\n'.join([swiss, world])

            # For Logos and Ads, we have to check the kontakt webserver.
            # They are stored with the company name (spaces replaced with _)
            key = parsed['name'].replace(' ', '_')

            # Try to retrieve Logo (path to placeholder logo if not found)
            parsed['logo'] = _download(LOGO_URL, key, 'png') or LOGO_MISSING

            # If media, try to retrieve advertisement as well
            # Note: for pdfs, it seems important to include the file ending
            parsed['media'] = (result['mediapaket_c'] == "mediaPaket")
            if parsed['media']:
                parsed['ad'] = _download(AD_URL, key, 'pdf') or AD_MISSING
            else:
                parsed['ad'] = AD_AD  # Insert placeholder promoting an ad

            return parsed
