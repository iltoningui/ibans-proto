import json

from google.protobuf.json_format import ParseDict

from bank_pb2 import Banks


def generate():
    data = []
    with open("banks/AO0600.txt", "r", encoding="utf8") as file:
        for line in file:
            if not line or line.startswith("#"):
                continue

            line = line.strip()
            code, name, initials, swift = line.split("|")

            data.append({"name": name, "code": code, "initials": initials, "swift": swift})

    banks = ParseDict({"list": data}, Banks())

    with open("banks.json", "w") as file:
        json.dump(data, file, indent=4)

    with open("banks.dat", "wb") as file:
        file.write(banks.SerializeToString())
