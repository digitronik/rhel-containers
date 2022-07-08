import logging
import random
import re
import string
from pathlib import Path

from packaging import version
from rhel_containers.config import load_config
from rhel_containers.engine import ContCommandResult
from rhel_containers.engine import OpenshiftEngine
from rhel_containers.engine import PodmanEngine
from rhel_containers.insights_client import InsightsClient
from rhel_containers.subscription import Subscription
from wait_for import TimedOutError
from wait_for import wait_for

EPEL_URL = "https://dl.fedoraproject.org/pub/epel/epel-release-latest-{major_ver}.noarch.rpm"
SUPPORTED_ENV = ("ci", "qa", "prod", "stage")
SUPPORTED_ORCHESTRATION_CLI = ("kubectl", "oc")
SUPPORTED_ENGINE_CLI = ("podman", "docker", "kubectl", "oc")

logger = logging.getLogger(__name__)


class RhelContainer:
    def __init__(self, engine_name="podman", release=8.3, name=None, env="qa", *args, **kwargs):
        self.engine_name = engine_name
        self.release = str(release)
        self.version = version.parse(self.release)
        self.name = name or f"rhel-{''.join(random.choice(string.ascii_letters).lower() for _ in range(5))}"
        self.env = env
        self.config = load_config(env=self.env, extra_conf=kwargs.get("config"))

        # Engine
        self.engine = (
            OpenshiftEngine(name=self.name, engine=engine_name)
            if engine_name in SUPPORTED_ORCHESTRATION_CLI
            else PodmanEngine(name=self.name, engine=engine_name)
        )

        # Subscription
        self.subscription = Subscription(
            engine=self.engine, config=self.config.subscription, env=self.env,
        )

        # Insights-client
        self.insights_client = InsightsClient(
            engine=self.engine, config=self.config.insights_client, env=self.env
        )

        # check for engine
        assert (
            self.engine_name in SUPPORTED_ENGINE_CLI
        ), f"'{self.engine_name}' not supported. Supported CLI are {SUPPORTED_ENGINE_CLI}"

        # check for env
        assert (
            self.env in SUPPORTED_ENV
        ), f"'{self.env}' not supported. Supported env are {SUPPORTED_ENV}"

    def start(self, hostname=None, envs=None, wait=True, *args, **kwargs):
        """Start container.

        Args:
            hostname: Set container hostname
            env: List of environment variables to set in container
            wait: wait for container/pod up and running.
        """
        logger.info(f"Provisioning RHEL-{self.version} container")
        repo = self.config.repositories.get(self.version.major)
        image = f"{repo}:{self.release}"
        out = self.engine.run(image=image, hostname=hostname, envs=envs, *args, **kwargs)
        if wait:
            try:
                wait_for(lambda: self.status == "Running", timeout="60s")
            except TimedOutError:
                print("Pod are not Running.")

        if out.exit_status == 0:
            logger.info("Successfully provisioned container")
        else:
            logger.error(f"Fail to provision container: {out.stderr}")
        return out

    def stop(self):
        """Stop container."""
        logger.info("Stopping container")
        return self.engine.stop()

    @property
    def status(self):
        """Return status of container."""
        return self.engine.status

    def exec(self, cmd):
        """Execute command on container.

        Args:
            cmd: command string
        """
        return self.engine.exec(cmd=cmd)

    @property
    def hostname(self):
        """It will give you current hostname."""
        # In rhel container sometime hostname pkg missing.
        if not self.is_pkg_installed("hostname"):
            self.install("hostname")
        return self.exec("hostname").stdout

    @property
    def pkg_mng(self):
        return "dnf" if self.version.major == 8 else "yum"

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
        return self.engine.exec(f"{self.pkg_mng} install -y {pkg}")

    def remove(self, pkg):
        """remove package on container.

        Args:
            pkg: Package to remove
        """
        return self.engine.exec(f"{self.pkg_mng} remove -y {pkg}")

    def is_pkg_installed(self, pkg):
        """Check specific package already installed or not.

        Args:
            pkg: Package, which you want to verify.
        """
        out = self.engine.exec(f"which {pkg}")
        return not out.exit_status

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
            arch = self.exec("/bin/arch").stdout
            self.exec(
                f"subscription-manager repos --enable codeready-builder-for-rhel-8-{arch}-rpms"
            )
            # self.exec("dnf config-manager --set-enabled powertools")

    def copy_to_cont(self, host_path, cont_path):
        """Copy file from host to container.

        Args:
            host_path: File path on host intended to copy.
            cont_path: Path on container to save
        """
        return self.engine.cp(source=host_path, dest=f"{self.name}:{cont_path}")

    def copy_to_host(self, cont_path, host_path="."):
        """Copy file from container to host.

        Args:
            host_path: Path on host to save
            cont_path: File path on container intended to copy.
        """
        return self.engine.cp(source=f"{self.name}:{cont_path}", dest=host_path)

    def add_file(self, filename, content, overwrite=False):
        return self.engine.add_file(filename=filename, content=content, overwrite=overwrite)

    def create_archive(self, path="."):
        """Create archive of container.

        Args:
            hostpath: Path to save
        """
        host_path = Path(path)
        out = self.insights_client.register(keep_archive=True)
        archive_path = Path(re.search("[^ ]*.tar.gz", out.stdout)[0])
        if host_path.is_dir() and host_path.exists():
            host_path = host_path.joinpath(archive_path.name)
        return self.copy_to_host(
            host_path=host_path.absolute().__str__(), cont_path=archive_path.absolute().__str__()
        )

    def setup_python(self, python="3"):
        """Install python3"""
        if self.is_pkg_installed(f"python{python}"):
            logger.info(f"python{python} already installed.")
        else:
            self.install(f"python{python}")
            logger.info(f"Successfully installed python{python}")
        out = self.exec(f"python{python} -m pip install --upgrade pip setuptools wheel")
        if out.exit_status == 0:
            logger.info(f"Successfully setup python{python}")
        else:
            logger.error(f"Fail to setup python{python} >> {out.stderr}")
        return out

    def setup_ansible(self, setup_ssh=True):
        """Install ansible and setup ansible"""
        # check for python as we are going to use pip for installation
        logger.info("Started ansible setup")
        if self.is_pkg_installed("ansible"):
            logger.info(f"ansible already installed.")
            out = ContCommandResult(exit_status=0, stdout="ansible already installed")
        else:
            self.setup_python()
            if setup_ssh:
                self.install("openssh-server ed openssh-clients tlog glibc-langpack-en")
                self.exec("systemctl enable sshd")
                self.exec(
                    "sed -i 's/#Port.*$/Port 22/' /etc/ssh/sshd_config && chmod 775 /var/run && rm -f /var/run/nologin"
                )
            out = self.exec(
                "pip3 install --trusted-host pypi.org --trusted-host "
                "files.pythonhosted.org ansible"
            )
            logger.info("Successfully setup ansible")
        return out

    def setup(self, *args, **kwargs):
        if "subscribe" in args:
            out = self.subscription.register()
            return out

        if "insights-client" in args:
            for k, v in [
                ("subscription", "register"),
                ("insights_client", "install"),
                ("insights_client", "configure"),
                ("insights_client", "register"),
            ]:
                out = getattr(getattr(self, k), v)()
                if out.exit_status != 0:
                    return out
            return out
