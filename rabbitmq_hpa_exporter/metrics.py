from prometheus_client.core import GaugeMetricFamily

def getMetrics():
  return {
    "rabbitmq_hpa_scale_factor": GaugeMetricFamily("rabbitmq_hpa_scale_factor", 
                                                   "Scale factor for rabbitmq celery worker HPA",
                                                   labels=['queue']),
    "celery_worker_busyness": GaugeMetricFamily("celery_worker_busyness",
                                                "Celery worker busyness from 0 to 1",
                                                labels=['queue']),
    "rabbitmq_consumer_restriction": GaugeMetricFamily("rabbitmq_consumer_restriction",
                                                       "Reverse of consumer utilization - how often consumers cannot fetch more messages from 0 to 1",
                                                       labels=['queue'])
  }