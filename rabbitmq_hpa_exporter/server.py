import time, os, json
from prometheus_client.core import REGISTRY
from prometheus_client import start_http_server
from collector import RabbitmqHpaCollector

def start():
  with open(os.environ.get('RABBITMQ_HPA_EXPORTER_CONFIG')) as config:
  	collector = RabbitmqHpaCollector(config)
    config = json.loads(config.read())
    start_http_server(config["port"])
    REGISTRY.register(collector)
    while True:
      collector.getData()
      time.sleep(5)
