# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import logging
import os
import signal

import boto3
from twisted.internet import defer, reactor
from txHL7.mllp import MLLPFactory
from txHL7.receiver import AbstractHL7Receiver

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_bucket_name = os.environ["S3_BUCKET_NAME"]
port = int(os.environ.get("PORT_NUMBER", "2575"))

resource_type = {
    "ADT": "Patient",
    "ORU": "Observation",
}


class HL7Receiver(AbstractHL7Receiver):
    def handleMessage(self, container):
        message = container.message

        message_type = str(message["MSH.F9"])
        resource_id = None
        for pid_3 in message.segment("PID")[3]:
            if len(pid_3) >= 5 and str(pid_3[4]) == "FW":
                resource_id = str(pid_3[0])
                break

        if resource_id is None:
            raise Exception("Unable to get resource ID from the message")

        print(f"Received message {message_type} id: [{resource_id}]", flush=True)

        try:
            s3 = boto3.resource("s3")
            s3_object = s3.Object(
                s3_bucket_name,
                f"{resource_type.get(str(message_type), 'Other')}/{resource_id}",
            )
            s3_object.put(Body=str.encode(str(message)))
        except Exception as e:
            logger.exception(f"Exception: {repr(e)}", exc_info=e)
            raise (e)
        else:
            # We succeeded, so ACK back (default is AA)
            return defer.succeed(container.ack())


def handler(signum, frame):
    logger.info(f"Signal {signum} caught.")


def run(port):
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    receiver = HL7Receiver()
    factory = MLLPFactory(receiver)

    reactor.listenTCP(port, factory)
    print(f"Listening on port {port}", flush=True)
    reactor.run()


if __name__ == "__main__":
    run(port)
