<h1 align="center"> rhel-containers </h1>
<h2 align="center"> RHEL containers for Insight testing </h2>

Note: *In progress* (POC)

### Installation
It's not package yet as POC. You can install it with source
```shell
git cone git@github.com:digitronik/rhel-containers.git
cd rhel-containers
python3 -m venv .venv
source .venv/bin/activate
pip install -e .    # editable
```

### Config
To get up and running, you can utilize a local config file (`~/.config/rhel_cont.yaml`).
`rhel-containers` ships with a [default config](src/rhel_containers/conf/conf.yaml).
For subscription and insights-client registration you can overwrite configuration by creating file `~/.config/rhel_cont.yaml`.

Example:
```shell
qa:
  rhel_containers:
    username: foo
    password: bar
ci:
  rhel_containers:
    username: foo
    password: bar
prod:
  rhel_containers:
    username: foo
    password: bar
```
**Note:** For now, credentials are in plain text.

### Usage:
```python
(.env) ~/r/rhel-containers ❯❯❯ ipython
Python 3.9.2 (default, Feb 20 2021, 00:00:00)

In [1]: from rhel_containers import RhelContainer

In [2]: rc = RhelContainer(release=8.3, env='ci')

In [3]: rc.start()
Out[3]: ContCommandResult(exit_status=0)

In [4]: rc.exec("ls").stdout
Out[4]: 'bin\nboot\ndev\netc\nhome\nlib\nlib64\nlost+found\nmedia\nmnt\nopt\nproc\nroot\nrun\nsbin\nsrv\nsys\ntmp\nusr\nvar'

In [5]: rc.subscription.list
Out[5]: ContCommandResult(exit_status=0)

In [6]: rc.subscription.register().stdout
Out[6]: 'Registering to: subscription.rhsm.qa.redhat.com:443/subscription\nThe system has been registered with ID: 1fcb339c-9f6b-4321-869d-bb05b207d172\nThe registered system name is: 8b5af8cd68de\nInstalled Product Current Status:\nProduct Name: Red Hat Enterprise Linux for x86_64\nStatus:       Subscribed'

In [7]: rc.insights_client.install()

In [8]: rc.insights_client.configure()

In [9]: rc.exec("cat /etc/insights-client/insights-client.conf").stdout
Out[9]: '[insights-client]\nbase_url= ci.cloud.redhat.com/api\ncert_verify=False\nauto_config=False\nlegacy_upload=False\nauthmethod=CERT'

In [10]: rc.insights_client.register().stdout

Out[10]: 'Unable to fetch egg url. Defaulting to /release\nAutomatic scheduling for Insights has been enabled.\nStarting to collect Insights data for 8b5af8cd68de\nUploading Insights data.\nSuccessfully uploaded report for 8b5af8cd68de.\nView the Red Hat Insights console at https://cloud.redhat.com/insights/'

In [11]: rc.is_pkg_installed("insights-client")
Out[11]: True

In [12]: rc.install("git")
Out[12]: ContCommandResult(exit_status=0)

In [13]: rc.is_pkg_installed("git")
Out[13]: True

In [14]: rc.hostname
Out[14]: '8b5af8cd68de'

In [15]: rc.enable_epel()

In [16]: rc.install("weechat")
Out[16]: ContCommandResult(exit_status=0)

In [17]: rc.is_pkg_installed("weechat")
Out[17]: True

In [18]: ls
LICENSE  README.md  setup.cfg  setup.py  src/  tests/

In [19]: rc.copy_to_cont(host_path="README.md", cont_path="/README.md")
Out[19]: ContCommandResult(exit_status=0)

In [20]: rc.exec("cat /README.md").stdout
Out[20]: '<h1 align="center"> rhel-containers </h1>\n<h2 align="center"> RHEL containers for Insight testing </h2>\n\nNote: *In progress* (POC)'

In [21]: rc.create_archive()
Out[21]: ContCommandResult(exit_status=0)

In [22]: ls
insights-8b5af8cd68de-20210510170726.tar.gz  LICENSE  README.md  setup.cfg  setup.py  src/  tests/

In [23]: rc.stop()
Out[23]: ContCommandResult(exit_status=0)

In [24]: exit
```

### WIP
- [] Support to `Openshift`
- [] Integration with `iqe`
- [] CLI so everyone can use other than qe
