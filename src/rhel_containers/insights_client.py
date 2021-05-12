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
        self._engine.exec(f"yum install -y {pkg}")

    def configure(self):
        if self.env == "prod":
            print("For prod env no need of config.")
            return
        if self.env == "stage":
            conf = "[insights-client]"
            if self._config.proxy:
                conf = f"{conf}\nproxy={self._config.proxy}"
        else:
            conf = INSIGHTS_CLIENT_CONF.format(base_url=self._config.base_url)
        return self._engine.add_file(self._config.conf_path, content=conf)

    def register(self, disable_schedule=None, keep_archive=None, no_upload=None):
        """Register insights-client.

        Args:
            disable_schedule: disable schedule
            keep_archive: Keep archive while uploading
            no_upload: don't upload data
        """
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

        return self._engine.exec(cmd)

    def unregister(self):
        return self._engine.exec("insights-client --unregister")

    @property
    def version(self):
        out = self._engine.exec("insights-client --version")
        return out.stdout
