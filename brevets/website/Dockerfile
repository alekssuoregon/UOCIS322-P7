FROM python:3.8
LABEL maintainer="alekss@uoregon.edu"
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential
COPY . /web
WORKDIR /web
RUN pip install -r requirements.txt
