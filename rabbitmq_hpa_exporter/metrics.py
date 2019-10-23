from prometheus_client.core import GaugeMetricFamily

def getMetrics(logger):
  logger.debug("TEST")
  return {
    "rabbitmq_hpa_scale_factor": GaugeMetricFamily("rabbitmq_hpa_scale_factor", 
                                                   "Scale factor for rabbitmq celery worker HPA",
                                                   labels=['queue']),
    "celery_worker_busyness": GaugeMetricFamily("celery_worker_busyness",
                                                "Celery worker busyness from 0 to 1",
                                                labels=['queue']),
    "rabbitmq_publish_acknowledgement_ratio": GaugeMetricFamily("rabbitmq_publish_acknowledgement_ratio",
                                                                "Ratio of publish rate to acknowledgement rate",
                                                                labels=['queue'])
  }