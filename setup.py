from setuptools import setup

setup(
  name='rabbitmq-hpa-exporter',
  version='0.1.0',
  description='',
  author='Farmers Edge',
  author_email='lindsay.ablonczy@farmersedge.ca',
  packages=['rabbitmq-hpa-exporter'],
  install_requires=[
    'celery',
    'prometheus_client',
    'requests'
  ],
)