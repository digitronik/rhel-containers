import datetime
import re
import shutil
import subprocess

from packaging import version
from rhel_containers.config import load_config
from rhel_containers.engine import PodmanEngine
from rhel_containers.insights_client import InsightsClient
from rhel_containers.subscription import Subscription

EPEL_URL = "https://dl.fedoraproject.org/pub/epel/epel-release-latest-{major_ver}.noarch.rpm"
SUPPORTED_ENV = ("ci", "qa", "prod")


class RhelContainer:
    def __init__(self, engine_name="auto", release=8.3, name=None, env="qa", *args, **kwargs):
        self.engine_name = engine_name
        self.version = version.parse(str(release))
        self.name = name or f"rhel-{datetime.datetime.now().strftime('%y%m%d-%H%M%S')}"
        self.env = env
        self.config = load_config(env=self.env, extra_conf=kwargs.get("config"))

        # Engine
        self.engine = PodmanEngine(name=self.name, engine=engine_name)

        # Subscription
        self.subscription = Subscription(
            engine=self.engine,
            username=kwargs.get("username"),
            password=kwargs.get("password"),
            config=self.config,
            env=self.env,
        )

        # Insights-client
        self.insights_client = InsightsClient(engine=self.engine, config=self.config, env=self.env)

        # check for env
        assert (
            self.env in SUPPORTED_ENV
        ), f"'{self.env}' not supported. Supported env are {SUPPORTED_ENV}"

    def start(self, hostname=None, detach=True, env=None):
        """Start container.
        Args:
            hostname: Set container hostname
            detach: Run container in background
            env: List of environment variables to set in container
        """
        repo = self.config.repositories.get(self.version.major)
        image = f"{repo}:{self.version.base_version}"
        return self.engine.run(image=image, hostname=hostname, detach=detach, env=env)

    def stop(self):
        """Stop container."""
        return self.engine.stop()

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
        return self.exec("hostname").stdout

    @property
    def redhat_release(self):
        """It will return redhat-release"""
        out = self.exec("cat /etc/redhat-release")
        return out.stdout

    def install(self, pkg):
        """Install package on container.

        Args:
            pkg: Package to install
        """
        return self.engine.install_pkg(pkg=pkg)

    def is_pkg_installed(self, pkg):
        """Check specific package already installed or not.

        Args:
            pkg: package name
        """
        return self.engine.is_pkg_installed(pkg=pkg)

    def enable_epel(self):
        """Enable EPEL repository on container."""
        epel = EPEL_URL.format(major_ver=self.version.major)
        epel_status = self.install(epel)

        # RHEL 7 it is recommended to also enable the optional, extras, and
        # HA repositories since EPEL packages may depend on packages from these repositories
        if self.version.major == 7:
            self.exec(
                'subscription-manager repos --enable "rhel-*-optional-rpms" --enable '
                '"rhel-*-extras-rpms"  --enable "rhel-ha-for-rhel-*-server-rpms"'
            )

        # RHEL 8 it is required to also enable the codeready-builder-for-rhel-8-*-rpms repository since EPEL packages may depend on packages from it
        if self.version.major == 8:
            arch = self.exec("/bin/arch")
            self.exec(
                f'subscription-manager repos --enable "codeready-builder-for-rhel-8-{arch}-rpms"'
            )
            # self.exec("dnf config-manager --set-enabled powertools")

    def copy_to_cont(self, host_path, cont_path):
        """Copy file from host to container.

        Args:
            host_path: File path on host intended to copy.
            cont_path: Path on container to save
        """
        return self.engine.copy_to_cont(host_path=host_path, cont_path=cont_path)

    def copy_to_host(self, cont_path, host_path):
        """Copy file from container to host.

        Args:
            host_path: Path on host to save
            cont_path: File path on container intended to copy.
        """
        return self.engine.copy_to_host(host_path=host_path, cont_path=cont_path)

    def create_archive(self, hostpath="."):
        """Create archive of container.

        Args:
            hostpath: Path to save
        """
        out = self.insights_client.register(keep_archive=True)
        archive_path = re.search("[^ ]*.tar.gz", out.stdout)[0]
        return self.copy_to_host(host_path=hostpath, cont_path=archive_path)
