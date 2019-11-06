from prometheus_client.core import GaugeMetricFamily

def getMetrics():
  return {
    "rabbitmq_hpa_scale_factor": GaugeMetricFamily("rabbitmq_hpa_scale_factor", 
                                                   "Scale factor for rabbitmq celery worker HPA",
                                                   labels=['queue']),
    "celery_worker_busyness": GaugeMetricFamily("celery_worker_busyness",
                                                "Celery worker busyness from 0 to 1",
                                                labels=['queue']),
    "rabbitmq_consumer_availability": GaugeMetricFamily("rabbitmq_consumer_availability",
                                                        "Portion of time where workers are able to get more tasks from 0 to 1",
                                                        labels=['queue'])
  }