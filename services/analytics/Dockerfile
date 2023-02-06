FROM python:3.9.16

WORKDIR /app

RUN apt-get update && python -m pip install aiohttp==3.8.3 && python -m pip install influxdb-client==1.36 && python -m pip install pika==1.3.1

COPY services/analytics/main.py /app/main.py

CMD ["python","/app/main.py"]
