# Use an official Python runtime as a base image
FROM python:3.6

# Additionally get TeXLive
RUN apt-get update && apt-get install -y texlive texlive-lang-german texlive-latex-extra
RUN apt-get update && apt-get install -y texlive-xetex

# Set the working directory and home (needed for tex) to /app
WORKDIR /app
ENV HOME /app

# Copy the current directory contents into the container at /app
ADD . /app

# Add amivtex in correct folder so tex can find it
ADD /amivtex /app/texmf/tex/latex/amivtex


# Install uwsgi Python web server
RUN pip install uwsgi
# Install app requirements
RUN pip install -r requirements.txt

# Expose port 80 for uwsgi
EXPOSE 80

CMD ["uwsgi", "--http", "0.0.0.0:80", "--manage-script-name", "--mount", "/fairguidegenerator=app:app"]
