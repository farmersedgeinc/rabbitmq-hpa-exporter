from prometheus_client.core import GaugeMetricFamily

def getMetrics():
  return {
    "rabbitmq_hpa_scale_factor": GaugeMetricFamily("rabbitmq_hpa_scale_factor", 
                                                   "Scale factor for rabbitmq celery worker HPA",
                                                   labels=['queue']),
    "celery_worker_busyness": GaugeMetricFamily("celery_worker_busyness",
                                                "Celery worker busyness from 0 to 1",
                                                labels=['queue']),
    "rabbitmq_ready_capacity_ratio": GaugeMetricFamily("rabbitmq_ready_capacity_ratio",
                                                      "Ratio of ready messages to current worker message capacity",
                                                      labels=['queue'])
  }