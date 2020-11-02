# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import core
from aws_cdk import aws_ec2 as ec2


class EcsVpcStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        cidr = self.node.try_get_context("cidr")
        if not cidr:
            cidr = "10.10.0.0/16"

        ecs_vpc = ec2.Vpc(
            self,
            "FhirTransformVpc",
            cidr=cidr,
            max_azs=2,
        )

        core.CfnOutput(
            self,
            "TransformVpc",
            value=ecs_vpc.vpc_id,
            export_name="TransformVpc",
        )
