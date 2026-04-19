FROM python:3.10-slim

RUN apt update && apt upgrade -y && apt install git -y && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /requirements.txt
RUN pip3 install -U pip && pip3 install -U -r requirements.txt

WORKDIR /Forward-Bot
COPY . .

CMD gunicorn app:app & python3 main.py
