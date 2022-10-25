import math
import tempfile
import logging

import pandas as pd
from splc2py import _preprocess, _splc, _logs


class Model:
    def __init__(self):
        self.fitted = False

    def fit(self, measurements, nfp, mlsettings):
        vm, measurements = _preprocess.prepare_learning_data(measurements, nfp)

        params = {
            "vm.xml": vm,
            "measurements.xml": measurements,
            "script.a": _splc.generate_script(
                learning=True,
                mlsettings_pwd="/application/data/mlsettings.txt",
                nfp=nfp,
            ),
            "mlsettings.txt": _splc.generate_mlsettings(mlsettings),
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            _preprocess.serialize_data(tmpdir, params)
            splc = _splc.SplcExecutor()
            splc.execute(tmpdir)
            self.model, self.learnHistory = _logs.extract_model(tmpdir)
        self.fitted = True

    def to_string(self):
        if not self.fitted:
            logging.error("No model fitted yet.")
            raise Exception
        else:
            return " + ".join(
                [
                    str(t["coefficient"]) + " * " + " * ".join(t["options"])
                    for t in self.model
                ]
            )

    def _calculate_prediction(self, x):
        interim = []
        for term in self.model:
            options = math.prod([x[option] for option in term["options"]])
            interim.append(term["coefficient"] * options)
        return sum(interim)

    def predict(self, X: pd.DataFrame):
        if not self.fitted:
            logging.error("No model fitted yet.")
            raise Exception
        else:
            if "root" not in X:
                X = X.copy()
                X["root"] = 1
            result = X.apply(self._calculate_prediction, axis=1)
            if len(result) == 1:
                return result[0]
            else:
                return result
