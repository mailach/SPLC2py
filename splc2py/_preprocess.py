import os
import xml.etree.ElementTree as ET
import pandas as pd


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
        ET.SubElement(r, "data", column="Configuration").text = str(bin)
        if len(numeric):
            ET.SubElement(r, "data", column="Variable Features").text = str(num)
        ET.SubElement(r, "data", column=nfp).text = str(row[nfp])
    return ET.ElementTree(root)


def prepare_learning_data(data: pd.DataFrame(), nfp) -> ET:
    features = data.drop(nfp, axis=1)
    binary = features.columns[features.isin([0, 1]).all()]
    numeric = [col for col in features.columns if col not in binary]
    measurements = _pandas_to_splcxml(data, nfp, binary, numeric)
    vm = _features_to_vm(binary, numeric, min(data.min()), max(data.max()))

    return vm, measurements


def serialize_data(cache_dir: str, artifacts: dict):
    for filename, artifact in artifacts.items():
        if "xml" in filename:
            artifact.write(os.path.join(cache_dir, filename))
        else:
            with open(os.path.join(cache_dir, filename), "w") as f:
                f.write(artifact)
