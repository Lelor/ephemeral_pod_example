from flask import Flask, jsonify

from .k8s import EphemeralPod


app = Flask(__name__)


@app.route('/', methods=['GET'])
def run():
    # main()
    with EphemeralPod(name='banana-test', namespace='leorodr2') as p:
        p.run("""#!/bin/sh
              echo "Starting the script"
              for i in $(seq 1 10); do
                  echo "Iteration $i"
                  sleep 1
              done
              echo "Script completed"
              """)
        p.run("echo 'this one goes to stderr' >&2")
    return jsonify(hello='world')