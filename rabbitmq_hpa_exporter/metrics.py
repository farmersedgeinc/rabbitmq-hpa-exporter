from prometheus_client.core import Gauge

scaleFactor = Gauge("rabbitmq_hpa_scale_factor", 
                    "Scale factor for rabbitmq celery worker HPA",
                    ['queue'])
workerBusyness = Gauge("celery_worker_busyness",
                       "Celery worker busyness from 0 to 1",
                       ['queue'])
pubAckRatio = Gauge("rabbitmq_publish_acknowledgement_ratio",
                    "Ratio of publish rate to acknowledgement rate",
                    ['queue'])