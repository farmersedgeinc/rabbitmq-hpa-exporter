import time, os
from prometheus_client.core import REGISTRY
from collector import RabbitmqHpaCollector

def start:
  with open(os.environ.get('RABBITMQ_HPA_EXPORTER_CONFIG')) as config:
    start_http_server(config.port)
    REGISTRY.register(RabbitmqHpaCollector(config))
    while True:
      time.sleep(1)