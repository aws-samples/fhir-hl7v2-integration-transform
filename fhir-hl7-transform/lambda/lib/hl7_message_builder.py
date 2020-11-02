# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from datetime import datetime
from uuid import uuid4

from hl7apy import set_default_version as hl7_set_version
from hl7apy.core import Field, Message, Segment


def _create_hl7_message(message_name: str, message_type: str) -> Message:
    hl7_set_version("2.5.1")
    m = Message(message_name)
    msg_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
    m.MSH.MSH_7 = msg_datetime
    m.MSH.MSH_9 = message_type
    m.MSH.MSH_10 = uuid4().hex
    m.MSH.MSH_11 = "T"
    m.MSH.MSH_16 = "AL"

    return m


def create_adt_message(fhir_resource: dict) -> str:
    m = _create_hl7_message("ADT_A05", "ADT^A28^ADT_A05")
    m.PID = _create_pid_segment(fhir_resource)

    if contact_list := fhir_resource.get("contact"):
        for nk1_set_id, contact in enumerate(contact_list):
            nk1 = m.add_segment("NK1")
            _populate_nk1_segment(nk1, contact, nk1_set_id + 1)

    return m.to_er7()


def _create_pid_segment(fhir_resource: dict) -> Segment:
    pid = Segment("PID")
    pid.PID_1 = str(1)

    for id_ in fhir_resource.get("identifier"):
        id_value = id_.get("value", "")
        id_type = id_.get("type", {})

        if any([id_value, id_type]):
            pid_3 = pid.add_field("PID_3")
            pid_3.PID_3_1 = id_value
            pid_3.PID_3_4 = id_.get("system", "")
            if id_type_coding := id_type.get("coding"):
                pid_3.PID_3_5 = id_type_coding[0].get("code", "")

            if assigner := id_.get("assigner"):
                pid_3.PID_3_9 = assigner.get("display", "")

    if name_list := fhir_resource.get("name"):
        for name in name_list:
            pid_5 = pid.add_field("PID_5")
            _populate_name_field(pid_5, name)

    pid.PID_7 = fhir_resource.get("birthDate", "")
    pid.PID_8 = fhir_resource.get("gender", "")

    if address_list := fhir_resource.get("address"):
        for address in address_list:
            pid_11 = pid.add_field("PID_11")
            _populate_address_field(pid_11, address)
            if address_county := address.get("district"):
                pid_12 = pid.add_field("PID_12")
                pid_12.value = address_county

    if telecom_list := fhir_resource.get("telecom"):
        _populate_telecom_fields(pid, "PID_13", "PID_14", telecom_list)

    if patient_communication_list := fhir_resource.get("communication"):
        for patient_communication in patient_communication_list:
            pid_15 = pid.add_field("PID_15")
            pid_15.value = patient_communication.get("language", {}).get("text", "")

    pid.PID_16 = fhir_resource.get("maritalStatus", {}).get("text", "")

    return pid


def _populate_nk1_segment(nk1: Segment, contact: dict, set_id: int) -> None:
    nk1.NK1_1 = str(set_id)
    if name := contact.get("name"):
        nk1_2 = Field("NK1_2")
        _populate_name_field(nk1_2, name)
        nk1.add(nk1_2)
    if address := contact.get("address"):
        nk1_4 = nk1.add_field("NK1_4")
        _populate_address_field(nk1_4, address)
    if telecom_list := contact.get("telecom"):
        _populate_telecom_fields(nk1, "NK1_5", "NK1_6", telecom_list)
    if relationship := contact.get("relationship"):
        nk1.NK1_7 = relationship[0].get("coding", [""])[0].get("code", "")


def _populate_name_field(name_field: Field, name: dict) -> None:
    name_field.XPN_1 = name.get("family", "")
    if given_name := name.get("given"):
        name_field.XPN_2 = given_name[0]
        if len(given_name) > 1:
            name_field.XPN_3 = " ".join(given_name[1:])
    name_field.XPN_5 = name.get("prefix", [""])[0]
    name_field.XPN_7 = _get_name_type_code(name.get("use"))


def _get_name_type_code(value: str) -> str:
    mapping = dict(
        usual="U",
        official="L",
        temp="U",
        nickname="N",
        anonymous="S",
        old="U",
        maiden="M",
    )
    return mapping.get(value, "")


def _populate_address_field(address_field: Field, address: dict) -> None:
    if address_line_list := address.get("line"):
        address_field.XAD_1 = address_line_list[0]
        if len(address_line_list) > 1:
            address_field.XAD_2 = address_line_list[1]
    address_field.XAD_3 = address.get("city", "")
    address_field.XAD_4 = address.get("state", "")
    address_field.XAD_5 = address.get("postalCode", "")
    address_field.XAD_6 = address.get("country", "")
    address_field.XAD_7 = address.get("use", "")


def _populate_telecom_fields(
    segment: Segment, personal_telecom: str, work_telecom: str, telecom_list
) -> None:
    for telecom in telecom_list:
        telecom_type = telecom.get("use", "")
        telecom_value = telecom.get("value", "")
        if telecom_type in ["home", "temp", "old", "mobile", ""]:
            telecom = personal_telecom
        else:
            telecom = work_telecom
        if telecom_value:
            telecom_field = Field(telecom)
            telecom_field.XTN_2 = _get_telecom_use_code(telecom_type)
            telecom_field.XTN_12 = telecom_value
            segment.add(telecom_field)


def _get_telecom_use_code(telecom_type: str) -> str:
    mapping = dict(
        home="PRN",
        temp="TMP",
        old="OLD",
        mobile="MOB",
        work="WPN",
    )
    return mapping.get(telecom_type, "")
