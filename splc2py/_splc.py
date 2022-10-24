import os
from typing import Dict, Sequence
import xml.etree.ElementTree as ET
from numpy import isin
import pandas as pd
import docker


def serialize_data(cache_dir: str, artifacts: dict):
    for filename, artifact in artifacts.items():
        if "xml" in filename:
            artifact.write(os.path.join(cache_dir, filename))
        else:
            with open(os.path.join(cache_dir, filename), "w") as f:
                f.write(artifact)


def generate_mlsettings(settings: Sequence[Dict[str, any]]):
    settings = [k + v for k, v in settings.items()]
    return "\n".join(settings)


def generate_script(
    binary: str = None,
    numeric: str = None,
    learning: str = None,
    mlsettings_pwd: str = None,
    nfp: str = None,
    solver: str = None,
):
    script = f"log /application/data/logs.txt\n"
    script += "vm /application/data/vm.xml\n"
    if binary:
        script += f"binary {binary}\n"
    if numeric:
        script += f"numeric {numeric}\n"
    if learning:
        script += f"load-mlsettings {mlsettings_pwd}\n"
        script += f"nfp {nfp}\n"
        script += "all /application/data/measurements.xml\n"
        if not numeric and not binary:
            script += "select-all-measurements true\n"
        script += "learn-splconqueror\nanalyze-learning\n"

    if solver:
        script += f"solver {solver}\n"
    script += f"printconfigs /application/data/sampled.txt\n"

    return script


def _row_to_str(row: pd.Series, binaries, numeric):
    bin = ",".join([b for b in binaries if row[b] == 1]) + ","
    num = ",".join([n + ";" + str(row[n]) for n in numeric]) + ","
    return bin, num


def _features_to_vm(binary, numeric, min, max):
    root = ET.Element("vm", name="fm")
    binaryOptions = ET.SubElement(root, "binaryOptions")
    for bin in binary:
        config = ET.SubElement(binaryOptions, "configurationOption")
        ET.SubElement(config, "name").text = bin
        ET.SubElement(config, "optional").text = "True"

    numericOptions = ET.SubElement(root, "numericOptions")
    for num in numeric:
        config = ET.SubElement(numericOptions, "configurationOption")
        ET.SubElement(config, "name").text = num
        ET.SubElement(config, "minValue").text = str(min)
        ET.SubElement(config, "maxValue").text = str(max)
        ET.SubElement(config, "stepFunction").text = num + "+ 1"

    return ET.ElementTree(root)


def _pandas_to_splcxml(data, nfp, binary, numeric):
    root = ET.Element("results")
    for _, row in data.iterrows():
        r = ET.SubElement(root, "row")
        bin, num = _row_to_str(row, binary, numeric)
        ET.SubElement(r, "data", columname="Configuration").text = str(bin)
        if len(numeric):
            ET.SubElement(r, "data", columname="Variable Features").text = str(num)
        ET.SubElement(r, "data", columname=nfp).text = str(row[nfp])
    return ET.ElementTree(root)


def pandas_to_xml(data: pd.DataFrame(), nfp) -> ET:
    features = data.drop(nfp, axis=1)
    binary = features.columns[features.isin([0, 1]).all()]
    numeric = [col for col in features.columns if col not in binary]
    measurements = _pandas_to_splcxml(data, nfp, binary, numeric)
    vm = _features_to_vm(binary, numeric, min(data.min()), max(data.max()))

    return vm, measurements


class SplcExecutor:
    def __init__(self):
        self.client = docker.from_env()

    def execute(self, mount_path: str):

        cmd = "mono SPLConqueror/SPLConqueror/CommandLine/bin/Release/CommandLine.exe /application/data/script.a"
        self.client.containers.run(
            image="mailach/splc",
            command=cmd,
            remove=True,
            volumes=[f"{mount_path}:/application/data"],
        )
        return mount_path
