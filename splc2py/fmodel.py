from typing import Sequence

from splc2py._parsing import SplcFmParser


def _constr_to_clauses(constraints, features):
    final_constraints = []
    for constraint in constraints:
        # bring constraint to dimacs format
        constraint = constraint.replace("!", "-")
        constraint = constraint.replace(" | ", " ")
        constraint += " 0"

        # replace feature name with id
        for id_nr, feature in features.items():
            constraint = constraint.replace(feature, str(id_nr))

        # identify mandatory features and add constraints for the combination of each one
        # if constraint.count(" ") == 1:
        #     mand = constraint.split(" ")[0]
        #     final_constraints += [
        #         f"{mand} -{str(id_nr)} 0"
        #         for id_nr in features.keys()
        #         if str(id_nr) != mand
        #     ]
        final_constraints.append(constraint)

    return list(set(final_constraints))


def _generate_dimacs(binary: Sequence, constraints: Sequence[str]) -> str:
    features = {i + 1: binary[i] for i in range(len(binary))}

    lines = [f"c {str(k)} {v}" for k, v in features.items()]
    clauses = _constr_to_clauses(constraints, features)
    lines += [f"p cnf {len(lines)} {len(clauses)}"]
    lines += clauses
    return "\n".join(lines)


class FeatureModel:
    """
    A FeatureModel, consisting of different representations
    ...

    Attributes
    ----------
    binary : Sequence[str]
        binary options of fm
    numeric : Sequence[str]
        numeric options of fm
    constraints : Sequence[str]
        boolean constraints for binary options
    dimacs : str
        dimacs representation of binary options
    xml : xml.etree.ElementTree
        xm representation of fm


    Methods
    -------
    get_features():
        returns dict of binary and numeric features
    """

    def __init__(self, xml_file: str):
        self._parser = SplcFmParser()
        self.binary, self.numeric, self.constraints = self._parser.parse(xml_file)
        self.dimacs = _generate_dimacs(self.binary, self.constraints)
        self.xml = self._parser.get_xml()

    def get_features(self):
        """
        Return dictionary representation of features
        """
        return {"binary": self.binary, "numeric": self.numeric}
