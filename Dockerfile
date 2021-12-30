FROM python:slim

RUN pip install -r requirements.txt

RUN mkdir /code
WORKDIR /code
ADD ./ /code/


CMD python3 /code/agent.py