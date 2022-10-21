import os
import tempfile

import xml.etree.ElementTree as ET
from splc2py import _splc


class Learner:
    def __init__(self, vm: ET, measurements: ET):
        self.vm = vm
        self.measurements = measurements
        self.splc = _splc.SplcExecutor()

    def _serialize_data(self, cache_dir: str = None):

        self.measurements.write(os.path.join(cache_dir, "measurements.xml"))
        self.vm.write(os.path.join(cache_dir, "vm.xml"))
        with open(os.path.join(cache_dir, "script.a"), "w") as f:
            f.write(self.script)
        with open(os.path.join(cache_dir, "mlsettings.txt"), "w") as f:
            f.write(self.mlsettings)

    def learn(self, nfp, mlsettings):
        self.mlsettings = _splc.generate_mlsettings(mlsettings)

        self.script = _splc.generate_script(
            learning=True, mlsettings_pwd="/application/data/mlsettings.txt", nfp=nfp
        )

        # with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = "/home/mailach/git/splc2py/tmp"
        if tmpdir:
            self._serialize_data(tmpdir)
            self.splc.execute(tmpdir)
            print(os.listdir(tmpdir))
