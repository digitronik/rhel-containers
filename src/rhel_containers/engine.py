import datetime
import json
import shutil
import subprocess


class ContCommandResult:
    """A representation engine command results."""

    def __init__(self, exit_status=None, stdout=None, stderr=None, command=None):
        self.exit_status = exit_status
        self.stdout = stdout
        self.stderr = stderr
        self.command = command

    @classmethod
    def from_subprocess_out(cls, sub_out):
        stdout = sub_out.stdout.decode().strip() if sub_out.stdout else ""
        stderr = sub_out.stderr.decode().strip() if sub_out.stderr else ""
        command = " ".join(sub_out.args)

        # TODO: Add logging
        if sub_out.returncode != 0 and stderr:
            print(f"Error: {command} >> {stderr}")

        return cls(exit_status=sub_out.returncode, stdout=stdout, stderr=stderr, command=command,)

    def __repr__(self):
        return f"ContCommandResult(exit_status={self.exit_status})"


class PodmanEngine:
    """Podman/Docker engine wrapper."""

    def __init__(self, name=None, engine="auto", *args, **kwargs):
        if engine == "auto":
            self.engine = "podman" if shutil.which("podman") else "docker"
        else:
            self.engine = engine

        # check engine exist or not
        if shutil.which(self.engine) is None:
            raise ValueError(
                f"'{engine}' engine not found. Make sure it should installed on your system."
            )
        self.name = name or f"rhel-{datetime.datetime.now().strftime('%y%m%d-%H%M%S')}"

    def _exec(self, command):
        """Internal use to execute subprocess cmd."""
        out = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return ContCommandResult.from_subprocess_out(out)

    def run(self, image, hostname=None, envs=None, *args, **kwargs):
        """run container.
        Args:
            image: Image of rhel container
            hostname: Set container hostname
            env: List of environment variables to set in container
        """
        cmd = [self.engine, "run", "--name", self.name, "--rm", "-d"]

        if hostname:
            cmd.extend(["--hostname", hostname])
        if envs:
            cmd.extend(["--env", " ".join(envs)])

        cmd.extend([image])
        return self._exec(cmd)

    def kill(self):
        """Kill running container."""
        return self._exec([self.engine, "kill", self.name])

    def rm(self):
        """Remove container."""
        return self._exec([self.engine, "rm", self.name])

    def stop(self):
        """Stop container."""
        return self._exec([self.engine, "stop", self.name])

    def exec(self, cmd):
        """Execute command on contaienr.

        Args:
            cmd: command string
        """
        command = [self.engine, "exec", self.name, "bash", "-c", cmd]
        return self._exec(command)

    def cp(self, source, dest):
        """Copy file from sorce to destination.

        Args:
            source: sorce path
            dest: destination path
        """
        command = [self.engine, "cp", source, dest]
        return self._exec(command)

    def add_file(self, filename, content, overwrite=False):
        if not overwrite:
            self.exec(f"rm {filename}")
        return self.exec(f"cat >>{filename} <<EOF\n{content}\nEOF")

    @property
    def status(self):
        """Return status of container."""
        command = [self.engine, "inspect", "--format", "{{.State.Status}}", self.name]
        out = self._exec(command=command)
        if out.exit_status != 0:
            return f"{self.name} unavailable."
        return out.stdout.title()


class OpenshiftEngine:
    """Openshift/k8s engine wrapper."""

    def __init__(self, name=None, engine="auto", *args, **kwargs):
        if engine == "auto":
            self.engine = "oc" if shutil.which("oc") else "kubectl"
        else:
            self.engine = engine

        # check engine exist or not
        if shutil.which(self.engine) is None:
            raise ValueError(
                f"'{engine}' engine not found. Make sure it should installed on your system."
            )
        self.name = name or f"rhel-{datetime.datetime.now().strftime('%y%m%d-%H%M%S')}"

    def _exec(self, command):
        """Internal use to execute subprocess cmd."""
        out = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return ContCommandResult.from_subprocess_out(out)

    def run(self, image, hostname=None, envs=None, *args, **kwargs):
        """run container.
        Args:
            hostname: Set container hostname
            env: dict of environment variables to set in container
        """
        cmd = [self.engine, "run", self.name]

        if envs:
            cmd.extend([f"--env='{k}={v}'" for k, v in envs.items()])

        cmd.extend([f"--image={image}"])
        if hostname:
            cmd.extend([f"--overrides={{'spec': {{'hostname': '{hostname}'}}"])
        return self._exec(cmd)

    def stop(self):
        """Delete container than stopping."""
        return self._exec([self.engine, "delete", "pod", self.name])

    def exec(self, cmd):
        """Execute command on contaienr.

        Args:
            cmd: command string
        """
        command = [self.engine, "exec", self.name, "--", "bash", "-c", cmd]
        return self._exec(command)

    def cp(self, source, dest):
        """Copy file from sorce to destination.

        Args:
            source: sorce path
            dest: destination path
        """
        command = [self.engine, "cp", source, dest]
        return self._exec(command)

    def add_file(self, filename, content, overwrite=False):
        if not overwrite:
            self.exec(f"rm {filename}")
        return self.exec(f"cat >>{filename} <<EOF\n{content}\nEOF")

    def get_json(self, restype, name=None, label=None, namespace=None):
        """
        Get json for resource type/name/label.
        If name is None all resources of this type are returned
        If label is not provided, then "oc get" will not be filtered on label
        """
        command = [self.engine, "get", restype]
        if name:
            command.append(name)
        if label:
            command.extend(["-l", label])
        if namespace:
            command.extend(["-n", namespace])

        command.extend(["-o", "json"])
        out = self._exec(command=command)

        if out.exit_status != 0:
            return {}
        try:
            return json.loads(out.stdout)
        except ValueError:
            return {}

    @property
    def status(self):
        """Return status of pod."""
        out = self.get_json(restype="pods", name=self.name)
        if not out:
            return f"{self.name} unavailable."
        return out["status"]["phase"]
