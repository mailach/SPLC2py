from typing import Dict, Sequence
import docker


def generate_mlsettings(settings: Sequence[Dict[str, any]]):
    settings = [k + " " + str(v) for k, v in settings.items()]
    return "\n".join(settings)


def generate_script(
    binary: str = None,
    numeric: str = None,
    learning: str = None,
    mlsettings_pwd: str = None,
    nfp: str = None,
    solver: str = None,
):
    script = f"log /application/data/logs.txt\n"
    script += "vm /application/data/vm.xml\n"
    if binary:
        script += f"binary {binary}\n"
    if numeric:
        script += f"numeric {numeric}\n"
    if learning:
        script += f"load-mlsettings {mlsettings_pwd}\n"
        script += f"nfp {nfp}\n"
        script += "all /application/data/measurements.xml\n"
        if not numeric and not binary:
            script += "select-all-measurements true\n"
        script += "learn-splconqueror\nanalyze-learning\n"

    if solver:
        script += f"solver {solver}\n"
    script += f"printconfigs /application/data/sampled.txt\n"

    return script


class SplcExecutor:
    def __init__(self):
        self.client = docker.from_env()

    def execute(self, mount_path: str):

        cmd = "mono SPLConqueror/SPLConqueror/CommandLine/bin/Release/CommandLine.exe /application/data/script.a"
        self.client.containers.run(
            image="mailach/splc",
            command=cmd,
            remove=True,
            volumes=[f"{mount_path}:/application/data"],
        )
        return mount_path
