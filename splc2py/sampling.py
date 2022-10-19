import logging
import tempfile
import os
from typing import Sequence
from abc import ABC, abstractmethod


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
        t = f"twise t:{params['t']}"
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


def _centralcomposite(params: dict[str, any]):
    return "centralcomposite"


def _boxbehnken(params: dict[str, any]):
    return "boxbehnken"


def _fullfactorial(params: dict[str, any]):
    return "fullfactorial"


def _random(params: dict[str, any]):
    try:
        r = f"random sampleSize:{params['sampleSize']} seed:{params['seed']}"
    except Exception as e:
        logging.error(
            "For using random sampling you need to specify sampleSize and seed."
        )
        raise e
    return r


def _hypersampling(params: dict[str, any]):
    try:
        r = f"hypersampling precision:{params['precision']}"
    except Exception as e:
        logging.error("For using hypersampling you need to specify precision.")
        raise e
    return r


def _onefactoratatime(params: dict[str, any]):
    try:
        r = f"onefactoratatime distinctValuesPerOption:{params['distinctValuesPerOption']}"
    except Exception as e:
        logging.error(
            "For using onefactoratatime you need to specify distinctValuesPerOption."
        )
        raise e
    return r


def _plackettburman(params: dict[str, any]):
    try:
        pb = f"plackettburman measurements:{params['measurements']} level:{params['level']}"
    except Exception as e:
        logging.error(
            "For using placketburman desing you need to specify measurements and level."
        )
        raise e
    return pb


def _kexchange(params: dict[str, any]):
    try:
        k = f"kexchange sampleSize:{params['sampleSize']} k:{params['k']}"
    except Exception as e:
        logging.error(
            "For using kexchange sampling you need to specify sampleSize and level."
        )
        raise e
    return k


def numericStrategyString(method: str, params: dict[str, any] = None):
    numericStrategies = {
        "random": _random,
        "centralcomposite": _centralcomposite,
        "plackettburman": _plackettburman,
        "fullfactorial": _fullfactorial,
        "boxbehnken": _boxbehnken,
        "hypersampling": _hypersampling,
        "onefactoratatime": _onefactoratatime,
        "kexchange": _kexchange,
    }
    return numericStrategies[method](params)


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


class Sampler(ABC):
    def __init__(self, vm: ET):
        self.vm = vm
        self.splc = _splc.SplcExecutor()

    def _serialize_data(self, cache_dir: str = None):

        self.vm.write(os.path.join(cache_dir, "vm.xml"))
        with open(os.path.join(cache_dir, "script.a"), "w") as f:
            f.write(self.script)

    @abstractmethod
    def sample(self, method, format, cache_dir, params):
        pass


class BinarySampler(Sampler):
    def _transform_sample(self, cache_dir: str, format: str = "list"):
        with open(os.path.join(cache_dir, "sampled.txt"), "r") as f:
            samples = f.readlines()
        configs = [_extract_binary(config) for config in samples]
        if format == "onehot":
            configs = _list_to_onehot(configs, _get_binary_features(self.vm))
        return configs

    def sample(
        self,
        method: str,
        format: str = "list",
        cache_dir: str = None,
        params=None,
    ):
        if not cache_dir:
            cache_dir = tempfile.mkdtemp()
        self.script = _splc.generate_script(binary=binaryStrategyString(method, params))

        # serialize vm and script and execute splc
        self._serialize_data(cache_dir)
        self.splc.execute(cache_dir)

        # extract sampled configurations
        configs = self._transform_sample(cache_dir, format)

        return configs


class NumericSampler(Sampler):
    def _transform_sample(self, cache_dir: str, format: str = "list"):
        with open(os.path.join(cache_dir, "sampled.txt"), "r") as f:
            samples = f.readlines()
        configs = [_extract_binary(config) for config in samples]
        if format == "onehot":
            configs = _list_to_onehot(configs, self.binary_features)
        return configs

    def sample(
        self,
        method: str,
        format: str = "list",
        cache_dir: str = None,
        params=None,
    ):
        if not cache_dir:
            cache_dir = tempfile.mkdtemp()
        self.script = _splc.generate_script(
            numeric=numericStrategyString(method, params)
        )

        # serialize vm and script and execute splc
        self._serialize_data(cache_dir)
        self.splc.execute(cache_dir)

        # extract sampled configurations
        # configs = self._transform_sample(cache_dir, format)

        print(cache_dir)
