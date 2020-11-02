#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import os
from aws_cdk import core

from cdk_infra.test_hl7_server_stack import TestHl7Stack


app = core.App()
TestHl7Stack(
    app,
    "test-hl7-server-stack",
    stack_name="test-hl7-server-stack",
    env=core.Environment(
        account=os.environ["CDK_DEFAULT_ACCOUNT"],
        region=os.environ["CDK_DEFAULT_REGION"],
    ),
)

app.synth()
