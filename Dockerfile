FROM python:latest

WORKDIR /usr/src/app

COPY app/requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app /usr/src/app

EXPOSE 443

ENV PORT 443

ENV PYTHONPATH ${PYTHONPATH}:/usr/src/app
CMD [ "python3", "main.py" ]