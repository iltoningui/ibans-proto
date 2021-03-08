import os

import json

from google.protobuf.json_format import ParseDict

from proto.python.proto.specs_pb2 import BanksData


def generate():
    data = {}
    banks = {}
    import glob
    for path in glob.glob('data/banks/*.txt'):
        with open(os.path.join(os.getcwd(), path), "r", encoding="utf8") as file:
            for line in file:
                if not line or line.startswith("#"):
                    continue

                line = line.strip()
                country_code, code, name, short_name, swift = line.split("|")
                if not code or not name:
                    continue
                key = f"{country_code}{code}"
                filename = country_code + ".dat"
                if not banks.get(filename):
                    banks[filename] = {}

                data[key] = {"name": name, "code": code, "short_name": short_name, "swift": swift}
                banks[filename][key] = data[key]

    with open("json/banks.json", "w") as file:
        json.dump(data, file, indent=4)

    with open("json/banks.min.json", "w") as file:
        json.dump(data, file)

    for filename, bank_map in banks.items():
        bank_obj = ParseDict({"banks": bank_map}, BanksData())

        with open(f"bin/banks/{filename}", "wb+", ) as file:
            file.write(bank_obj.SerializeToString())
