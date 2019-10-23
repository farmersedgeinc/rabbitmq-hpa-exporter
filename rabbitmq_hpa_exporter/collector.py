import subprocess, requests, json, metrics, logging, sys

class RabbitmqHpaCollector(object):
  def __init__(self, config):
    self.celery = getattr(__import__(config["celery"]["module"], fromlist=[config["celery"]["app"]]), config["celery"]["app"])    
    self.config = config
    self.data = {}
    self.logger = logging.getLogger("hpa-exporter-logger")
    self.logger.setLevel(logging.DEBUG)
    self.logger.addHandler(logging.StreamHandler(sys.stdout))

  def calculate(self):
    tempData = {}

    i = self.celery.control.inspect()
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
        tempData[q]["rabbitmq_publish_acknowledgement_ratio"] = tempData[q]["publish"]/tempData[q]["acknowledge"]
      except:
        tempData[q]["rabbitmq_publish_acknowledgement_ratio"] = 0
      tempData[q]["celery_worker_busyness"] = (tempData[q]["reserved"]+tempData[q]["active"])/(tempData[q]["prefetch"]+tempData[q]["concurrency"])

    self.data = tempData

  def collect(self):
    m = metrics.getMetrics()
    self.logger.debug("METRICS: ".format(metrics))
    for q in self.data:
      for kind in m:
        m[kind].add_metric(labels=[q], value=self.data[q][kind])
    for kind in m:
      yield m[kind]
