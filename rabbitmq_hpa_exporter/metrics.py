from prometheus_client.core import Gauge, CollectorRegistry

registry = CollectorRegistry()

scaleFactor = Gauge("rabbitmq_hpa_scale_factor", 
                    "Scale factor for rabbitmq celery worker HPA",
                    ['queue'], registry=registry)
workerBusyness = Gauge("celery_worker_busyness",
                       "Celery worker busyness from 0 to 1",
                       ['queue'], registry=registry)
pubAckRatio = Gauge("rabbitmq_publish_acknowledgement_ratio",
                    "Ratio of publish rate to acknowledgement rate",
                    ['queue'], registry=registry)