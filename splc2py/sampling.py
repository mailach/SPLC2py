import logging
import tempfile
import os


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
        "negfeaturwise": _negfeaturewise,
        "distance-based": _distancebased,
        "twise": _twise,
    }
    return binStrategies[method](params)


class BinarySampler:
    def __init__(self, vm: ET, measurements: ET):
        self.vm = vm
        self.measurements = measurements
        self.splc = _splc.SplcExecutor()

    def _serialize_data(self, cache_dir: str = None):

        self.vm.write(os.path.join(cache_dir, "vm.xml"))
        self.measurements.write(os.path.join(cache_dir, "measurements.xml"))
        with open(os.path.join(cache_dir, "script.a"), "w") as f:
            f.write(self.script)
        return cache_dir

    def sample(self, method: str, cache_dir: str = None):
        if not cache_dir:
            cache_dir = tempfile.mkdtemp()
        self.script = _splc.generate_script(binary=binaryStrategyString(method))
        cache_dir = self._serialize_data(cache_dir)
        self.splc.execute(cache_dir)
        print(cache_dir)
