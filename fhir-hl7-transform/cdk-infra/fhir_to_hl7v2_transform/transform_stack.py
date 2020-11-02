# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from os import path

from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_ssm as ssm
from aws_cdk import core
from aws_solutions_constructs import aws_apigateway_lambda as apigw_lambda

dirname = path.dirname(__file__)

COMPONENT_PREFIX = "FhirToHl7v2"
COMPONENT_PREFIX_DASHES = "fhir-to-hl7v2"


class FhirToHl7V2TransformStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # API Gateway needs to have resource policy granting FHIR Works on AWS lambda
        # execute permissions. Lambda function ARN will be passed during deployment as CDK context variable
        # FHIR Works lambda will need to have policy attached to its execution role
        # allowing it to invoke API
        # From --context resource-router-lambda-role="arn:aws:iam::123456789012:role/rolename"
        imported_resource_router_lambda_role = self.node.try_get_context(
            "resource-router-lambda-role"
        )
        # Amazon ECS on AWS Fargate container implementing connection manager
        # will be launched into a VPC that needs to have private and public subnets
        # and NAT gateway or instance
        # From --context vpc-id="vpc-123456"
        vpc_id = self.node.try_get_context("vpc-id")

        # The following parameters specify name of the HL7 server
        # that will be receiving transformed HL7v2 messages and TCP port
        # that it will be listening on
        # From --context hl7-server-name="hl7.example.com"
        # From --context hl7-port="2575"
        hl7_server_name = self.node.try_get_context("hl7-server-name")
        hl7_port = self.node.try_get_context("hl7-port")

        # In this proof of concept source of data for read interactions
        # is S3 bucket where mock HL7 server stores processed HL7 messages
        # From --context test-server-output-bucket-name="DOC-EXAMPLE-BUCKET"
        test_server_output_bucket_name = self.node.try_get_context(
            "test-server-output-bucket-name"
        )

        # SQS queue
        # Custom transform lambda communicates with Connectivity Manager using this SQS queue
        queue = sqs.Queue(
            self, f"{COMPONENT_PREFIX}Queue", encryption=sqs.QueueEncryption.KMS_MANAGED
        )

        # S3 Bucket to retrieve HL7v2 messages in proof of concept deployment
        test_server_output_bucket = s3.Bucket.from_bucket_name(
            self, f"{COMPONENT_PREFIX}OutputBucket", test_server_output_bucket_name
        )

        # Transform Lambda
        # Reference implementation of Custom Transform component of Transform Execution Environment

        transform_lambda = lambda_.Function(
            self,
            f"{COMPONENT_PREFIX}TransformLambda",
            handler="transform.handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            code=lambda_.Code.from_asset(
                path.join(dirname, "../../lambda"),
                bundling={
                    "image": lambda_.Runtime.PYTHON_3_8.bundling_docker_image,
                    "command": [
                        "bash",
                        "-c",
                        " && ".join(
                            [
                                "pip install --no-cache-dir -r requirements.txt -t /asset-output",
                                "(tar -c --exclude-from=exclude.lst -f - .)|(cd /asset-output; tar -xf -)",
                            ]
                        ),
                    ],
                },
            ),
            timeout=core.Duration.seconds(60),
            environment=dict(
                SQS_QUEUE=queue.queue_url,
                # The following parameter is optional
                S3_BUCKET_NAME=test_server_output_bucket_name,
            ),
        )
        queue.grant_send_messages(transform_lambda)

        # API Gateway with Lambda construct (using https://aws.amazon.com/solutions/constructs/patterns)
        # Reference implementation of Custom Transform component of Transform Execution Environment

        api_lambda = apigw_lambda.ApiGatewayToLambda(
            self,
            "ApiGw",
            existing_lambda_obj=transform_lambda,
            api_gateway_props=apigw.LambdaRestApiProps(
                handler=transform_lambda,
                proxy=False,
                rest_api_name=f"{COMPONENT_PREFIX_DASHES}-api",
                endpoint_export_name=f"{COMPONENT_PREFIX}ApiEndPoint",
                description=f"{COMPONENT_PREFIX} APIGW with Transform Lambda (FHIR to HL7v2)",
                default_method_options=apigw.MethodOptions(
                    authorization_type=apigw.AuthorizationType.IAM,
                ),
                policy=iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["execute-api:Invoke"],
                            effect=iam.Effect.ALLOW,
                            principals=[
                                iam.ArnPrincipal(imported_resource_router_lambda_role),
                            ],
                            resources=["execute-api:/*/*/*"],
                        )
                    ]
                ),
            ),
        )
        rest_api = api_lambda.api_gateway
        persistence = rest_api.root.add_resource("persistence")
        resource_type = persistence.add_resource("{resource_type}")
        resource_type.add_method("POST")
        resource_id = resource_type.add_resource("{id}")
        resource_id.add_method("GET")
        resource_id.add_method("PUT")
        resource_id.add_method("DELETE")

        # ECS Fargate Container (HL7v2 sender)
        # This container implements Connectivity Manager component
        # of Transform Execution Environment

        vpc = ec2.Vpc.from_lookup(self, "DefaultVpc", vpc_id=vpc_id)

        cluster = ecs.Cluster(self, f"{COMPONENT_PREFIX}Cluster", vpc=vpc)

        ecs_patterns.QueueProcessingFargateService(
            self,
            f"{COMPONENT_PREFIX}Service",
            cluster=cluster,
            image=ecs.ContainerImage.from_asset(path.join(dirname, "../../container")),
            queue=queue,
            desired_task_count=1,
            log_driver=ecs.LogDriver.aws_logs(
                stream_prefix=f"{COMPONENT_PREFIX}HL7Client",
                log_retention=logs.RetentionDays.ONE_DAY,
            ),
            environment=dict(
                SERVER_NAME=hl7_server_name,
                PORT_NUMBER=hl7_port,
            ),
        )

        # The following permission grants are needed to support
        # read interactions with integration transform
        test_server_output_bucket.grant_read(transform_lambda)

        transform_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:ListBucket"],
                effect=iam.Effect.ALLOW,
                resources=[test_server_output_bucket.bucket_arn],
            )
        )
        transform_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                effect=iam.Effect.ALLOW,
                resources=[test_server_output_bucket.arn_for_objects("*")],
            )
        )

        # CloudFormation Stack outputs
        # The following outputs needed to configure FHIR Works on AWS API interface
        core.CfnOutput(
            self,
            "TransformApiRootUrl",
            value=rest_api.url,
            export_name="TransformApiRootUrl",
        )
        core.CfnOutput(
            self,
            "TransformApiRegion",
            value=self.region,
            export_name="TransformApiRegion",
        )
        core.CfnOutput(
            self,
            "TransformApiAccountId",
            value=self.account,
            export_name="TransformApiAccountId",
        )
