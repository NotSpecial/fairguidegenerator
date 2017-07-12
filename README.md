# Fairguidegenerator

A tool to create AMIV Kontakt fairguide pages for companies.

## Deployment with Docker

A `Dockerfile` is available, but two things are needed before it can be built:

1. For the SugarCRM connection, username and password are required.
   Both can be found in the
   [AMIV Wiki](https://intern.amiv.ethz.ch/wiki/SugarCRM#SOAP).

2. You have to get the DINPro font (it is not free, but available for ETH
   members). To ease this process, the Dockerfile takes the link to download
   the fonts as `.tar.gz`. You can find a direct link
   in the [AMIV Wiki](https://wiki.amiv.ethz.ch/Corporate_Design#DINPro)
   as well.


If you have got the link and credentials, you can build the container
directly from github using `--build-arg`:

```bash
docker build -t fairguidegenerator \
    --build-arg FONT_LINK="https://wiki.amiv.ethz.ch/..." \
    --build-arg SOAP_USERNAME="..." \
    --build-arg SOAP_PASSWORD="..." \
    https://github.com/NotSpecial/fairguidegenerator.git

# Run on port 9876 (choose whatever you like)
docker run -p 9876:80 fairguidegenerator
```

Done!

The SOAP Credentials do not need to be specified as build arguments:
alternatively, they can be provided as environment variables.

Finally, this can be automated, the important configuration option in the
docker compose file is `build`
([Check out the docs.](https://docs.docker.com/compose/compose-file/#build))

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

# Set credentials
export SOAP_USERNAME=...
export SOAP_PASSWORD=...

# Run development server
export FLASK_APP=app.py
export FLASK_DEBUG=1
flask run
```

Now all is set up for development.
Instead of using environment vars, they can be put into a file named
`config.py`.
