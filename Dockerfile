# Use an official Python runtime as a base image
FROM python:3.6

## Tex Setup

# Install TeXLive and XeTeX
RUN apt-get update && apt-get install -y texlive texlive-xetex

# Set HOME so we can use a local TEXMF tree and fonts
ENV HOME /

# Add amivtex to local texmf tree
ADD amivtex /texmf/tex/latex/amivtex

# Add DINPro to local fonts and update font cache
ADD DINPro /.fonts
RUN fc-cache -f -v

## App Setup

# Copy the current directory contents into the container at /app
ADD . /

# Explicitly try to add config.py to get an error if its missing
ADD config.py /config,py

# Install uwsgi Python web server and app requirements
RUN pip install uwsgi
RUN pip install -r requirements.txt

# Expose port 80 for uwsgi
EXPOSE 80

# uwsgi is entry point
ENTRYPOINT ["uwsgi", "--http", "0.0.0.0:80", "--manage-script-name", "--mount", "/fairguidegenerator=app:app"]
