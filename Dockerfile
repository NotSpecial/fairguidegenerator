# Use Arch linux as base because we need up to date version of TexLive+Python
FROM dock0/arch_full

# Get Texlive and python
RUN pacman -Sy --noconfirm texlive-most python python-pip

## TeX Setup

# Set HOME so we can use a local TEXMF tree and fonts
ENV HOME /

# Add amivtex to local texmf tree
ADD amivtex /texmf/tex/latex/amivtex

# Add DINPro to local fonts and update font cache
ADD DINPro /.fonts
RUN fc-cache -f -v

## App Setup

# Explicitly try to add config.py to get an error if its missing
ADD config.py /config,py

# Install uwsgi Python web server and app requirements
ADD requirements.txt /requirements.txt
RUN pip install uwsgi
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
ADD . /

# Expose port 80 for uwsgi
EXPOSE 80

# uwsgi is entry point (disable file wrapper to send bytesio!)
ENTRYPOINT ["uwsgi", \
"--http", "0.0.0.0:80", \
"--manage-script-name", \
"--wsgi-disable-file-wrapper", \
"--mount", "/fairguidegenerator=app:app"]
