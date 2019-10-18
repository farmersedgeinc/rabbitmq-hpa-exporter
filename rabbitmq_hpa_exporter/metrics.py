from prometheus_client.core import Gauge

scaleFactor = Gauge("rabbitmqHpaScaleFactor", 
                    "Scale factor for rabbitmq celery worker HPA",
                    ['queue'])
workerBusyness = Gauge("celeryWorkerBusyness",
                       "Celery worker busyness from 0 to 1",
                       ['queue'])
pubAckRatio = Gauge("rabbitMqPublishAcknowledgementRatio",
                    "Ratio of publish rate to acknowledgement rate",
                    ['queue'])