# start by pulling the python image
FROM python:3.10-alpine

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:3000", "-t", "0", "--log-level", "debug"]
