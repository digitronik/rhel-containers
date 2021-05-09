# RHEL Subscription management.
QA_SERVER_URL = "subscription.rhsm.qa.redhat.com"
PROD_SERVER_URL = "subscription.rhsm.redhat.com"
BASE_URL = "http://cdn.redhat.com/"


class Subscription:
    def __init__(self, engine, username, password, env="qa"):
        self.engine = engine
        self.username = username
        self.password = password
        self.env = env
        self.serverurl = PROD_SERVER_URL if env == "prod" else QA_SERVER_URL

    def register(self, auto_attach=True, force=True):
        if not (self.username and self.password):
            raise ValueError("Please provide credentials to subscribe.")

        cmd = f"subscription-manager register --serverurl={self.serverurl} --username={self.username} --password={self.password}"
        if self.env != "prod":
            cmd = f"{cmd} --baseurl={BASE_URL}"
        if auto_attach:
            cmd = f"{cmd} --auto-attach"
        if force:
            cmd = f"{cmd} --force"

        return self.engine.exec(cmd)

    def attach(self, pool):
        cmd = f"subscription-manager attach --pool {pool}"
        return self.engine.exec(cmd)

    def unregister(self):
        return self.engine.exec("subscription-manager unregister")

    def refresh(self):
        return self.engine.exec("subscription-manager refresh")

    def clean(self):
        return self.engine.exec("subscription-manager clean")

    @property
    def status(self):
        return self.engine.exec("subscription-manager status")

    @property
    def list(self):
        return self.engine.exec("subscription-manager list")
