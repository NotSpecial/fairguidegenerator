"""Get data from AMIV CRM."""

from amivcrm import AMIVCRM

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
            'our_industries11_c'
        ]

        result = self.getentry(
            module_name="Accounts",
            query="accounts.id = '%s'" % company_id,
            order_by="accounts.name",
            select_fields=fields)

        if result is not None:
            def _parse_list(raw):
                """CRM Format is ^something^,^otherthing^,.."""
                return [item[1:-1] for item in raw.split(",")]

            parsed = {
                'id': result['id'],

                'booth': result['standplatz11_c'],
                'interested_in': _parse_list(result['interest_subject11_c']),

                'name': result['name'],
                'website': result['website'],

                'contact': result['study_contact11_c'],

                'employees_ch': result['employees_ch11_c'],
                'employees_world': result['employees_world11_c'],

                'offering': _parse_list(result['job_offer11_c']),

                'about': result['about_us11_c'],
                'focus': result['our_industries11_c']
            }

            return parsed
