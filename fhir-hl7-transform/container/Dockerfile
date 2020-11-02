# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# Container image to run microservice implementing
# HL7v2 client (sender)
FROM python:3.8

WORKDIR /application

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY application/ .

CMD [ "python", "./hl7_sender.py" ]
