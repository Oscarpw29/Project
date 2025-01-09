# Start your image with a node base image
FROM ubuntu:20.04

ENV DEBIAN_frontend=noninteractive
ARG DEBIAN_FRONTEND=noninteractive

# The /app directory should act as the main application directory
RUN apt-get update && apt-get install -y python3.9 python3.9-dev python3-pip

FROM python:3.9 as build

RUN pip install --upgrade pip


COPY . .
COPY requirements.txt .

RUN pip install -r requirements.txt

EXPOSE 3000

CMD [."python" , "-m", "flask", "--app", "main" ,"run", "--host=0.0.0.0"]