import logging
import time

from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

class EphemeralPod():
    def __init__(self, cfg=None, name='Test', namespace='default'):
        if not cfg:
            #config.load_incluster_config()
            config.load_kube_config()
            try:
                cfg = Configuration().get_default_copy()
            except AttributeError:
                cfg = Configuration()
                cfg.assert_hostname = False
        Configuration.set_default(cfg)
        self.name = name
        self.namespace = namespace
        self.api = core_v1_api.CoreV1Api()
        self.manifest = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {
                'name': name
            },
            'spec': {
                'containers': [{
                    'image': 'busybox',
                    'name': 'sleep',
                    "args": [
                        "/bin/sh",
                        "-c",
                        "while true;do date;sleep 5; done"
                    ]
                }]
            }
        }

    def run(self, command):
        resp = stream(self.api.connect_get_namespaced_pod_exec,
                      self.name,
                      self.namespace,
                      command=['sh', '-c', command],
                      stderr=True, stdin=False,
                      stdout=True, tty=False,
                      _preload_content=False)
        while resp.is_open():
            resp.update(timeout=1)
            if resp.peek_stdout():
                logger.info("[STDOUT] %s" % resp.read_stdout())
            if resp.peek_stderr():
                logger.error("[STDERR] %s" % resp.read_stderr())
        resp.close()

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        try:
            self.tear_down()
        except:
            ...

    def __del__(self):
        try:
            self.tear_down()
        except:
            ...

    def setup(self):
        logger.info("Setting up ephemeral pod.")
        resp = self.api.create_namespaced_pod(body=self.manifest,
                                              namespace=self.namespace)
        while True:
            resp = self.api.read_namespaced_pod(name=self.name,
                                                namespace=self.namespace)
            if resp.status.phase != 'Pending':
                break
            time.sleep(1)
        logger.info(f"Pod {self.name} is up and running.")

    def tear_down(self):
        self.api.delete_namespaced_pod(self.name, self.namespace)
        logger.info(f'Tearing down pod "{self.name}".')
        while True:
            try:
                resp = self.api.read_namespaced_pod(name=self.name,
                                                    namespace=self.namespace)
            except ApiException as e:
                if e.status == 404:
                    break
                raise
            time.sleep(1)
