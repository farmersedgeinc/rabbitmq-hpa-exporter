import subprocess, requests, json, metrics, sys, logging
from decimal import *

filters = ["celeryev.", "celery@", "amq.gen"]

def divide(num1, num2):
  try:
    return num1/num2
  except:
    if num1 == num2:
      return Decimal(1)
    else:
      return num1    

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

    avgRatio = json.loads(requests.get(self.prometheus["host"], auth=self.prometheus["auth"], params={"query": "avg_over_time(rabbitmq_ready_capacity_ratio{}[2m])"}).content)
    avgBusyness = json.loads(requests.get(self.prometheus["host"], auth=self.prometheus["auth"], params={"query": "avg_over_time(celery_worker_busyness{}[2m])"}).content)

    for d in rabbitStats:
      name = d["name"]
      if not any(f in name for f in filters):
        if name not in self.data:
          self.data[name] = {}
        tempData[name] = {"reserved": Decimal(0), "active": Decimal(0), "prefetch": Decimal(0), "concurrency": Decimal(0)}
        try:
          self.data[name]["consumers"] = Decimal(d["consumers"])
        except:
          self.data[name]["consumers"] = None
        self.data[name]["ready"] = Decimal(d["messages_ready"])

    for key in queues:
      name = queues[key][0]["name"]
      # sometimes these queries don't have all the data needed, so better all or nothing
      if name in tempData:
        try:
          tempData[name]["active"] += len(active[key])
          tempData[name]["reserved"] += len(reserved[key])
          tempData[name]["prefetch"] += stats[key]["prefetch_count"]
          tempData[name]["concurrency"] += stats[key]["pool"]["max-concurrency"]
        except:
          del tempData[name]

    for name in tempData:
      self.data[name].update(tempData[name])

    for r in avgRatio["data"]["result"]:
      if r["metric"]["queue"] in self.data:
        self.data[r["metric"]["queue"]]["avgRatio"] = Decimal(r["value"][1])
    for r in avgBusyness["data"]["result"]:
      if r["metric"]["queue"] in self.data:
        self.data[r["metric"]["queue"]]["avgBusyness"] = Decimal(r["value"][1])

    for q in self.data:
      try:
        self.data[q]["rabbitmq_ready_capacity_ratio"] = self.data[q]["ready"]/(self.data[q]["prefetch"]+self.data[q]["concurrency"])
      except:
        self.data[q]["rabbitmq_ready_capacity_ratio"] = Decimal(0)
      try:
        self.data[q]["celery_worker_busyness"] = divide(self.data[q]["reserved"]+self.data[q]["active"], self.data[q]["prefetch"]+self.data[q]["concurrency"])
      except:
        self.data[q]["celery_worker_busyness"] = Decimal(1)
      if (self.data[q].get("avgRatio", Decimal(0)) > self.config.get("queues", {}).get(q, {}).get("scaleUpThreshold", Decimal(1))) and self.data[q]["consumers"] != None:
        self.data[q]["rabbitmq_hpa_scale_factor"] = divide(self.data[q]["consumers"]+self.config.get("queues", {}).get(q, {}).get("scaleAmount", 1), self.data[q]["consumers"])
      elif (self.data[q].get("avgBusyness", Decimal(1)) < self.config.get("queues", {}).get(q, {}).get("scaleDownThreshold", Decimal(0.5))) and self.data[q]["consumers"] != None:
        self.data[q]["rabbitmq_hpa_scale_factor"] = divide(self.data[q]["consumers"]-self.config.get("queues", {}).get(q, {}).get("scaleAmount", 1), self.data[q]["consumers"])
      else:
        self.data[q]["rabbitmq_hpa_scale_factor"] = Decimal(1)

  def collect(self):
    m = metrics.getMetrics()

    for q in self.data:
      for kind in m:
        if kind in self.data[q].keys():
          m[kind].add_metric(labels=[q], value=self.data[q][kind])
    for kind in m:
      yield m[kind]
