# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from typing import Tuple
from uuid import uuid4

from lib.fhir_to_hl7 import FhirToHL7v2Converter
from lib.hl7_to_fhir import Hl7v2ToFhirConverter


class FhirResourceWriter:
    """
    Class representing FHIR resource writer
    """

    def __init__(self, payload: dict, path_parameters: dict = None) -> None:
        self._fhir_resource = payload
        self._path_parameters = path_parameters

    def write(self) -> (Tuple[str, str]):
        fhir_resource = self._set_resource_id()
        resource_type = self._get_resource_type()
        resource_id = fhir_resource.get("id")
        message = FhirToHL7v2Converter(fhir_resource, resource_type).transform()

        fhir_resource = Hl7v2ToFhirConverter(
            message, resource_type, resource_id
        ).transform()

        return (message, fhir_resource)

    def _get_resource_type(self) -> str:
        return self._fhir_resource.get("resourceType")

    def _set_resource_id(self) -> dict:
        fhir_resource = self._fhir_resource
        if self._path_parameters:
            resource_id = self._path_parameters["id"]
        else:
            resource_id = str(uuid4())
        fhir_resource["id"] = resource_id
        if fhir_resource.get("identifier") is None:
            fhir_resource["identifier"] = list()
        for identifier in fhir_resource["identifier"]:
            if identifier.get("value", "") == resource_id:
                break
        else:
            fhir_resource["identifier"].append(
                {
                    "value": resource_id,
                    "type": {
                        "coding": [
                            {
                                "code": "FW",
                            },
                        ],
                    },
                    "assigner": {
                        "display": "FHIR Works on AWS Integration Transform",
                    },
                }
            )

        return fhir_resource
