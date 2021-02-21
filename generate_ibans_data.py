import re
import json

from google.protobuf.json_format import ParseDict

from iban_spec_pb2 import IbansSpecs


def generate():
    data = []
    with open("ibans.txt", "r", encoding="utf8") as file:
        for line in file:
            if not line or line.startswith("#"):
                continue

            line = line.strip()
            country_code, country_name, length, bban_format, iban_fields = line.split("|")

            iban_spec = {"patterns": __get_patterns(bban_format, iban_fields),
                         "fields": __get_fields(iban_fields),
                         "country_code": country_code,
                         "country_name": country_name,
                         "length": int(length)}

            data.append(iban_spec)

    specs_pb = ParseDict({"list": data}, IbansSpecs())

    with open("ibans.json", "w") as file:
        json.dump(data, file, indent=4)

    with open("ibans.dat", "wb") as file:
        file.write(specs_pb.SerializeToString())


def __get_patterns(bban_format: str, iban_fields: str) -> dict:
    iban_fields = iban_fields.replace(" ", "")
    patterns = {"bban": r"^.{4}", "check_digit": "^.{2}", "constants": []}

    check_digit_field = iban_fields[2:4]
    if check_digit_field == "kk":
        patterns["check_digit"] += "[0-9]{2}"
    else:
        patterns["check_digit"] += check_digit_field

    for x in bban_format.split(","):
        char_type = x[-1]
        size = x[:-1]
        if char_type == 'a':
            patterns["bban"] += f"[A-Z]{{{size}}}"
        elif char_type == 'c':
            patterns["bban"] += f"[A-Za-z0-9]{{{size}}}"
        elif char_type == 'n':
            patterns["bban"] += f"[0-9]{{{size}}}"
    for match in re.finditer(r"[0-9]+", iban_fields):
        s = match.start()
        e = match.end()
        if s <= 3:
            continue
        constant = {"position": s, "constant": iban_fields[s:e]}
        constant["pattern"] = f"[.]{{{s}}}[{constant['constant']}]{{{e - s}}}"
        patterns["constants"].append(constant)

    return patterns


def __get_fields(iban_fields: str) -> dict:
    iban_fields = iban_fields.replace(" ", "")
    fields = {"bank_code": __get_field_from_pattern(r"[b]+", iban_fields),
              "account_number": __get_field_from_pattern(r"[c]+", iban_fields),
              "branch_code": __get_field_from_pattern(r"[s]+", iban_fields),
              "account_type": __get_field_from_pattern(r"[t]+", iban_fields),
              "account_holder": __get_field_from_pattern(r"[i]+", iban_fields),
              "balance_account_number": __get_field_from_pattern(r"[a]+", iban_fields),
              "owner_account_number": __get_field_from_pattern(r"[o]+", iban_fields),
              "currency_code": __get_field_from_pattern(r"[m]+", iban_fields),
              "country_check_digits": __get_field_list_from_pattern(r"[x]+", iban_fields),
              "constants": __get_field_constants_from_pattern(r"[0-9]+", iban_fields)}
    return fields


def __get_field_from_pattern(pattern, iban_fields):
    match = re.search(pattern, iban_fields)

    if match is None:
        return None

    s = match.start()
    e = match.end()

    field = {"position": s, "length": e - s}
    return field


def __get_field_constants_from_pattern(pattern, iban_fields) -> list:
    matches = re.finditer(pattern, iban_fields)
    constants = []
    for match in matches:
        s = match.start()
        e = match.end()
        if s <= 3:
            continue
        constants.append({"position": s, "constant": iban_fields[e:s]})
    return constants


def __get_field_list_from_pattern(pattern, iban_fields) -> list:
    matches = re.finditer(pattern, iban_fields)
    country_check_codes = []
    for match in matches:
        s = match.start()
        e = match.end()
        if s <= 3:
            continue
        country_check_codes.append({"position": s, "length": e - s})
    return country_check_codes
