# pull official base image
FROM python:3.7-buster


#Labels as key value pair
LABEL Maintainer="Guinsly (SP)"

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# i have chosen /usr/app/src
WORKDIR /usr/app/src

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

#to COPY the remote file at working directory in container
# copy project
COPY . .

CMD [ "python -m unittest tests.py"]
#docker build -t sp_ask_chat_review .
#docker run sp_ask_chat_review
