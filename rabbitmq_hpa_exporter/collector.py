import subprocess, requests, json, metrics, sys, logging

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

    avgRatio = json.loads(requests.get(self.prometheus["host"], auth=self.prometheus["auth"], params={"query": "avg_over_time(rabbitmq_publish_acknowledgement_ratio{}[5m])"}).content)
    avgBusyness = json.loads(requests.get(self.prometheus["host"], auth=self.prometheus["auth"], params={"query": "avg_over_time(celery_worker_busyness{}[5m])"}).content)

    for key in queues:
      name = queues[key][0]["name"]
      if name not in tempData.keys():
        tempData[name] = {"reserved": 0.0, "active": 0.0, "prefetch": 0.0, "concurrency": 0.0, "publish": 0, "acknowledge": 0, "consumers": None}
      try:
        tempData[name]["active"] += len(active[key])
        tempData[name]["reserved"] += len(reserved[key])
        tempData[name]["prefetch"] += stats[key]["prefetch_count"]
        tempData[name]["concurrency"] += stats[key]["pool"]["max-concurrency"]
      except:
        del tempData[name]

    for d in rabbitStats:
      if d["name"] in tempData.keys():
        if d.get("message_stats", {}).get("ack_details", None) != None:
          tempData[d["name"]]["acknowledge"] = d["message_stats"]["ack_details"]["rate"]
          tempData[d["name"]]["publish"] = d["message_stats"]["publish_details"]["rate"]
        tempData[d["name"]]["consumers"] = float(d["consumers"])

    for r in avgRatio["data"]["result"]:
      tempData[r["metric"]["queue"]]["avgRatio"] = r["value"][1]
    for r in avgBusyness["data"]["result"]:
      tempData[r["metric"]["queue"]]["avgBusyness"] = r["value"][1]

    for q in tempData:
      try:
        tempData[q]["rabbitmq_publish_acknowledgement_ratio"] = tempData[q]["publish"]/tempData[q]["acknowledge"]
      except:
        tempData[q]["rabbitmq_publish_acknowledgement_ratio"] = 0
      tempData[q]["celery_worker_busyness"] = (tempData[q]["reserved"]+tempData[q]["active"])/(tempData[q]["prefetch"]+tempData[q]["concurrency"])
      if tempData[q].get("avgRatio", 1) > self.config.get("queues", {}).get(q, {}).get("scaleUpThreshold", 2) and tempData[q]["consumers"] != None:
        tempData[q]["rabbitmq_hpa_scale_factor"] = (tempData[q]["consumers"]+self.config.get("queues", {}).get(q, {}).get("scaleAmount", 1))/tempData[q]["consumers"]
      elif tempData[q].get("avgBusyness", 1) < self.config.get("queues", {}).get(q, {}).get("scaleDownThreshold", 0.5) and tempData[q]["consumers"] != None:
        tempData[q]["rabbitmq_hpa_scale_factor"] = (tempData[q]["consumers"]-self.config.get("queues", {}).get(q, {}).get("scaleAmount", 1))/tempData[q]["consumers"]
      else:
        tempData[q]["rabbitmq_hpa_scale_factor"] = 1

    self.data = tempData

  def collect(self):
    m = metrics.getMetrics()
    self.logger.debug(self.data)

    for q in self.data:
      for kind in m:
        if kind in self.data[q].keys():
          m[kind].add_metric(labels=[q], value=self.data[q][kind])
    for kind in m:
      yield m[kind]
