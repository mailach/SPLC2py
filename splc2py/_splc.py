import os
import docker


def generate_script(binary: str = None, numeric: str = None):
    script = f"log /application/data/logs.txt\nvm /application/data/vm.xml\nall /application/data/measurements.xml\n"
    if binary:
        script += f"binary {binary}\n"
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
