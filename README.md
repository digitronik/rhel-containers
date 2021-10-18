<h1 align="center"> rhel-containers </h1>
<h2 align="center"> RHEL containers for Insight testing </h2>

Note: *In progress* (POC)

### Installation
It's not package yet as POC. You can install it with source
```shell
git clone git@github.com:digitronik/rhel-containers.git
cd rhel-containers
python3 -m venv .env
source .env/bin/activate
pip install -e .    # editable
```

### Config
To get up and running, you can utilize a local config file (`~/.config/rhel_cont.yaml`).
`rhel-containers` ships with a [default config](src/rhel_containers/conf/conf.yaml).
For subscription and insights-client registration you can overwrite configuration by creating file `~/.config/rhel_cont.yaml`.
`default` session holds default configuration you can overwrite values in specific session.

Example:
```shell
default:
  rhel_containers:
    subscription:
      # eg. creds common for all env except prod else overwrite in each env.
      username: foo
      password: bar
prod:
  rhel_containers:
    subscription:
      username: foo_prod
      password: bar_prod
stage:
  rhel_containers:
    insights_client:
      proxy: foo.com
```
**Note:** For now, credentials are in plain text.

### Usage:
```python
(.env) ~/r/rhel-containers ❯❯❯ ipython
Python 3.9.2 (default, Feb 20 2021, 00:00:00)

In [1]: from rhel_containers import RhelContainer

In [2]: rc = RhelContainer(engine_name="podman", release=8.3, env='ci')

In [3]: # engine can be [podman, docker, kubectl, oc]. release point to which version of rhel, curretnly, rhel7 and rhel8 supported.

In [4]: rc.start() # it will run rhel-8.3 container.
Out[4]: ContCommandResult(exit_status=0)

In [5]: rc.subscription.register() # subscribe system
Out[5]: ContCommandResult(exit_status=0)

In [6]: rc.subscription.status
Out[6]: ContCommandResult(exit_status=0)

In [7]: rc.subscription.status.stdout
Out[7]: '+-------------------------------------------+\n   System Status Details\n+-------------------------------------------+\nOverall Status: Current\n\nSystem Purpose Status: Not Specified'

In [8]: rc.insights_client.install() # Install insights-client

In [9]: rc.is_pkg_installed("insights-client") # check pkg installed or not
Out[9]: True

In [10]: rc.insights_client.configure() # configure insights-client for specific env.

In [11]: rc.insights_client.register() # register system
Out[11]: ContCommandResult(exit_status=0)

In [12]: rc.hostname # it will give hostname of container and with same you can check your system
    ...:  in insights.
Out[12]: '4debc82a1b9d'

In [13]: rc.setup("insights-client") # It will do all above steps for you like subcription, insight client installation and registration.

In [14]: rc.enable_epel() # enable EPEL repo

In [15]: rc.install("weechat") # installing package from EPEL repo
Out[15]: ContCommandResult(exit_status=0)

In [16]: rc.is_pkg_installed("weechat")
Out[16]: True

In [17]: rm -rf insights-9d90211a6956-20210512080327.tar.gz

In [18]: ls
LICENSE  README.md  setup.cfg  setup.py  src/  tests/

In [19]: rc.create_archive()
Out[19]: ContCommandResult(exit_status=0)

In [20]: ls
insights-4debc82a1b9d-20210512161946.tar.gz  README.md  setup.py  tests/
LICENSE                                      setup.cfg  src/

In [21]: rc.copy_to_cont(host_path="README.md", cont_path="/README.md") # copy some file to system
Out[21]: ContCommandResult(exit_status=0)

In [21]: rc.exec("cat /README.md").stdout	# execute some command on system
Out[21]: '<h1 align="center"> rhel-containers </h1>\n<h2 align="center"> RHEL containers for Insight testing </h2>\n\nNote: *In progress* (POC)'


In [22]: rc.stop() # stop container :)
Out[22]: ContCommandResult(exit_status=0)
```

### WIP
- [x] Support to `Openshift`
- [] Integration with `iqe`
- [] CLI so everyone can use other than qe
