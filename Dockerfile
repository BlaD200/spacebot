FROM python:latest

WORKDIR /usr/src/project

COPY requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY ./ /usr/src/project

EXPOSE 80

ENV PORT 80

ENV PYTHONPATH ${PYTHONPATH}:/usr/src/project
WORKDIR /usr/src/project/spacebot/app
CMD ["gunicorn", "--bind", "0.0.0.0:80", "main:app"]