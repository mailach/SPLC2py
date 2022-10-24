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


def _generate_model(history):
    model = _best_model(history)
    terms = model["Model"].split("+")
    return [
        {
            "coefficient": float(t.split(" * ")[0]),
            "options": t.strip().split(" * ")[1:],
        }
        for t in terms
    ]


def _best_model(models):
    best = [float(models[0]["ValidationError"]), 0]
    for i in range(len(models)):
        if float(models[i]["ValidationError"]) < best[0]:
            best[0] = float(models[i]["ValidationError"])
            best[1] = i
    return models[best[1]]


def extract_model_from_logs(tmpdir):
    with open(os.path.join(tmpdir, "logs.txt"), "r") as f:
        logs = f.readlines()

    beginModels = logs.index("command: analyze-learning\n") + 1
    endModels = logs.index("Analyze finished\n")
    table = logs[beginModels:endModels]
    header = [h.strip() for h in table[0].split(",")]
    history = []
    for row in table[3:]:
        row = row.split(";")
        m = {}
        for i in range(len(row)):
            m[header[i]] = row[i]
        history.append(m)

    return _generate_model(history), history


def _extract_options(config: str):
    config = config.split('"')[1].split("%;%")
    config = [option for option in config if option != ""]
    return config


def extract_samples(cache_dir: str, format: str = "list"):
    with open(os.path.join(cache_dir, "sampled.txt"), "r") as f:
        samples = f.readlines()

    configs = [_extract_options(config) for config in samples]
    return configs


def serialize_data(cache_dir: str, artifacts: dict):
    for filename, artifact in artifacts.items():
        if "xml" in filename:
            artifact.write(os.path.join(cache_dir, filename))
        else:
            with open(os.path.join(cache_dir, filename), "w") as f:
                f.write(artifact)
