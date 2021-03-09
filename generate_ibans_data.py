import re
from collections import OrderedDict

from google.protobuf.json_format import ParseDict

import json
from proto.python.proto.specs_pb2 import IbansSpecs

codes = {
    "b": "bank_code",
    "s": "branch_code",
    "a": "balance_account_number",
    "i": "account_holder_number",
    "c": "account_number",
    "o": "owner_account_number",
    "m": "currency_code",
    "t": "account_type"
}


def generate():
    data = {}
    ibans = {}
    with open("data/ibans/ibans.txt", "r", encoding="utf8") as file:
        for line in file:
            if not line or line.startswith("#"):
                continue

            line = line.strip()
            country_code, country_name, length, bban_format, iban_fields = line.split("|")
            key = country_code
            filename = country_code[0] + ".dat"
            if not ibans.get(filename):
                ibans[filename] = {}

            iban_spec = __get_patterns(country_code, bban_format, iban_fields)
            iban_spec["formats"] = __get_format(iban_fields)
            iban_spec["country_name"] = country_name
            iban_spec["length"] = length
            data[key] = iban_spec
            ibans[filename][key] = iban_spec

    with open("json/ibans.json", "w") as file:
        json.dump(data, file, indent=4)

    with open("json/ibans.min.json", "w") as file:
        json.dump(data, file)

    for filename, bank_map in ibans.items():
        bank_obj = ParseDict({"specs": bank_map}, IbansSpecs())

        with open(f"bin/ibans/{filename}", "wb+", ) as file:
            file.write(bank_obj.SerializeToString())


def __get_patterns(country_code: str, bban_format: str, iban_fields: str) -> dict:
    iban_fields = iban_fields.replace(" ", "")
    iban_pattern = ""
    iban_pattern += f"({country_code})"

    patterns = {"country_code": 1, "check_digit": 2, "bban_pattern": "", "country_check_digits_pattern": ""}

    check_digit_field = iban_fields[2:4]
    if check_digit_field == "kk":
        check_digit_field = r"[0-9]{2}"

    iban_pattern += f"({check_digit_field})"

    fields = OrderedDict()

    for idx, letter in enumerate(iban_fields[4:], start=4):
        if letter in codes:
            if codes[letter] in fields:
                fields[codes[letter]] += 1
            else:
                fields[codes[letter]] = 1
        else:
            fields[idx] = letter

    group_number = 3
    for key, value in fields.items():
        if isinstance(key, int):
            iban_pattern += "."
        else:
            patterns[key] = group_number
            iban_pattern += f"(.{{{value}}})"
            group_number += 1

    patterns["iban_pattern"] = iban_pattern

    for x in bban_format.split(","):
        char_type = x[-1]
        size = x[:-1]
        if char_type == 'a':
            patterns["bban_pattern"] += f"[A-Z]{{{size}}}"
        elif char_type == 'c':
            patterns["bban_pattern"] += f"[A-Za-z0-9]{{{size}}}"
        elif char_type == 'n':
            patterns["bban_pattern"] += f"[0-9]{{{size}}}"

    reserved_fields = re.finditer(r"[0-9]+", iban_fields)
    if reserved_fields.__sizeof__() > 0:
        patterns["reserved_fields"] = {"pattern": "", "data": ""}
        pos = 0
        for match in reserved_fields:
            s = match.start()
            e = match.end()
            if s <= 3:
                continue
            patterns["reserved_fields"]["pattern"] += f".{{{pos}}}([{iban_fields[s:e]}]{{{e - s}}})"
            patterns["reserved_fields"]["data"] += iban_fields[s:e]
            pos += e - s

    for match in re.finditer(r"[x]+", iban_fields):
        s = match.start()
        e = match.end()
        if s <= 3:
            continue
        patterns["country_check_digits_pattern"] += f".{{{s}}}(.{{{e - s}}})"

    return patterns


def __get_format(iban_fields: str) -> dict:
    blocks = iban_fields.split(" ")
    iban_format = {"print": {}}

    format_patterns = []
    format_groups = []
    for idx, block in enumerate(blocks, start=1):
        size = len(block)
        format_patterns.append(f"(.{{{size}}})")
        format_groups.append("$" + str(idx))
    iban_format["print"]["pattern"] = "".join(format_patterns)
    iban_format["print"]["replacement"] = " ".join(format_groups)
    return iban_format
