from pathlib import Path

import rhel_containers as rc
import yaml
from box import Box

PROJECT_PATH = Path(rc.__file__).parent
DEFAULT_CONF = PROJECT_PATH.joinpath("conf", "conf.yaml")
LOCAL_CONF = Path.home().joinpath(".config", "rhel_cont.yaml")


def merge(a, b, path=None):
    """Merge a dict to b dict."""

    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                # same value
                pass
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a


def _load_file(path):
    with path.open() as fp:
        return yaml.safe_load(fp)


def load_config(env, extra_conf=None):
    """Load configuration files."""
    conf = _load_file(DEFAULT_CONF)

    # overwrite local conf is available
    if LOCAL_CONF.exists():
        local_conf = _load_file(LOCAL_CONF)
        conf = merge(conf, local_conf)

    # merge data as per env
    conf = merge(conf["default"], conf[env])

    # for iqe testing, we can pass extra_conf.
    if extra_conf:
        conf = merge(conf, extra_conf)
    return Box(conf).RHEL_CONTAINERS
