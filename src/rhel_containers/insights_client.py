BASE_URL = "http://cdn.redhat.com/"
CI_API_ENTRYPOINT = "ci.cloud.redhat.com/api"
QA_API_ENTRYPOINT = "qa.cloud.redhat.com/api"
CONF_PATH = "/etc/insights-client/insights-client.conf"
INSIGHTS_CLIENT_CONF = """[insights-client]
base_url= {base_url}
cert_verify=False
auto_config=False
legacy_upload=False
authmethod=CERT"""


class InsightsClient:
    def __init__(self, engine, env="qa"):
        self.engine = engine
        self.env = env

    def install(self, pkg="insights-client"):
        """Install insights-client packges

        Args:
            pkg: insights-client package with specific version.
        """
        self.engine.install_pkg(pkg)

    def configure(self):
        if self.env == "prod":
            print("For prod env no need of config.")
            return
        base_url = QA_API_ENTRYPOINT if self.env == "qa" else CI_API_ENTRYPOINT
        conf = INSIGHTS_CLIENT_CONF.format(base_url=base_url)
        return self.engine.add_file(CONF_PATH, content=conf)

    def register(self, disable_schedule=None, keep_archive=None, no_upload=None):
        cmd = "insights-client --register"
        if disable_schedule:
            cmd = f"{cmd} --disable-schedule"
        if keep_archive:
            cmd = f"{cmd} --keep-archive"
        if no_upload:
            cmd = f"{cmd} --no-upload"

        # In rhel container sometime hostname pkg missing and insights-client need this package.
        if not self.engine.is_pkg_installed("hostname"):
            self.engine.install_pkg("hostname")

        # If insights-client not installed then installed it first.
        if not self.engine.is_pkg_installed("insights-client"):
            self.install()

        return self.engine.exec(cmd)

    def unregister(self):
        return self.engine.exec("insights-client --unregister")

    @property
    def version(self):
        return self.engine.exec("insights-client --version")
