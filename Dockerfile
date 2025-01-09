# Start your image with a node base image
FROM ubuntu:20.04

# The /app directory should act as the main application directory
RUN apt-get update && apt-get install -y python3.9 python3.9-dev

COPY . .

RUN pip install -r requirements.txt

CMD ["python]