from prometheus_client.core import GaugeMetricFamily
import subprocess, requests, json

class RabbitmqHpaCollector(object):
  def __init__(self, config):
    self.celery = getattr(__import__(config["celery"]["module"], fromlist=[config["celery"]["app"]]), config["celery"]["app"])
  	self.config = config
    self.data = {}
    self.scaleFactor = GaugeMetricFamily("rabbitmqHpaScaleFactor", 
                                         "Scale factor for rabbitmq celery worker HPA",
                                         labels=['queue'])
    self.workerBusyness = GaugeMetricFamily("celeryWorkerBusyness",
                                            "Celery worker busyness from 0 to 1",
                                            labels=['queue'])
    self.pubAckRatio = GaugeMetricFamily("rabbitMqPublishAcknowledgementRatio",
                                         "Ratio of publish rate to acknowledgement rate",
                                         labels=['queue'])

  def getData():
    i = self.celery.inspect()
    queues = i.active_queues()
    stats = i.stats()
    active = i.active()
    reserved = i.reserved()

    rabbitStats = json.loads(requests.get("https://{}:{}@{}/api/queues".format(config["broker"]["user"], config["broker"]["pass"], config["broker"]["host"])).content)

    self.data = {}


    for key in queues:
      name = queues[key][0]["name"]
      if name not in self.data.keys():
        self.data[name] = {"reserved": 0.0, "active": 0.0, "prefetch": 0.0, "concurrency": 0.0, "publish": 0, "acknowledge": 0, "consumers": None}
      self.data[name]["active"] += len(active[key])
      self.data[name]["reserved"] += len(reserved[key])
      self.data[name]["prefetch"] += stats[key]["prefetch_count"]
      self.data[name]["concurrency"] += stats[key]["pool"]["max-concurrency"]

    for d in rabbitStats:
      if d["name"] in self.data.keys():
        if d.get("message_stats", {}).get("ack_details", None) != None:
          self.data[d["name"]]["acknowledge"] = d["message_stats"]["ack_details"]["rate"]
          self.data[d["name"]]["publish"] = d["message_stats"]["publish_details"]["rate"]
        self.data[d["name"]]["consumers"] = d["consumers"]

    for q in self.data:
      try:
        self.data[q]["ratio"] = self.data[q]["publish"]/self.data[q]["acknowledge"]
      except:
        self.data[q]["ratio"] = 1
      self.data[q]["busyness"] = (self.data[q]["reserved"]+self.data[q]["active"])/(self.data[q]["prefetch"]+self.data[q]["concurrency"])

  def collect():
    self.getData()

    for q in self.data:
      self.workerBusyness.add_metric([q], self.data[q]["busyness"])
      self.pubAckRatio.add_metric([q], self.data[q]["ratio"])

    yield self.workerBusyness
    yield self.pubAckRatio