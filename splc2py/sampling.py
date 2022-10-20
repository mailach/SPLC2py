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


def _allbinary(params: dict[str, str] = None):
    return "allbinary"


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
        "allbinary": _allbinary,
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


def _extract_options(config: str):
    config = config.split('"')[1].split("%;%")
    config = [option for option in config if option != ""]
    return config


def _get_binary_features(vm):
    return [
        option.find("name").text
        for option in vm.find("binaryOptions").findall("configurationOption")
    ]


def _get_numeric_features(vm):
    return [
        option.find("name").text
        for option in vm.find("numericOptions").findall("configurationOption")
    ]


def _list_to_dict(configs: Sequence[Sequence[str]], binary, numeric):
    onehot = []
    for config in configs:
        c = {}
        for option in binary:
            c[option] = 1 if option in config else 0

        for option in numeric:
            num_value = [opt for opt in config if option in opt]
            if len(num_value):
                c[option] = float(num_value[0].split(";")[1])

        onehot.append(c)

    return onehot


class Sampler:
    def __init__(self, vm: ET):
        self.vm = vm
        self.splc = _splc.SplcExecutor()
        self.numeric = _get_numeric_features(vm)
        self.binary = _get_binary_features(vm)

    def _serialize_data(self, cache_dir: str = None):

        self.vm.write(os.path.join(cache_dir, "vm.xml"))
        with open(os.path.join(cache_dir, "script.a"), "w") as f:
            f.write(self.script)

    def _transform_sample(self, cache_dir: str, format: str = "list"):
        with open(os.path.join(cache_dir, "sampled.txt"), "r") as f:
            samples = f.readlines()

        configs = [_extract_options(config) for config in samples]
        if format == "dict":
            configs = _list_to_dict(configs, self.binary, self.numeric)
        return configs

    def sample(
        self,
        binary: str = "allbinary",
        numeric: str = None,
        format: str = "list",
        params=None,
    ):
        # Generate strings for sampling strategies
        binString = binaryStrategyString(binary, params)
        numString = numericStrategyString(numeric, params) if numeric else None

        # Generate script
        self.script = _splc.generate_script(
            binary=binString,
            numeric=numString,
        )

        # serialize data and script in tempdir and execute splc
        with tempfile.TemporaryDirectory() as tmpdir:
            self._serialize_data(tmpdir)
            self.splc.execute(tmpdir)

            # extract sampled configurations
            configs = self._transform_sample(tmpdir, format)

        return configs
