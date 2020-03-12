FROM python:latest

WORKDIR /usr/src/spacebot

COPY requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY spacebot /usr/src/project/

EXPOSE 80

ENV PORT 80

ENV PYTHONPATH ${PYTHONPATH}:/usr/src/spacebot
CMD [ "python3", "main.py" ]