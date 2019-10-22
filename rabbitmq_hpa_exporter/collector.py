import subprocess, requests, json, metrics, logging, sys

class RabbitmqHpaCollector(object):
  def __init__(self, config):
    self.config = config
    self.data = {}
    self.logger = logging.getLogger("hpa-exporter-logger")
    self.logger.setLevel(logging.DEBUG)
    self.logger.addHandler(logging.StreamHandler(sys.stdout))

  def calculate(self):
    celery = getattr(__import__(self.config["celery"]["module"], fromlist=[self.config["celery"]["app"]]), self.config["celery"]["app"])
    tempData = {}

    i = celery.control.inspect()
    queues = i.active_queues()
    stats = i.stats()
    active = i.active()
    reserved = i.reserved()

    rabbitStats = json.loads(requests.get("https://{}:{}@{}/api/queues".format(self.config["broker"]["user"], self.config["broker"]["password"], self.config["broker"]["host"])).content)

    for key in queues:
      name = queues[key][0]["name"]
      if name not in tempData.keys():
        tempData[name] = {"reserved": 0.0, "active": 0.0, "prefetch": 0.0, "concurrency": 0.0, "publish": 0, "acknowledge": 0, "consumers": None}
      tempData[name]["active"] += len(active[key])
      tempData[name]["reserved"] += len(reserved[key])
      tempData[name]["prefetch"] += stats[key]["prefetch_count"]
      tempData[name]["concurrency"] += stats[key]["pool"]["max-concurrency"]

    for d in rabbitStats:
      if d["name"] in tempData.keys():
        if d.get("message_stats", {}).get("ack_details", None) != None:
          tempData[d["name"]]["acknowledge"] = d["message_stats"]["ack_details"]["rate"]
          tempData[d["name"]]["publish"] = d["message_stats"]["publish_details"]["rate"]
        tempData[d["name"]]["consumers"] = d["consumers"]

    for q in tempData:
      try:
        tempData[q]["ratio"] = tempData[q]["publish"]/tempData[q]["acknowledge"]
      except:
        tempData[q]["ratio"] = 1
      tempData[q]["busyness"] = (tempData[q]["reserved"]+tempData[q]["active"])/(tempData[q]["prefetch"]+tempData[q]["concurrency"])

    self.data = tempData

  def collect(self):
    self.logger.debug("\nCOLLECT CALLED, CURRENT VALUES: - {}\n".format(self.data))
    workerBusyness = GaugeMetricFamily("celery_worker_busyness",
                                       "Celery worker busyness from 0 to 1",
                                       labels=['queue'])
    pubAckRatio = GaugeMetricFamily("rabbitmq_publish_acknowledgement_ratio",
                                    "Ratio of publish rate to acknowledgement rate",
                                    labels=['queue'])
    for q in self.data:
      workerBusyness.add_metric(labels=[q], value=self.data[q]["busyness"])
      pubAckRatio.add_metric(labels=[q], value=self.data[q]["ratio"])
    self.logger.debug("\nBUSYNESS: {}".format(metrics.workerBusyness))
    yield metrics.workerBusyness
    yield metrics.pubAckRatio