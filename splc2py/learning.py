import os
import uuid
import tempfile
import logging
from functools import reduce
import operator

import pandas as pd
from splc2py import _preprocess, _splc, _logs


class Model:
    def __init__(self, backend):
        self.fitted = False
        self.model = None
        self.learn_history = None
        self.artifact_repo = None
        self.splc = _splc.SplcExecutorFactor(backend)

    def fit(self, measurements, nfp, mlsettings):
        vm, measurements = _preprocess.prepare_learning_data(measurements, nfp)
        self.artifact_repo = os.path.join(tempfile.gettempdir(), uuid.uuid4().hex)
        os.mkdir(self.artifact_repo)

        params = {
            "vm.xml": vm,
            "measurements.xml": measurements,
            "script.a": _splc.generate_script(
                path=self.artifact_repo,
                learning=True,
                mlsettings_pwd=f"{self.artifact_repo}/mlsettings.txt",
                nfp=nfp,
            ),
            "mlsettings.txt": _splc.generate_mlsettings(mlsettings),
        }

        _preprocess.serialize_data(self.artifact_repo, params)
        self.splc.execute(self.artifact_repo)
        self.model, self.learn_history = _logs.extract_model(self.artifact_repo)
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
            options = reduce(operator.mul, [x[option] for option in term["options"]], 1)
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
