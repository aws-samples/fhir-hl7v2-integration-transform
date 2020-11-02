# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from lib.hl7_message_parser import parse_adt_message, parse_oru_message


class Hl7v2ToFhirConverter(object):
    """
    This class converts HL7v2 messages to FHIR resource format using JSON
    """

    def __init__(self, hl7msg: str, resource_type: str, resource_id: str) -> None:
        self._hl7msg = hl7msg
        self._resource_type = resource_type
        self._resource_id = resource_id

    def transform(self) -> dict:
        r = dict()
        r["resourceType"] = self._resource_type
        r["id"] = self._resource_id
        if self._resource_type == "Patient":
            resource = parse_adt_message(self._hl7msg, r)
        elif self._resource_type == "Observation":
            resource = parse_oru_message(self._hl7msg, r)
        else:
            return {}

        return resource
