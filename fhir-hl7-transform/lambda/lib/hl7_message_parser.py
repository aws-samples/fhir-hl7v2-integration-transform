# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from hl7apy.core import Field
from hl7apy.parser import parse_message


def parse_oru_message(hl7msg: str, r: dict) -> dict:
    # This function will be implemented in the next release
    return r


def parse_adt_message(hl7msg: str, r: dict) -> dict:
    m = parse_message(hl7msg, find_groups=False)

    identifier_list = list()
    for pid_3 in m.PID.PID_3:
        identifier_element = {}
        if value := pid_3.PID_3_1.value:
            identifier_element["value"] = value
        if system := pid_3.PID_3_4.value:
            identifier_element["system"] = system
        if code := pid_3.PID_3_5.value:
            identifier_element["type"] = dict(coding=[dict(code=code)])
        if assigner := pid_3.PID_3_9.value:
            identifier_element["assigner"] = dict(display=assigner)
        identifier_list.append(identifier_element)
    r["identifier"] = identifier_list

    if pid_5 := m.PID.PID_5:
        r["name"] = list()
        for pid_5_rep in pid_5:
            r["name"].append(_parse_name_field(pid_5_rep))

    if birth_date := m.PID.PID_7.value:
        r["birthDate"] = birth_date

    if gender := m.PID.PID_8.value:
        r["gender"] = gender

    if pid_11 := m.PID.PID_11:
        r["address"] = list()
        for pid_11_rep in pid_11:
            r["address"].append(_parse_address_field(pid_11_rep))

    if pid_12 := m.PID.PID_12:
        for rep, address_county in enumerate(pid_12):
            r["address"][rep]["district"] = address_county.value

    pid_13, pid_14 = m.PID.PID_13, m.PID.PID_14
    if pid_13 or pid_14:
        r["telecom"] = _parse_telecom_fields(pid_13, pid_14)

    if m.NK1:
        # parse NK1 segments
        contact_list = list()
        for nk1 in m.NK1:
            contact = dict()
            if nk1_2 := nk1.NK1_2:
                contact["name"] = _parse_name_field(nk1_2)
            if nk1_4 := nk1.NK1_4:
                contact["address"] = _parse_address_field(nk1_4)
            nk1_5, nk1_6 = nk1.NK1_5, nk1.NK1_6
            if nk1_5 or nk1_6:
                contact["telecom"] = _parse_telecom_fields(nk1_5, nk1_6)
            if nk1_7 := nk1.NK1_7.value:
                contact["relationship"] = [dict(coding=[dict(code=nk1_7)])]
            contact_list.append(contact)
        r["contact"] = contact_list

    return r


def _parse_telecom_fields(
    personal_telecom_field: Field, work_telecom_field: Field
) -> list:
    telecom_list = list()
    for field in [personal_telecom_field, work_telecom_field]:
        if field:
            for rep in field:
                t = dict()
                if use_value := _get_telecom_use_value(rep.XTN_2.value):
                    t["use"] = use_value
                if value := rep.XTN_12.value:
                    t["value"] = value
                telecom_list.append(t)

    return telecom_list


def _get_telecom_use_value(use_code: str) -> str:
    mapping = dict(
        PRN="home",
        TMP="temp",
        OLD="old",
        MOB="mobile",
        WPN="work",
    )
    return mapping.get(use_code, "")


def _parse_name_field(name_field: Field) -> list:
    name_entry = dict()
    if family_name := name_field.XPN_1.value:
        name_entry["family"] = family_name
    given_name = list()
    if first_given_name := name_field.XPN_2.value:
        given_name.append(first_given_name)
    if other_given_names := name_field.XPN_3.value:
        for given_name_component in other_given_names.split(" "):
            given_name.append(given_name_component)
    if given_name:
        name_entry["given"] = given_name
    if prefix := name_field.XPN_5.value:
        name_entry["prefix"] = [prefix]
    if use := _get_name_type_value(name_field.XPN_7.value):
        name_entry["use"] = use
    return name_entry


def _parse_address_field(address_field: Field) -> list:
    address_list_entry = dict()
    address_line = list()
    if first_address_line := address_field.XAD_1.value:
        address_line.append(first_address_line)
    if second_address_line := address_field.XAD_2.value:
        address_line.append(second_address_line)
    if address_line:
        address_list_entry["line"] = address_line
    if city := address_field.XAD_3.value:
        address_list_entry["city"] = city
    if state := address_field.XAD_4.value:
        address_list_entry["state"] = state
    if postal_code := address_field.XAD_5.value:
        address_list_entry["postalCode"] = postal_code
    if country := address_field.XAD_6.value:
        address_list_entry["country"] = country
    if use := address_field.XAD_7.value:
        address_list_entry["use"] = use

    return address_list_entry


def _get_name_type_value(value: str) -> str:
    mapping = dict(
        U="usual",
        L="official",
        N="nickname",
        S="anonymous",
        M="maiden",
    )
    return mapping.get(value, "")
