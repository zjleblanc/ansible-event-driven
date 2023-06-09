from aiokafka import AIOKafkaProducer
from datetime import datetime
from pathlib import Path
import asyncio
import csv
import json
import os
import requests
import time

# GRAFANA_USER_ID = os.getenv('GRAFANA_USER_ID')
# GRAFANA_API_KEY = os.getenv('GRAFANA_API_KEY')
# def publish_prom_metric(name, label, source, value):
#     body = f'{name},bar_label={label},source={source} metric={value}'
#     requests.post('https://influx-prod-13-prod-us-east-0.grafana.net/api/v1/push/influx/write', 
#                             headers = {
#                             'Content-Type': 'text/plain',
#                             },
#                             data = str(body),
#                             auth = (GRAFANA_USER_ID, GRAFANA_API_KEY)
#     )

async def send_msg(topic, data):
    producer = AIOKafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))
    await producer.start()
    try:
        # Produce message
        await producer.send_and_wait(topic, data)
    finally:
        # Wait for all pending messages to be delivered or expire.
        await producer.stop()


async def process(dataset: Path):
    with open(dataset) as data:
        data_reader = csv.reader(data)
        next(data_reader, None) # skip headers

        last_power_kw = None
        for row in data_reader:
            power_kw = float(row[1])
            ts = datetime.strptime(row[0],'%Y-%m-%d %H:%M:%S')
            data = { "timestamp": str(ts), "power_kw": power_kw }
            if last_power_kw:
                data['change_kw'] = last_power_kw - power_kw
            last_power_kw = power_kw
            await send_msg('scada-data', data)
            #publish_prom_metric('wind_turbine_power','power_kw','grafanacloud-zleblanc-prom',power_kw)
            time.sleep(5)

if __name__ == '__main__':
    wind_turbine_data = (Path(__file__).parent / '../datasets/raw/wind_turbine/power.csv').resolve()
    asyncio.run(process(wind_turbine_data))