import logging
import tempfile
import os
from typing import Sequence


import xml.etree.ElementTree as ET


from splc2py import _splc


def _featurewise(params: dict[str, str] = None):
    return "featurewise"


def _pairwise(params: dict[str, str] = None):
    return "pairwise"


def _negfeaturewise(params: dict[str, str] = None):
    return "negfw"


def _distancebased(params: dict[str, str]):
    try:
        db = f"distance-based optionWeight:{params['optionWeight']} numConfigs:{params['numConfigs']}"
    except Exception as e:
        logging.error(
            "For using distance-based sampling you need to specify numConfigs and optionWeight."
        )
        raise e
    return db


def _twise(params: dict[str, str]):
    try:
        t = f"twise t: {params['t']}"
    except Exception as e:
        logging.error("For using twise sampling you need to specify t.")
        raise e
    return t


def binaryStrategyString(method: str, params: dict[str, str] = None):
    binStrategies = {
        "featurewise": _featurewise,
        "pairwise": _pairwise,
        "negfeaturewise": _negfeaturewise,
        "distance-based": _distancebased,
        "twise": _twise,
    }
    return binStrategies[method](params)


def _extract_binary(config: str):
    config = config.split('"')[1].split("%;%")
    config = [option for option in config if option != ""]
    return config


def _get_binary_features(vm):
    return [
        option.find("name").text
        for option in vm.find("binaryOptions").findall("configurationOption")
    ]


def _list_to_onehot(configs: Sequence[Sequence[str]], features):
    onehot = []
    for config in configs:
        c = {}
        for option in features:
            c[option] = 1 if option in config else 0
        onehot.append(c)
    return onehot


class BinarySampler:
    def __init__(self, vm: ET):
        self.vm = vm
        self.binary_features = _get_binary_features(vm)
        self.splc = _splc.SplcExecutor()

    def _serialize_data(self, cache_dir: str = None):

        self.vm.write(os.path.join(cache_dir, "vm.xml"))
        with open(os.path.join(cache_dir, "script.a"), "w") as f:
            f.write(self.script)

    def _transform_sample(self, cache_dir: str, format: str = "list"):
        with open(os.path.join(cache_dir, "sampled.txt"), "r") as f:
            samples = f.readlines()
        configs = [_extract_binary(config) for config in samples]
        if format == "onehot":
            configs = _list_to_onehot(configs, self.binary_features)
        return configs

    def sample(self, method: str, format: str, cache_dir: str = None):
        if not cache_dir:
            cache_dir = tempfile.mkdtemp()
        self.script = _splc.generate_script(binary=binaryStrategyString(method))

        # serialize vm and script and execute splc
        self._serialize_data(cache_dir)
        self.splc.execute(cache_dir)

        # extract sampled configurations
        configs = self._transform_sample(cache_dir, format)

        return configs
