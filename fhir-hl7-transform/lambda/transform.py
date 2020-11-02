# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import logging
import os
from base64 import b64decode
from typing import Any

import boto3

from lib.fhir_resource_reader import FhirResourceReader
from lib.fhir_resource_writer import FhirResourceWriter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event, context):
    sqs_queue = os.environ.get("SQS_QUEUE")
    s3_bucket_name = os.environ.get("S3_BUCKET_NAME")

    if (sqs_queue is None) or (s3_bucket_name is None):
        logger.error("Check SQS_QUEUE or S3_BUCKET_NAME environment variables")
        return prepare_response(500, {}, "Configuration Error")

    http_method = event.get("httpMethod")

    # Write request
    if http_method in ["POST", "PUT"]:
        fhir_resource_content = parse_event(event)
        try:
            hl7v2_message, resource = FhirResourceWriter(
                fhir_resource_content,
                event.get("pathParameters") if http_method == "PUT" else None,
            ).write()
        except Exception as exc:
            path_parameters = event.get("pathParameters", {})
            resource_type = path_parameters.get("resource_type", "")
            status_code = 400
            resource = {}
            message = f"Unable to parse resource {resource_type}"
            logger.exception(message, exc_info=exc)
        else:
            try:
                send_hl7_to_transporter(sqs_queue, hl7v2_message)
                status_code = 201
                message = ""
            except Exception as exc:
                status_code = 500
                resource = {}
                message = "Unable to pass request to back end system"
                logger.exception(message, exc_info=exc)

    # Read request implemented in this proof of concept relies
    # on mock HL7 server implementation which stores HL7 messages
    # as S3 objects
    elif http_method == "GET":
        try:
            resource = FhirResourceReader(
                s3_bucket_name, event.get("pathParameters")
            ).read()
            status_code = 200
            message = ""
        except Exception as exc:
            path_parameters = event.get("pathParameters", {})
            resource_type = path_parameters.get("resource_type", "")
            id = path_parameters.get("id", "")
            status_code = 404
            resource = {}
            message = f"Unable to find resource {resource_type} with {id}"
            logger.error(f"Resource {resource_type}/{id} not found", exc_info=exc)

    # Delete
    elif http_method == "DELETE":
        status_code = 400
        resource = {}
        message = "We currently do not support DELETE requests"

    # Unknown method
    else:
        status_code = 501
        resource = {}
        message = f"Unknown method: {http_method}"
        logger.error(message)

    return prepare_response(status_code, resource, message)


def send_hl7_to_transporter(sqs_queue: str, message: Any) -> None:
    sqs = boto3.client("sqs")
    sqs.send_message(QueueUrl=sqs_queue, MessageBody=message)


def parse_event(event: Any) -> Any:
    if event.get("isBase64Encoded"):
        return json.loads(b64decode(event["body"]))
    else:
        return json.loads(event["body"])


def prepare_response(status_code: int, resource: Any, message: str) -> dict:
    body = {"resource": resource, "message": message}
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
    }
