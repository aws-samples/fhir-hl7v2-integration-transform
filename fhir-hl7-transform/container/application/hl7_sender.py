# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import logging
import os
from signal import SIGINT, SIGTERM, signal

import boto3
from hl7.client import MLLPClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class SignalHandler:
    def __init__(self):
        self.received_signal = False
        signal(SIGINT, self._signal_handler)
        signal(SIGTERM, self._signal_handler)

    def _signal_handler(self, signal, frame):
        logger.info(f"handling signal {signal}, exiting gracefully")
        self.received_signal = True


sqs = boto3.resource("sqs")
queue = sqs.get_queue_by_name(QueueName=os.environ["QUEUE_NAME"])
port_number = int(os.environ.get("PORT_NUMBER", 2575))
server_name = os.environ.get("SERVER_NAME", "localhost")


def process_message(client, body):
    client.send_message(body)


def main():
    signal_handler = SignalHandler()
    while True:
        try:
            with MLLPClient(server_name, port_number) as client:
                print(f"Connecting to {server_name} on {port_number}", flush=True)
                while not signal_handler.received_signal:
                    messages = queue.receive_messages(
                        AttributeNames=["All"],
                        MaxNumberOfMessages=10,
                        WaitTimeSeconds=10,
                    )
                    for message in messages:
                        try:
                            print("Processing message...", flush=True)
                            process_message(client, message.body)
                            # BrokenPipeError: [Errno 32] Broken pipe
                            # ConnectionResetError: [Errno 104] Connection reset by peer
                        except ConnectionResetError as exc:
                            client.close()
                            raise exc
                        except ConnectionAbortedError as exc:
                            client.close()
                            raise exc
                        except Exception as exc:
                            client.close()
                            logger.exception(
                                f"Exception: {repr(exc)} Connection: {server_name}:{port_number}",
                                exc_info=exc,
                            )
                            # raise RuntimeError(
                            #     f"Parameters: {server_name}:{port_number}"
                            # ) from exc
                            raise exc
                        else:
                            message.delete()
        except ConnectionResetError as exc:
            print(f"Reconnecting due to {exc}")
            continue
        except ConnectionAbortedError as exc:
            print(f"Reconnecting due to {exc}")
            continue
        except BrokenPipeError as exc:
            print(f"Reconnecting due to {exc}")
            continue
        except TimeoutError as exc:
            print(f"Reconnecting due to {exc}")
            continue


if __name__ == "__main__":
    main()
