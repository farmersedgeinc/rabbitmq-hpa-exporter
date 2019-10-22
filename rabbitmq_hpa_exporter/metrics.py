from prometheus_client.core import GaugeMetricFamily, CollectorRegistry

registry = CollectorRegistry()

scaleFactor = GaugeMetricFamily("rabbitmq_hpa_scale_factor", 
                                "Scale factor for rabbitmq celery worker HPA",
                                labels=['queue'], registry=registry)
workerBusyness = GaugeMetricFamily("celery_worker_busyness",
                                   "Celery worker busyness from 0 to 1",
                                   labels=['queue'], registry=registry)
pubAckRatio = GaugeMetricFamily("rabbitmq_publish_acknowledgement_ratio",
                                "Ratio of publish rate to acknowledgement rate",
                                labels=['queue'], registry=registry)