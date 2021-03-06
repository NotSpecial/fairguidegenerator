"""Get data from AMIV CRM."""
from os import path, makedirs
from io import BytesIO
import re
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


def _processed(logo):
    """Remove transparencies because they sometimes cause problems.

    Also re-scale the image if it is more then 2048px wide or high, since
    Latex is not very good at this and produces ugly results.
    """
    converted = logo.convert('RGBA')

    # Rescale if needed
    MAX_SIZE = 2048
    size = converted.size

    def _keep_ratio(a, b):
        return int(round((MAX_SIZE/float(a)) * b))

    if max(size) > MAX_SIZE:
        if size[0] > size[1]:
            new_width = MAX_SIZE
            new_height = _keep_ratio(size[0], size[1])
        else:
            new_height = MAX_SIZE
            new_width = _keep_ratio(size[1], size[0])

        converted = converted.resize((new_width, new_height))

    # Remove Transparencies
    white_back = Image.new('RGB', converted.size, (255, 255, 255))
    white_back.paste(converted, mask=converted.split()[-1])
    return white_back


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
            _processed(logo).save(filepath)
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

            def _parse_offering(raw):
                """Split offers in three blocks (fulltime, entry, thesis)"""
                # Remove the 'arbeiten' part from Semesterarbeiten etc.
                all_offers = _parse_list(raw)

                offers = {}
                if 'Festanstellungen' in all_offers:
                    offers['fulltime'] = 'Festanstellungen'

                entry_offers = [item for item in all_offers
                                if item in ['Praktika', 'TraineeProgramm']]
                if entry_offers:
                    offers['entry'] = '\n'.join(entry_offers)

                thesis_offers = list(
                    item for item in ['Semester', 'Bachelor', 'Master']
                    if "%sarbeiten" % item in all_offers
                )
                # If more then one item, put last on newline
                if len(thesis_offers) > 1:
                    thesis_offers[-1] = "\n%s" % thesis_offers[-1]

                # Join them with kommas and write 'arbeiten' after the last one
                if thesis_offers:
                    offers['thesis'] = "%sarbeiten" % ', '.join(thesis_offers)

                return offers

            parsed = {
                'id': result['id'],

                'booth': result['standplatz11_c'],
                'interested_in': _parse_list(result['interest_subject11_c']),

                'name': result['name'],
                'website': result['website'],

                'contact': result['study_contact11_c'],

                'offers': _parse_offering(result['job_offer11_c']),

                'about': result['about_us11_c'],
                'focus': result['our_industries11_c']
            }

            # Employees
            def _parse_employees(key, suffix):
                num = re.sub("\D", "", str(result[key]))  # Only numbers
                # Add comma separators for thousands
                if num:
                    return "{:,} Mitarbeiter {}".format(int(num), suffix)

            swiss = _parse_employees('employees_ch11_c', 'in der Schweiz')
            world = _parse_employees('employees_world11_c', 'weltweit')
            parsed['employees'] = '\n'.join(filter(None, [swiss, world]))

            # For Logos and Ads, we have to check the kontakt webserver.
            # They are stored with the company name (spaces replaced with _)
            key = parsed['name'].replace(' ', '_')

            # Try to retrieve Logo (path to placeholder logo if not found)
            parsed['logo'] = _download(LOGO_URL, key, 'png') or LOGO_MISSING

            # If media, try to retrieve advertisement as well
            parsed['media'] = (result['mediapaket_c'] == "mediaPaket")
            if parsed['media']:
                parsed['ad'] = _download(AD_URL, key, 'pdf') or AD_MISSING
            else:
                parsed['ad'] = AD_AD  # Insert placeholder promoting an ad

            return parsed
