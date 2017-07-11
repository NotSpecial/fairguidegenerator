# Use Arch linux as base because we need up to date version of TexLive+Python
FROM dock0/arch

# Set locale to something with utf-8 to avoid problems with files in python
ENV LANG=en_US.UTF-8

# Get development tools to compile uwsgi, Texlive (we also need latexextra)
# and python
RUN pacman -Sy --noconfirm gcc \
    texlive-core texlive-bin texlive-latexextra \
    python python-pip


## TeX and Font Setup

# Set HOME so we can use a local TEXMF tree and fonts
ENV HOME /

# Add amivtex to local texmf tree
COPY amivtex /texmf/tex/latex/amivtex

# Docker build arg: Link to download fonts as .tar.gz
ARG FONT_LINK

# Download and extract DINPro to local fonts and update font cache
RUN mkdir /.fonts ; \
	curl $FONT_LINK \
	| tar -xzC /.fonts
RUN fc-cache -f -v


## App Setup

# Install uwsgi Python web server and app requirements
RUN pip install uwsgi
COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /


## Configuration

# Allow configuration to be specified by environment var or build arg
ARG SOAP_USERNAME
ENV SOAP_USERNAME $SOAP_USERNAME
ARG SOAP_PASSWORD
ENV SOAP_PASSWORD $SOAP_PASSWORD


## uwsgi as entry point for the container

# Expose port 80 for uwsgi
EXPOSE 80

# uwsgi is entry point (disable file wrapper to send bytesio!)
ENTRYPOINT ["uwsgi", \
"--http", "0.0.0.0:80", \
"--manage-script-name", \
"--wsgi-disable-file-wrapper", \
"--mount", "/fairguidegenerator=app:app"]
