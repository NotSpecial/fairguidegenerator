# Fairguidegenerator

A tool to create AMIV Kontakt fairguide pages for companies.

## Configuration

No matter how the fairguidegenerator is run, a config file is needed,
which requires the following information:

1. For the SugarCRM connection, username and password are required.
   Both can be found in the
   [AMIV Wiki](https://intern.amiv.ethz.ch/wiki/SugarCRM#SOAP).

2. You have to get the DINPro font (it is not free, but available for ETH
   members). A direct link to download the fonts as `.tar.gz` is in the
   [AMIV Wiki](https://wiki.amiv.ethz.ch/Corporate_Design#DINPro).

Create the file, e.g. called `config.py`, and define the following variables:

```python
SOAP_USERNAME = "..."
SOAP_PASSWORD = "..."
FONT_URL = "..."
```


## Deployment with Docker

The `Docker` image can be pulled directly from docker hub,

TODO

## Development

For compilation of the tex files,
[amivtex](https://github.com/NotSpecial/amivtex) needs to be installed along
with the DINPro fonts. Take a look the repository for instructions.

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

# Set config (optional, default is 'config.py' in current working dir)
export FAIRGUIDEGENERATOR_CONFIG=...

# Run development server
export FLASK_APP=app.py
export FLASK_DEBUG=1
flask run
```
