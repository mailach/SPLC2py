import logging
import tempfile

from typing import Sequence
import xml.etree.ElementTree as ET


from splc2py import _preprocess, _splc, _logs


def _distancebased(params):
    try:
        db = f"distance-based optionWeight:{params['optionWeight']} numConfigs:{params['numConfigs']}"
    except:
        logging.error(
            "For using distance-based sampling you need to specify numConfigs and optionWeight."
        )
        raise
    return db


def _twise(params):
    try:
        t = f"twise t:{params['t']}"
    except:
        logging.error("For using twise sampling you need to specify t.")
        raise
    return t


def binary_strategy_string(method: str, params=None):
    bin_strategies = {
        "featurewise": "featurewise",
        "pairwise": "pairwise",
        "negfw": "negfw",
        "distance-based": _distancebased,
        "twise": _twise,
        "allbinary": "allbinary",
    }

    if isinstance(bin_strategies[method], str):
        return bin_strategies[method]

    return bin_strategies[method](params)


def _random(params):
    try:
        r = f"random sampleSize:{params['sampleSize']} seed:{params['seed']}"
    except:
        logging.error(
            "For using random sampling you need to specify sampleSize and seed."
        )
        raise
    return r


def _hypersampling(params):
    try:
        r = f"hypersampling precision:{params['precision']}"
    except:
        logging.error("For using hypersampling you need to specify precision.")
        raise
    return r


def _onefactoratatime(params):
    try:
        r = f"onefactoratatime distinctValuesPerOption:{params['distinctValuesPerOption']}"
    except:
        logging.error(
            "For using onefactoratatime you need to specify distinctValuesPerOption."
        )
        raise
    return r


def _plackettburman(params):
    try:
        pb = f"plackettburman measurements:{params['measurements']} level:{params['level']}"
    except:
        logging.error(
            "For using placketburman desing you need to specify measurements and level."
        )
        raise
    return pb


def _kexchange(params):
    try:
        k = f"kexchange sampleSize:{params['sampleSize']} k:{params['k']}"
    except:
        logging.error(
            "For using kexchange sampling you need to specify sampleSize and level."
        )
        raise
    return k


def numeric_strategy_string(method: str, params=None):
    numeric_strategies = {
        "random": _random,
        "centralcomposite": "centralcomposite",
        "plackettburman": _plackettburman,
        "fullfactorial": "fullfactorial",
        "boxbehnken": "boxbehnken",
        "hypersampling": _hypersampling,
        "onefactoratatime": _onefactoratatime,
        "kexchange": _kexchange,
    }

    if isinstance(numeric_strategies[method], str):
        return numeric_strategies[method]

    return numeric_strategies[method](params)


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
    def __init__(self, vm: ET, backend: str):

        self.vm = vm
        self.splc = _splc.SplcExecutorFactor(backend)
        self.numeric = _get_numeric_features(vm)
        self.binary = _get_binary_features(vm)

    def sample(
        self,
        binary: str = "allbinary",
        numeric: str = None,
        formatting: str = "list",
        params=None,
    ):
        # Generate strings for sampling strategies
        bin_string = binary_strategy_string(binary, params)
        num_string = numeric_strategy_string(numeric, params) if numeric else None

        # Generate script

        # serialize data and script in tempdir and execute splc
        with tempfile.TemporaryDirectory() as tmpdir:
            print(tmpdir)
            script = _splc.generate_script(
                path=tmpdir,
                binary=bin_string,
                numeric=num_string,
            )
            _preprocess.serialize_data(tmpdir, {"vm.xml": self.vm, "script.a": script})
            self.splc.execute(tmpdir)

            # extract sampled configurations
            configs = _logs.extract_samples(tmpdir)
            if formatting == "dict":
                configs = _list_to_dict(configs, self.binary, self.numeric)

        return configs
