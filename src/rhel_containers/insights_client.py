import logging

from rhel_containers.engine import ContCommandResult

logger = logging.getLogger(__name__)

INSIGHTS_CLIENT_CONF = """[insights-client]
base_url= {base_url}
cert_verify=False
auto_config=False
legacy_upload=False
authmethod=CERT"""


class InsightsClient:
    def __init__(self, engine, config, env="qa"):
        self._engine = engine
        self._config = config
        self.env = env

    def install(self, pkg="insights-client"):
        """Install insights-client packges

        Args:
            pkg: insights-client package with specific version.
        """
        logger.info(f"Installing {pkg}")
        return self._engine.exec(f"yum install -y {pkg}")

    @property
    def status(self):
        out = self._engine.exec("insights-client --status")
        return out.stdout

    def configure(self):
        logger.info(f"Configuring insights-client for '{self.env}' env.")
        if self.env == "prod":
            logger.info(f"Default setting selected for {self.env}")
            return ContCommandResult(exit_status=0, stdout="No need of configuration.")
        if self.env == "stage":
            conf = "[insights-client]"
            if self._config.proxy:
                conf = f"{conf}\nproxy={self._config.proxy}"
        else:
            conf = INSIGHTS_CLIENT_CONF.format(base_url=self._config.base_url)
        out = self._engine.add_file(self._config.conf_path, content=conf, overwrite=True)

        if out.exit_status != 0:
            logger.error(f"Fail to configure insights-client for env '{self.env}'\n {out.stderr}")
        else:
            logger.info(f"Successfully configured insights-client for '{self.env}' env.")
        return out

    def register(self, disable_schedule=None, keep_archive=None, no_upload=None):
        """Register insights-client.

        Args:
            disable_schedule: disable schedule
            keep_archive: Keep archive while uploading
            no_upload: don't upload data
        """
        logger.info("Registering insight client")
        cmd = "insights-client --register"
        if disable_schedule:
            cmd = f"{cmd} --disable-schedule"
        if keep_archive:
            cmd = f"{cmd} --keep-archive"
        if no_upload:
            cmd = f"{cmd} --no-upload"

        # In rhel container sometime hostname pkg missing and insights-client need this package.
        if "not installed" in self._engine.exec(f"rpm -q hostname").stdout:
            self._engine.exec("yum install -y hostname")

        # If insights-client not installed then installed it first.
        if "not installed" in self._engine.exec(f"rpm -q insights-client").stdout:
            self.install()

        out = self._engine.exec(cmd)
        if out.exit_status != 0:
            logger.error(f"Fail to register insights-client for env '{self.env}'\n {out.stderr}")
        else:
            logger.info(f"Successfully registered insights client.\n {out.stdout}")
        return out

    def unregister(self):
        out = self._engine.exec("insights-client --unregister")
        if out.exit_status != 0:
            logger.error(f"Fail to register insights-client for env '{self.env}'\n {out.stderr}")
        return out

    @property
    def version(self):
        out = self._engine.exec("insights-client --version")
        return out.stdout

    def test_connection(self):
        return self._engine.exec("insights-client --test-connection")
