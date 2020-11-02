#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import core

from ecs_vpc.ecs_vpc_stack import EcsVpcStack


app = core.App()
EcsVpcStack(app, "ecs-vpc")

app.synth()
