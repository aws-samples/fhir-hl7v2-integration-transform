# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
from lib.hl7_to_fhir import Hl7v2ToFhirConverter


class FhirResourceReader(object):
    """
    Class representing FHIR resource reader
    """

    def __init__(self, s3_bucket_name: str, path_parameters: dict) -> None:
        self._s3_bucket_name = s3_bucket_name
        self._path_parameters = path_parameters
        self._resource_type = self._path_parameters.get("resource_type")
        self._resource_id = self._path_parameters.get("id")

    def _get_hl7_from_s3(self) -> str:
        s3 = boto3.resource("s3")
        obj_key = f"{self._resource_type}/{self._resource_id}"
        hl7obj = s3.Object(self._s3_bucket_name, obj_key)
        return hl7obj.get()["Body"].read().decode("utf-8")

    def read(self) -> str:
        self._hl7msg = self._get_hl7_from_s3()

        return Hl7v2ToFhirConverter(
            self._hl7msg, self._resource_type, self._resource_id
        ).transform()
