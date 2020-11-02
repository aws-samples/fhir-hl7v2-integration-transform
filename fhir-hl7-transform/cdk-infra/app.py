#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os

from aws_cdk import core

from fhir_to_hl7v2_transform.transform_stack import FhirToHl7V2TransformStack

app = core.App()

transform_stack = FhirToHl7V2TransformStack(
    app,
    "fhir-to-hl7v2-transform",
    env=core.Environment(
        account=os.environ["CDK_DEFAULT_ACCOUNT"],
        region=os.environ["CDK_DEFAULT_REGION"],
    ),
)


app.synth()
