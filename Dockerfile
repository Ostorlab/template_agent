FROM python:slim

RUN pip install -r requirements.txt

RUN mkdir /code
WORKDIR /code
ADD src/ /code/
ADD agent.yaml /code/


CMD python3 /code/agent.py