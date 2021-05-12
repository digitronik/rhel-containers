# RHEL Subscription management.


class Subscription:
    def __init__(self, engine, config, env="qa", *args, **kwargs):
        self._engine = engine
        self._config = config
        self._env = env

    def register(self, auto_attach=True, force=True):
        """Subscribed system

        Args:
            auto_attach: auto attach pool
            force: force subscribed
        """
        if not (self._config.username and self._config.password):
            raise ValueError("Please provide credentials to subscribe.")

        cmd = (
            f"subscription-manager register --serverurl={self._config.subscription.server} "
            f"--username={self._config.username} --password={self._config.password}"
        )
        if self._env != "prod":
            cmd = f"{cmd} --baseurl={self._config.subscription.cdn}"
        if auto_attach:
            cmd = f"{cmd} --auto-attach"
        if force:
            cmd = f"{cmd} --force"

        return self._engine.exec(cmd)

    def attach(self, pool):
        """Attach pool

        Args:
            pool: pool id
        """
        cmd = f"subscription-manager attach --pool {pool}"
        return self._engine.exec(cmd)

    def unregister(self):
        return self._engine.exec("subscription-manager unregister")

    def refresh(self):
        return self._engine.exec("subscription-manager refresh")

    def clean(self):
        return self._engine.exec("subscription-manager clean")

    @property
    def status(self):
        return self._engine.exec("subscription-manager status")

    @property
    def list(self):
        return self._engine.exec("subscription-manager list")
