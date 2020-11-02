# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from os import path

from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import core

COMPONENT_PREFIX = "Hl7TestServer"

dirname = path.dirname(__file__)


class TestHl7Stack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        vpc_id = self.node.try_get_context("vpc-id")
        if _server_port := (self.node.try_get_context("server-port")):
            server_port = int(_server_port)
        else:
            server_port = 2575

        # S3 Bucket to store and retrieve HL7v2 messages
        test_server_output_bucket = s3.Bucket(
            self,
            f"{COMPONENT_PREFIX}OutputBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        vpc = ec2.Vpc.from_lookup(self, "EcsVpc", vpc_id=vpc_id)

        # cluster = ecs.Cluster(self, f"{COMPONENT_PREFIX}", vpc=vpc)

        # Test receiver (server)
        nlb_service = ecs_patterns.NetworkLoadBalancedFargateService(
            self,
            f"{COMPONENT_PREFIX}Service",
            # cluster=cluster,
            task_image_options={
                "image": ecs.ContainerImage.from_asset(
                    path.join(dirname, "../../container")
                ),
                "container_port": server_port,
                "enable_logging": True,
                "environment": {
                    "S3_BUCKET_NAME": test_server_output_bucket.bucket_name,
                    "PORT_NUMBER": str(server_port),
                },
                "container_name": "hl7server",
            },
            desired_count=1,
            listener_port=server_port,
            public_load_balancer=False,
            vpc=vpc,
        )
        service = nlb_service.service
        connections = service.connections
        connections.allow_from(
            ec2.Peer.ipv4(vpc.vpc_cidr_block),
            ec2.Port.tcp(server_port),
            "Allow inbound HL7 connections",
        )
        task_definition = service.task_definition
        test_server_output_bucket.add_to_resource_policy(
            permission=iam.PolicyStatement(
                actions=["s3:ListBucket", "s3:PutObject"],
                effect=iam.Effect.ALLOW,
                principals=[task_definition.task_role],
                resources=[
                    test_server_output_bucket.bucket_arn,
                    test_server_output_bucket.arn_for_objects("*"),
                ],
            )
        )
        task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=["s3:ListBucket"],
                effect=iam.Effect.ALLOW,
                resources=[test_server_output_bucket.bucket_arn],
            )
        )
        task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject"],
                effect=iam.Effect.ALLOW,
                resources=[test_server_output_bucket.arn_for_objects("*")],
            )
        )

        core.CfnOutput(
            self,
            "TestHl7ServerFQDN",
            value=nlb_service.load_balancer.load_balancer_dns_name,
            export_name="TestHl7ServerFQDN",
        )

        core.CfnOutput(
            self,
            "TestHl7ServerS3",
            value=test_server_output_bucket.bucket_name,
            export_name="TestHl7ServerBucket",
        )
