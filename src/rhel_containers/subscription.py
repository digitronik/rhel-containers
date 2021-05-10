# RHEL Subscription management.


class Subscription:
    def __init__(self, engine, config, env="qa", *args, **kwargs):
        self.engine = engine
        self.config = config
        self.env = env

    def register(self, auto_attach=True, force=True):
        """Subscribed system

        Args:
            auto_attach: auto attach pool
            force: force subscribed
        """
        if not (self.config.username and self.config.password):
            raise ValueError("Please provide credentials to subscribe.")

        cmd = (
            f"subscription-manager register --serverurl={self.config.subscription.server} "
            f"--username={self.config.username} --password={self.config.password}"
        )
        if self.env != "prod":
            cmd = f"{cmd} --baseurl={self.config.subscription.cdn}"
        if auto_attach:
            cmd = f"{cmd} --auto-attach"
        if force:
            cmd = f"{cmd} --force"

        return self.engine.exec(cmd)

    def attach(self, pool):
        """Attach pool

        Args:
            pool: pool id
        """
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
