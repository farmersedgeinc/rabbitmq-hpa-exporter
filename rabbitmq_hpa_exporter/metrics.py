from prometheus_client.core import GaugeMetricFamily

scaleFactor = GaugeMetricFamily("rabbitmqHpaScaleFactor", 
                    "Scale factor for rabbitmq celery worker HPA",
                    ['queue'])
workerBusyness = GaugeMetricFamily("celeryWorkerBusyness",
                       "Celery worker busyness from 0 to 1",
                       ['queue'])
pubAckRatio = GaugeMetricFamily("rabbitMqPublishAcknowledgementRatio",
                    "Ratio of publish rate to acknowledgement rate",
                    ['queue'])