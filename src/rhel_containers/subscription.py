# RHEL Subscription management.
import logging

logger = logging.getLogger(__name__)


class Subscription:
    """Manage subscription."""

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
        logger.info(f"Subscribing system {self._engine.name} to {self._config.serverurl}")
        auto_attach = self._config.auto_attach if auto_attach is None else auto_attach
        force = self._config.force if force is None else force

        if not (self._config.username and self._config.password):
            raise ValueError("Please provide credentials to subscribe.")

        cmd = (
            f"subscription-manager register --serverurl={self._config.serverurl} "
            f"--username={self._config.username} --password={self._config.password}"
        )

        if self._config.baseurl:
            cmd = f"{cmd} --baseurl={self._config.baseurl}"
        if auto_attach:
            cmd = f"{cmd} --auto-attach"
        if force:
            cmd = f"{cmd} --force"

        out = self._engine.exec(cmd)
        if out.exit_status != 0:
            logger.error(f"Fail to subscribe system {self._engine.name}: {out.stderr}")
        else:
            logger.info(f"Successfully subscribed.")

        return out

    def attach(self, pool=None):
        """Attach pool

        Args:
            pool: pool id
        """
        pool = pool or self._config.pool
        cmd = f"subscription-manager attach --pool {pool}"
        return self._engine.exec(cmd)

    def unregister(self):
        """Unregister this system from the Customer Portal or
        another subscription management service."""
        return self._engine.exec("subscription-manager unregister")

    def refresh(self):
        """Pull the latest subscription data from the server."""
        return self._engine.exec("subscription-manager refresh")

    def clean(self):
        """Remove all local system and subscription data without affecting the server."""
        return self._engine.exec("subscription-manager clean")

    @property
    def status(self):
        """Show status information for this system's subscriptions and products."""
        return self._engine.exec("subscription-manager status")

    @property
    def list(self):
        """List subscription and product information for this system."""
        return self._engine.exec("subscription-manager list")
