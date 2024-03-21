FROM python:3.11-slim-bullseye

RUN mkdir /code
WORKDIR /code

ENV PYTHONUNBUFFERED 1

RUN apt-get -y update && \
    apt-get -y install gcc python3-dev git curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /code/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
