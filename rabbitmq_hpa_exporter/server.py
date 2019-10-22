import time, os, json
from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY
from collector import RabbitmqHpaCollector

def start():
  with open(os.environ.get('RABBITMQ_HPA_EXPORTER_CONFIG')) as config:
    config = json.loads(config.read())
    collector = RabbitmqHpaCollector(config)
    REGISTRY.register(collector)
    start_http_server(config["port"], registry=REGISTRY)
    while True:
      collector.calculate()
      time.sleep(10)
