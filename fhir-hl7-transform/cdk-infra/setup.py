# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="fhir_to_hl7v2_transform",
    version="0.0.2",
    description="CDK App to deploy FHIR to HL7v2 transform proof of concept architecture",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Bakha Nurzhanov <bakha@amazon.com>",
    package_dir={"": "fhir_to_hl7v2_transform"},
    packages=setuptools.find_packages(where="fhir_to_hl7v2_transform"),
    install_requires=[
        "aws-cdk.core==1.69.0",
        "aws-cdk.aws-lambda==1.69.0",
        "aws-cdk.aws_ecs==1.69.0",
        "aws-cdk.aws_ecs_patterns==1.69.0",
        "aws_solutions_constructs.aws_apigateway_lambda==1.69.0",
    ],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
