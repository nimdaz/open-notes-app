FROM python:3.12-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY run.py .

ENV DATA_DIR=/code/data
EXPOSE 5000

CMD ["python", "run.py"]
