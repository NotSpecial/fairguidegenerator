"""Get data from AMIV CRM."""
from os import path, makedirs
import requests
from flask import current_app
from amivcrm import AMIVCRM


LOGO_URL = 'http://www.kontakt.amiv.ethz.ch/data/company-logos/2016/'
AD_URL = 'http://www.kontakt.amiv.ethz.ch/data/company-inserat/'


def _download(url, filename):
    """Download image, return path to file (or None if not found.)"""
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        directory = current_app.config['STORAGE_DIR']
        makedirs(directory, exist_ok=True)
        filepath = path.join(directory, filename)

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

            # Try to retrieve Logo (None if nothing found)
            parsed['logo'] = (
                _download(LOGO_URL + key + '.png', 'logo_%s.png' % key) or
                _download(LOGO_URL + key + '.jpeg', 'logo_%s.jpeg' % key)
            )

            # If media, try to retrieve advertisement as well
            # Note: for pdfs, it seems important to include the file ending
            parsed['media'] = (result['mediapaket_c'] == "mediaPaket")
            if parsed['media']:
                parsed['ad'] = _download(AD_URL + key + '.pdf',
                                         'ad_%s.pdf' %key)

            return parsed
