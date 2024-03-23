FROM python:3.11-slim-bullseye

RUN mkdir /code
WORKDIR /code

ENV PYTHONUNBUFFERED 1

RUN apt-get -y update && \
    apt-get -y install gcc python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /code/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy code and data folder into the Docker image
COPY . /code/
RUN ls /code
# expose the port
EXPOSE 8050
# Run the Dash app
CMD ["python", "app.py", "--host=0.0.0.0", "--port=8050"]
