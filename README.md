# Fairguidegenerator

A tool to create AMIV Kontakt fairguide pages for companies.

## Deployment with Docker

When cloning the repository, don't forget the `--recursive` option to include
the amivtex submodule

```bash
git clone --recursive https://github.com/NotSpecial/fairguidegenerator.git
# If you have already cloned the repo, use this command to get the submodule:
git submodule update --init --recursive
```

A `Dockerfile` is available, but two things are needed before it can be built:

1. You have to get the DINPro font (it is not free, but available for ETH
   members) and place it next to the Dockerfile. Name the folder `DINPro`.
2. Also next to the Dockerfile, create a config file named `config.py` with the
   following content:

   ```python
   SOAP_USERNAME = 'username for amiv crm soap'
   SOAP_PASSWORD = 'and the password'
   ```

   You can find the credentials in the
   [AMIV Wiki](https://intern.amiv.ethz.ch/wiki/SugarCRM#SOAP).

If thats done, you can build and run the container:

```bash
docker build -t fairguidegenerator .
# Run on port 9876 (choose whatever you like)
docker run -p 9876:80 fairguidegenerator
```

Done!

## Development

For compilation of the tex files,
[amivtex](https://github.com/NotSpecial/amivtex) needs to be installed along
with the DINPro fonts as well. Take a look the repository for instructions.

You need Python 3. The following commands create a virtual environment and
install dependencies:

```bash
# (If not yet done: clone and go into folder)
git clone https://github.com/NotSpecial/fairguidegenerator
cd fairguidegenerator

# Create and activate env
python -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
export FLASK_APP=app.py
export FLASK_DEBUG=1
flask run
```

Now you should be set up for development.
