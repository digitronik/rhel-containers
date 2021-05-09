import re
import shutil
import subprocess

from packaging import version
from rhel_containers.engine import PodmanEngine
from rhel_containers.insights_client import InsightsClient
from rhel_containers.subscription import Subscription

REPOS = {
    7: "registry.access.redhat.com/ubi7/ubi-init",
    8: "registry.access.redhat.com/ubi8/ubi-init",
}


class RhelContainer:
    def __init__(self, engine_name="auto", release=8.0, name=None, *args, **kwargs):
        # engine
        self.engine_name = engine_name
        self.version = version.parse(str(release))
        self.image = f"{REPOS[self.version.major]}:{self.version.base_version}"
        self.name = name or f"rhel-{self.version}"
        self.engine = PodmanEngine(image=self.image, name=self.name, engine=engine_name)

        # Subscription
        self.env = kwargs.get("env", "qa")
        self.subscription = Subscription(
            engine=self.engine,
            username=kwargs.get("username"),
            password=kwargs.get("password"),
            env=self.env,
        )
        self.insight_client = InsightsClient(engine=self.engine, env=self.env)

    def exec(self, cmd):
        """Execute command on contaienr.

        Args:
            cmd: command string
        """
        return self.engine.exec(cmd=cmd)

    @property
    def hostname(self):
        """It will give you current hostname."""
        # In rhel container sometime hostname pkg missing.
        if not self.engine.is_pkg_installed("hostname"):
            self.engine.install_pkg("hostname")
        return self.exec("hostname")

    @property
    def redhat_release(self):
        """It will return redhat-release"""
        return self.exec("cat /etc/redhat-release")

    def install(self, pkg):
        """Install package/s on container."""
        return self.exec(f"yum install -y {pkg}")

    def is_pkg_installed(self, pkg):
        """Check specific package already installed or not."""
        return "not installed" not in self.exec(f"rpm -q {pkg}")

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
        subprocess.run(command)

    def enable_epel(self):
        epel = EPEL_URL.format(major_ver=self.version.major)
        self.install(epel)
        # RHEL 7 it is recommended to also enable the optional, extras, and
        # HA repositories since EPEL packages may depend on packages from these repositories
        if self.version.major == 7:
            self.exec(
                'subscription-manager repos --enable "rhel-*-optional-rpms" --enable "rhel-*-extras-rpms"  --enable "rhel-ha-for-rhel-*-server-rpms"'
            )

        # RHEL 8 it is required to also enable the codeready-builder-for-rhel-8-*-rpms repository since EPEL packages may depend on packages from it
        if self.version.major == 8:
            arch = self.exec("/bin/arch")
            self.exec(
                f'subscription-manager repos --enable "codeready-builder-for-rhel-8-{arch}-rpms"'
            )
            self.exec("dnf config-manager --set-enabled powertools")

    def copy_to_rhel(self, rhel_path, host_path):
        command = [self.engine, "cp", host_path, f"{self.name}:{rhel_path}"]
        return subprocess.run(command).returncode

    def copy_to_host(self, host_path, rhel_path):
        command = [self.engine, "cp", f"{self.name}:{rhel_path}", host_path]
        return subprocess.run(command).returncode

    def create_archive(self, hostpath="."):
        out = self.insight_client.register(keep_archive=True)
        archive_path = re.search("[^ ]*.tar.gz", out)[0]
        self.copy_to_host(host_path=hostpath, rhel_path=archive_path)
