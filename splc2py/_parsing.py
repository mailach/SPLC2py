import logging
from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET

import importlib.resources
import xmlschema

xsd_path = importlib.resources.path("splc2py.data", "schema_splc.xsd")


def _implication(option1, options):
    return [f"!{option1} | {opt}" for opt in options]


def _exclusion(option1, options, optional=None):
    simple_exclusion = [f"!{option1} | !{opt}" for opt in options]
    if optional == "True":
        return simple_exclusion
    return [" | ".join([option1] + options)] + simple_exclusion


def _optional(option):
    return [option]


class Parser(ABC):
    """
    Abstract Parser that implements standard functionalities all Parsers need.
    ...

    Attributes
    ----------
    schema : xmlschema.XMLSchema
        the schema used by the instance.
    decoded_xml: dict
        the last decoded xml, returned from parsing with the schema

    Methods
    -------
    get_xml():
        Encodes last parsed file as xml.etree.ElemetTree

    parse():
        Abstract method implemented by subclasses
    """

    schema: xmlschema.XMLSchema = None
    decoded_xml: dict = None

    def _validate_and_decode(self, xml_file: str):
        try:
            self.schema.validate(xml_file)
        except Exception:
            logging.error("The provided xml file is not valid vm format.")
            raise
        self.decoded_xml = self.schema.decode(xml_file)

    def get_xml(self):
        """
        Encodes last parsed file as xml.etree.ElemetTree
        """
        return ET.ElementTree(self.schema.encode(self.decoded_xml))

    @abstractmethod
    def parse(self, xml_file):
        """
        Keyfunctionality every Parser-Subclass should implement
        """


class FmParser(Parser):

    """
    Abstract parser for feature models.
    """

    @abstractmethod
    def _extract_binaries(self):
        pass

    @abstractmethod
    def _extract_bool_constraints(self):
        pass


class SplcFmParser(FmParser):
    """
    Parser to validate and parse feature models in the SPLC xml format.

    Methods
    -------
    parse():
        Parses feature model and returns features and constraints.
    """

    def __init__(self):
        self.schema = xmlschema.XMLSchema("splc2py/data/schema_splc.xsd")

    def _extract_binaries(self):
        binaries = []
        constraints = []
        binary_options = self.decoded_xml["binaryOptions"]["configurationOption"]
        for bo in binary_options:
            binaries.append(bo["name"])
            if bo["impliedOptions"]:
                constraints += _implication(bo["name"], bo["impliedOptions"]["option"])
            if bo["excludedOptions"]:
                constraints += _exclusion(
                    bo["name"], bo["excludedOptions"]["option"], bo["optional"]
                )
            if bo["optional"] == "False":
                constraints += _optional(bo["name"])
        return binaries, constraints

    def _extract_numerics(self):
        if not self.decoded_xml["numericOptions"]:
            return []

        numerics = []
        numeric_options = self.decoded_xml["numericOptions"]["configurationOption"]
        for num_opt in numeric_options:
            numerics.append(num_opt["name"])
        return numerics

    def _extract_bool_constraints(self):
        if self.decoded_xml["booleanConstraints"]:
            return [c for c in self.decoded_xml["booleanConstraints"]["constraint"]]
        return []

    def parse(self, xml_file: str):
        self._validate_and_decode(xml_file)
        binaries, constraints = self._extract_binaries()
        numerics = self._extract_numerics()
        constraints += self._extract_bool_constraints()
        return binaries, numerics, constraints


class MeasurementParser(Parser):
    """
    Abstract parser for measurements.
    """

    @abstractmethod
    def _extract_rows(self):
        pass


class SplcMeasurementParser(MeasurementParser):
    """
    Parser to validate and parse measurements in the SPLC xml format.

    Methods
    -------
    parse():
        Parses measurements and returns rows with data.
    """

    def __init__(self):
        self.schema = xmlschema.XMLSchema(xsd_path)

    def _extract_rows(self):
        rows = []
        for row in self.decoded_xml["row"]:
            config = {"nfp": {}}
            for column in row["data"]:
                if column["@column"] == "Configuration":
                    config["binaries"] = column["$"].replace("\n", "")
                elif column["@column"] == "Variable Features":
                    config["numerics"] = column["$"].replace("\n", "")
                else:
                    config["nfp"][column["@column"]] = column["$"].replace("\n", "")
            rows.append(config)

        return rows

    def parse(self, xml_file):
        self._validate_and_decode(xml_file)
        return self._extract_rows()
