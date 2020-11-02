# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# Container image to run test HL7v2 server (receiver)
FROM python:3.8

WORKDIR /application

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY application/ .

EXPOSE 2575

CMD [ "python", "hl7_listener.py" ]
