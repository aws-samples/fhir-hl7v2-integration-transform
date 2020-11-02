# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from lib.hl7_message_builder import create_adt_message


class FhirToHL7v2Converter(object):
    def __init__(self, fhir_resource: dict, resource_type: str) -> None:
        self._fhir_resource = fhir_resource
        self._resource_type = resource_type

    def transform(self) -> str:
        if self._resource_type == "Patient":
            return create_adt_message(self._fhir_resource)
