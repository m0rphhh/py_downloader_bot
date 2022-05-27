FROM python:3.7

COPY /requirements.txt /app/requirements.txt
COPY /.env /app/.env

WORKDIR /app

RUN pip3 install -r /app/requirements.txt

ADD . /app

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg

CMD python3 /app/main.py