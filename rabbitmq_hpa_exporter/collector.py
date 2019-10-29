import subprocess, requests, json, metrics, sys, logging
from decimal import *

class RabbitmqHpaCollector(object):
  def __init__(self, config):
    self.celery = getattr(__import__(config["celery"]["module"], fromlist=[config["celery"]["app"]]), config["celery"]["app"])
    self.rabbitmq = {
      "host": "{}/api/queues".format(config["broker"]["host"]),
      "auth": (config["broker"].get("user", "user"),config["broker"].get("password", "pass"))
    }
    self.prometheus = {
      "host": "{}/api/v1/query".format(config["prometheus"]["host"]),
      "auth": (config["prometheus"].get("user", "user"),config["prometheus"].get("password", "pass"))
    }
    self.config = config
    self.data = {}
    self.logger = logging.getLogger("rabbitmq-hpa-exporter")
    self.logger.addHandler(logging.StreamHandler(sys.stdout))
    self.logger.setLevel(logging.DEBUG)

  def calculate(self):
    tempData = {}

    i = self.celery.control.inspect()
    queues = i.active_queues()
    stats = i.stats()
    active = i.active()
    reserved = i.reserved()

    rabbitStats = json.loads(requests.get(self.rabbitmq["host"], auth=self.rabbitmq["auth"]).content)

    avgRestriction = json.loads(requests.get(self.prometheus["host"], auth=self.prometheus["auth"], params={"query": "avg_over_time(rabbitmq_consumer_restriction{}[2m])"}).content)
    avgBusyness = json.loads(requests.get(self.prometheus["host"], auth=self.prometheus["auth"], params={"query": "avg_over_time(celery_worker_busyness{}[2m])"}).content)

    for key in queues:
      name = queues[key][0]["name"]
      if name not in tempData.keys():
        tempData[name] = {"reserved": Decimal(0), "active": Decimal(0), "prefetch": Decimal(0), "concurrency": Decimal(0), "consumers": None}
      try:
        tempData[name]["active"] += len(active[key])
        tempData[name]["reserved"] += len(reserved[key])
        tempData[name]["prefetch"] += stats[key]["prefetch_count"]
        tempData[name]["concurrency"] += stats[key]["pool"]["max-concurrency"]
      except:
        del tempData[name]

    for d in rabbitStats:
      if d["name"] in tempData.keys():
        tempData[d["name"]]["utilisation"] = d.get("consumer_utilisation", 1)
        tempData[d["name"]]["consumers"] = Decimal(d["consumers"])
        self.logger.debug("UTIL: {}".format(tempData[d["name"]]["utilisation"]))

    for r in avgRestriction["data"]["result"]:
      tempData[r["metric"]["queue"]]["avgRestriction"] = Decimal(r["value"][1])
    for r in avgBusyness["data"]["result"]:
      tempData[r["metric"]["queue"]]["avgBusyness"] = Decimal(r["value"][1])

    for q in tempData:
      try:
        tempData[q]["rabbitmq_consumer_restriction"] = Decimal(1)-tempData[q]["utilisation"]
      except:
        tempData[q]["rabbitmq_consumer_restriction"] = Decimal(0)
      tempData[q]["celery_worker_busyness"] = (tempData[q]["reserved"]+tempData[q]["active"])/(tempData[q]["prefetch"]+tempData[q]["concurrency"])
      if (tempData[q].get("avgRestriction", Decimal(1)) > self.config.get("queues", {}).get(q, {}).get("scaleUpThreshold", Decimal(0.3))) and tempData[q]["consumers"] != None:
        tempData[q]["rabbitmq_hpa_scale_factor"] = (tempData[q]["consumers"]+self.config.get("queues", {}).get(q, {}).get("scaleAmount", 1))/tempData[q]["consumers"]
      elif (tempData[q].get("avgBusyness", Decimal(1)) < self.config.get("queues", {}).get(q, {}).get("scaleDownThreshold", Decimal(0.5))) and tempData[q]["consumers"] != None:
        tempData[q]["rabbitmq_hpa_scale_factor"] = (tempData[q]["consumers"]-self.config.get("queues", {}).get(q, {}).get("scaleAmount", 1))/tempData[q]["consumers"]
      else:
        tempData[q]["rabbitmq_hpa_scale_factor"] = Decimal(1)

    self.data = tempData

  def collect(self):
    m = metrics.getMetrics()

    for q in self.data:
      for kind in m:
        if kind in self.data[q].keys():
          m[kind].add_metric(labels=[q], value=self.data[q][kind])
    for kind in m:
      yield m[kind]
