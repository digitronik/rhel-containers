import datetime
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

        # TODO: Add logging
        if sub_out.returncode != 0:
            print(stderr)

        return cls(
            exit_status=sub_out.returncode,
            stdout=stdout,
            stderr=stderr,
            command=" ".join(sub_out.args),
        )

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

    def run(self, image, hostname=None, detach=True, env=None):
        """run container.
        Args:
            image: Image of rhel container
            hostname: Set container hostname
            detach: Run container in background
            env: List of environment variables to set in container
        """
        cmd = [self.engine, "run", "--name", self.name, "--rm"]

        if hostname:
            cmd.extend(["--hostname", hostname])
        if detach:
            cmd.extend(["-d"])
        if env:
            cmd.extend(["--env", " ".join(env)])

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
        command = [self.engine, "exec", self.name,] + cmd.split()
        return self._exec(command)

    def copy_to_cont(self, host_path, cont_path):
        """Copy file from host to container.

        Args:
            host_path: File path on host intended to copy.
            cont_path: Path on container to save
        """
        command = [self.engine, "cp", host_path, f"{self.name}:{cont_path}"]
        return self._exec(command)

    def copy_to_host(self, host_path, cont_path):
        """Copy file from container to host.

        Args:
            host_path: Path on host to save
            cont_path: File path on container intended to copy.
        """
        command = [self.engine, "cp", f"{self.name}:{cont_path}", host_path]
        return self._exec(command)

    def install_pkg(self, pkg):
        """Install package/s on container.

        Args:
            pkg: Package string
        """
        return self.exec(f"yum install -y {pkg}")

    def is_pkg_installed(self, pkg):
        """Check specific package already installed or not.

        Args:
            pkg: Package, which you want to verify.
        """
        return "not installed" not in self.exec(f"rpm -q {pkg}").stdout

    def add_file(self, filename, content, overwrite=False):
        if not overwrite:
            self.exec(f"rm {filename}")
        command = [
            self.engine,
            "exec",
            self.name,
            "bash",
            "-c",
            f"cat >>{filename} <<EOF\n{content}\nEOF",
        ]
        self._exec(command=command)
