import os
import math
import tempfile
import logging

import pandas as pd
from splc2py import _splc


class Model:
    def __init__(self):
        self.splc = _splc.SplcExecutor()
        self.fitted = False

    def _serialize_data(self, cache_dir: str = None):

        self.measurements.write(os.path.join(cache_dir, "measurements.xml"))
        self.vm.write(os.path.join(cache_dir, "vm.xml"))
        with open(os.path.join(cache_dir, "script.a"), "w") as f:
            f.write(self.script)
        with open(os.path.join(cache_dir, "mlsettings.txt"), "w") as f:
            f.write(self.mlsettings)

    def _generate_model(self, model):
        terms = model.split("+")
        return [
            {
                "coefficient": float(t.split(" * ")[0]),
                "options": t.strip().split(" * ")[1:],
            }
            for t in terms
        ]

    def _best_model(self, models):
        best = [float(models[0]["ValidationError"]), 0]
        for i in range(len(models)):
            if float(models[i]["ValidationError"]) < best[0]:
                best[0] = float(models[i]["ValidationError"])
                best[1] = i
        return models[best[1]]

    def _transform_logs(self, tmpdir):
        with open(os.path.join(tmpdir, "logs.txt"), "r") as f:
            logs = f.readlines()

        beginModels = logs.index("command: analyze-learning\n") + 1
        endModels = logs.index("Analyze finished\n")
        table = logs[beginModels:endModels]
        header = [h.strip() for h in table[0].split(",")]
        final = []
        for row in table[3:]:
            row = row.split(";")
            m = {}
            for i in range(len(row)):
                m[header[i]] = row[i]
            final.append(m)
        best = self._best_model(final)

        self.model = self._generate_model(best["Model"])
        self.learnHistory = final

    def fit(self, measurements, nfp, mlsettings):
        self.vm, self.measurements = _splc.pandas_to_xml(measurements, nfp)

        self.mlsettings = _splc.generate_mlsettings(mlsettings)
        self.script = _splc.generate_script(
            learning=True, mlsettings_pwd="/application/data/mlsettings.txt", nfp=nfp
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            self._serialize_data(tmpdir)
            self.splc.execute(tmpdir)
            self._transform_logs(tmpdir)
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
