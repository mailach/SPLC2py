from typing import Dict, Sequence
import docker
from abc import ABC, abstractmethod
import subprocess


def generate_mlsettings(settings: Sequence[Dict[str, any]]):
    settings = [k + " " + str(v) for k, v in settings.items()]
    return "\n".join(settings)


def generate_script(
    path: str,
    binary: str = None,
    numeric: str = None,
    learning: str = None,
    mlsettings_pwd: str = None,
    nfp: str = None,
    solver: str = None,
):
    script = f"log {path}/logs.txt\n"
    script += f"vm {path}/vm.xml\n"
    if binary:
        script += f"binary {binary}\n"
    if numeric:
        script += f"numeric {numeric}\n"
    if learning:
        script += f"load-mlsettings {mlsettings_pwd}\n"
        script += f"nfp {nfp}\n"
        script += f"all {path}/measurements.xml\n"
        if not numeric and not binary:
            script += "select-all-measurements true\n"
        script += "learn-splconqueror\nanalyze-learning\n"

    if solver:
        script += f"solver {solver}\n"
    script += f"printconfigs {path}/sampled.txt\n"

    return script


class SplcExecutor(ABC):
    @abstractmethod
    def execute(self, mount_path: str):
        pass


class DockerSplcExecutor:
    def __init__(self):
        self.client = docker.from_env()

    def execute(self, mount_path: str):

        cmd = f"mono /application/SPLConqueror/SPLConqueror/CommandLine/bin/Release/CommandLine.exe {mount_path}/script.a"
        self.client.containers.run(
            image="mailach/splc",
            command=cmd,
            remove=True,
            volumes=[f"{mount_path}:{mount_path}"],
        )
        return mount_path


class LocalSplcExecutor:
    def execute(self, mount_path: str):
        cmd = [
            "mono",
            "/application/SPLConqueror/SPLConqueror/CommandLine/bin/Release/CommandLine.exe",
            f"{mount_path}/script.a",
        ]
        subprocess.run(cmd, check=True)
        return mount_path


def SplcExecutorFactor(backend: str):
    executors = {"docker": DockerSplcExecutor, "local": LocalSplcExecutor}
    return executors[backend]()
