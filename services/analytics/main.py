import pika
import os
import math
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


class Analytics():
    max_value = -math.inf
    min_value = math.inf
    influx_bucket = 'rabbit'
    influx_token = 'token-secreto'
    influx_url = 'http://influxdb:8086'
    influx_org = 'org'
    step_count = 0
    step_sum = 0
    days_with_100k_steps = 0
    days_with_5k_steps = 0
    prev_value = 0
    consecutive_days = 0

    def write_db(self, tag, key, value):
        client = InfluxDBClient(url=self.influx_url,
                                token=self.influx_token, org=self.influx_org)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        point = Point('Analytics').tag("Descriptive", tag).field(key, value)
        write_api.write(bucket=self.influx_bucket, record=point)

    def steps_day_more_walk(self, _measurement):
        if _measurement > self.max_value:
            self.max_value = _measurement
        self.write_db('steps', "Maximum", self.max_value)

    def steps_day_less_walk(self, _measurement):
        if _measurement < self.min_value:
            self.min_value = _measurement
        self.write_db('steps', "Minimum", self.min_value)

    def mean_of_steps(self, _measurement):
        self.step_count += 1
        self.step_sum += _measurement
        mean_of_steps = self.step_sum/self.step_count
        print("mean {}".format(mean_of_steps), flush=True)
        self.write_db('steps', "mean_of_steps", mean_of_steps)

    def more_than_100k_steps(self, _measurement):
        if _measurement >= 100000:
            self.days_with_100k_steps += 1
            print("days_with_100k_steps {}".format(
                self.days_with_100k_steps), flush=True)
        self.write_db('steps', "more_than_100k_steps",
                      self.days_with_100k_steps)

    def less_than_50k_steps(self, _measurement):
        if _measurement <= 50000:
            self.days_with_5k_steps += 1
            print("days_with_5k_steps {}".format(
                self.days_with_5k_steps), flush=True)
        self.write_db('steps', "less_than_50k_steps", self.days_with_5k_steps)

    def get_consecutive_days(self, _measurement):
        if _measurement >= self.prev_value:
            self.consecutive_days += 1
        else:
            self.consecutive_days = 0
        print("consecutive_days {}".format(self.consecutive_days), flush=True)
        self.prev_value = _measurement
        self.write_db('steps', "consecutive_days", self.consecutive_days)

    def take_measurement(self, _message):
        message = _message.split("=")
        measurement = float(message[-1])
        print("measurement {}".format(measurement), flush=True)
        self.steps_day_more_walk(measurement)
        self.steps_day_less_walk(measurement)
        self.mean_of_steps(measurement)
        self.more_than_100k_steps(measurement)
        self.less_than_50k_steps(measurement)
        self.get_consecutive_days(measurement)


if __name__ == '__main__':

    analytics = Analytics()

    def callback(ch, method, properties, body):
        global analytics
        message = body.decode("utf-8")
        analytics.take_measurement(message)

    url = os.environ.get('AMQP_URL', 'amqp://guest:guest@rabbit:5672/%2f')
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)

    channel = connection.channel()
    channel.queue_declare(queue='Reloj_inteligente')
    channel.queue_bind(exchange='amq.topic', queue='Reloj_inteligente', routing_key='#')
    channel.basic_consume(
        queue='Reloj_inteligente', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()
