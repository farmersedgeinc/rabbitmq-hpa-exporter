import time, os, json
from metrics import registry
from prometheus_client import start_http_server
from prometheus_client.core import CollectorRegistry
from collector import RabbitmqHpaCollector

def start():
  with open(os.environ.get('RABBITMQ_HPA_EXPORTER_CONFIG')) as config:
    config = json.loads(config.read())
    collector = RabbitmqHpaCollector(config)
    registry = CollectorRegistry()
    registry.register(collector)
    start_http_server(config["port"], registry=registry)
    while True:
      collector.calculate()
      time.sleep(5)
