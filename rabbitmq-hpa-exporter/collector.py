from prometheus_client.core import GaugeMetricFamily

class RabbitmqHpaCollector(object):
  def __init__(self, config):
    self.rabbitUrl = "https://{config['broker']['user']}:{config['broker']['password']}@{config['broker']['url']}/api/queues"
    self.gauge = GaugeMetricFamily("rabbitmqHpaScaleFactor", 
    	                             "Scale factor for rabbitmq celery worker HPA",
    	                             labels=['queue'])

  def getStats(self):


  def collect(self):
    
    # g.add_metric(["instance01.us.west.local"], 20)
    yield g