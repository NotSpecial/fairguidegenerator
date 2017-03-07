# -*- coding: utf-8 -*-

"""Provide a connector to the AMIV sugarcrm.

sugarcrm provides a SOAP and a REST api. At the time this tool was written
the REST api was unfortunately not available. Therefore SOAP is used.

The python library suds is used, more exactly the fork by (jurko)
[https://bitbucket.org/jurko/suds].

Information for the AMIV side can be found in the (wiki)
[intern.amiv.ethz.ch/wiki/SugarCRM#SOAP]. Although written for php the
procedures can be copied without to much trouble.


This file provides two classes, the first being a more generic wrapper for the
amiv crm soap, the second being basically a wrapper around the first tailored
to the contractor flask app.

If you want to write your own python app using crm, you'll be all set copying
the first class. Should it be used a lot it might be worth considering to move
the connector to it's own project.

In the wiki you will notice that the password in php is `md5('somestring')`.
To get the python equivalent of this, you need:

```
from hashlib import md5
password = md5(b'somestring').hexdigest()

```
Note: This is python 3.5. In earlier versions the import is different.
    Furthermore notice that md5 requires the string as binary, so don't
    forget the `b` prefix.x
"""

from suds.client import Client
from contextlib import contextmanager
import html


class AMIVCRMConnector(object):
    """The connector class.

    If you want to implement your own app you can just copy this class.
    In the (wiki)[intern.amiv.ethz.ch/wiki/SugarCRM#SOAP] you will find the
    url, appname, username and password.

    You can use the session context to easily manage the connection.

    Example usage:

    ```
    crm = AMIVCRMConnector(...)
    with crm.session():
        crm.get_full_entry_list(...)
    ```

    Args:
        url (str): CRM url
        appname (str): the soap appname
        username (str): the soap username
        password (str): the soap password
    """

    def __init__(self, url, appname, username, password):
        """Init."""
        self.client = Client(url)
        self.session_id = None
        self.appname = appname
        self.username = username
        self.password = password

    def login(self):
        """Login.

        Args:
            username (str): sugarcrm soap username
            password (str): sugarcrm soap password, md5 hashed
        """
        auth = {'user_name': self.username,
                'password': self.password}

        self.session_id = self.client.service.login(auth, self.appname).id

    def check_session(self):
        """Raise exception if session is missing."""
        if self.session_id is None:
            raise RuntimeError("No session, you need to log in!")

    def logout(self):
        """Logout."""
        self.check_session()

        self.client.service.logout(self.session_id)
        self.session_id = None

    @contextmanager
    def session(self):
        """Session context.

        Use in a with statement. Login will be performed on entering and
        logout on leaving the block

        Args:
            username (str): sugarcrm soap username
            password (str): sugarcrm soap password, md5 hashed
        """
        self.login()
        yield
        self.logout()

    def _safe_str(self, item):
        """Escape strings.

        First of all if its a string it is actually a suds Text class.
        In some environments this seems not to play along well with unicode.
        (Although it is a subclass of str)

        Therefore explicitly cast it to a str and unescape html chars.

        Possible improvement: Check if soap returns anything else but strings.
        If not, the if statement might be scraped.

        Args:
            item: The object to make safe. Changed only if subclass of str.
        """
        if isinstance(item, str):
            return html.unescape(str(item))
        else:
            return item

    def parse(self, response):
        """Turn results into list of dicts."""
        return ([{item.name: self._safe_str(item.value)
                for item in entry.name_value_list}
                for entry in response.entry_list])

    def get_full_entry_list(self, module_name="", query="", order_by="",
                            select_fields=[]):
        """Get list of all entries.

        Because the server ignores the 'max_results' parameter,
        we need this workaround.

        Args:
            module_name (str): crm module
            query (str): SQL query string
            order_by (str): SQL order by string
            select_fields (list): fields the crm should return

        Returns:
            list: list of dictionaries with result data
        """
        self.check_session()

        results = []

        # Collect results
        offset = 0
        while True:
            response = self.client.service.get_entry_list(
                session=self.session_id,
                module_name=module_name,
                query=query,
                order_by=order_by,
                offset=offset,
                select_fields=select_fields)
            # Check if end is reached
            if response.result_count == 0:
                break
            else:
                results += self.parse(response)
                offset = response.next_offset

        return results


class CRMImporter(object):
    """Handling connection and parsing of soap data.

    This class is specific for the kontakt contract app.

    Args:
        app (Flask): The flask object.
    """

    def __init__(self, app=None):
        """Init."""
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Init app.

        Read soap settings and get data.

        Args:
            app (Flask): The flask object.
        """
        try:
            url = app.config['SOAP_URL']
            appname = app.config['SOAP_APPNAME']
            username = app.config['SOAP_USERNAME']
            password = app.config['SOAP_PASSWORD']
        except:
            # In python 3, this will "reraise" - the old stacktrace won't
            # be lost
            raise Exception("SOAP login data missing. "
                            "Call setup.py to create.")

        self.client = AMIVCRMConnector(url, appname, username, password)

    def get_companies(self):
        """Get a list of companies."""
        with self.client.session():
            response = self.client.get_full_entry_list(
                module_name="Accounts",
                query="accounts_cstm.messeteilnahme_c = 1",
                order_by="accounts.name",
                select_fields=['name', 'id'])

        return {item['name']: item['id'] for item in response}

    def get_company_data(self, id):
        """Get the data from soap for a single company.

        Args:
            id (str): The id of the company

        Returns:
            dict: Company data
        """
        # Fields needed
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

        # Get data
        with self.client.session():
            results = self.client.get_full_entry_list(
                module_name="Accounts",
                query="accounts.id = '%s'" % id,
                order_by="accounts.name",
                select_fields=fields)

        if not results:
            raise Exception("Nothing found!")
        else:
            result = results[0]

        def parse_list(raw):
            # Format is ^something^,^otherthing^,..
            return [item[1:-1] for item in raw.split(",")]

        parsed = {
            'id': result['id'],

            'booth': result['standplatz11_c'],
            'interested_in': parse_list(result['interest_subject11_c']),

            'name': result['name'],
            'website': result['website'],

            'contact': result['study_contact11_c'],

            'employees_ch': result['employees_ch11_c'],
            'employees_world': result['employees_world11_c'],

            'offering': parse_list(result['job_offer11_c']),

            'about': result['about_us11_c'],
            'focus': result['our_industries11_c']
        }

        return parsed
