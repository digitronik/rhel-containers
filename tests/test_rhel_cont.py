import pytest
from rhel_containers import RhelContainer

ENGINES =  ["podman", "kubectl"]


@pytest.fixture(params=ENGINES, scope="module")
def rc(request):
    cont = RhelContainer(engine_name=request.param, release=8.3, env='ci')
    cont.start()
    yield cont
    cont.stop()


@pytest.fixture(scope="module")
def rc_subscribed(rc):
    out = rc.subscription.register(force=True)
    if out.exit_status != 0:
        pytest.skip(f"Problem in subscription: {out.stdout}")
    return rc


@pytest.mark.parametrize("engine", ENGINES)
def test_start_stop(engine):
    rc = RhelContainer(engine_name=engine, release=8.3, env='ci')
    rc.start()
    assert rc.status == "Running"
    rc.stop()
    assert "unavailable" in rc.status


def test_subscription(rc):
    out = rc.subscription.register()
    assert out.exit_status == 0
    assert "Subscribed" in out.stdout

    out = rc.subscription.list
    assert out.exit_status == 0
    assert "Subscribed" in out.stdout

    out = rc.subscription.refresh()
    assert out.stdout == 'All local data refreshed'

    out = rc.subscription.unregister()
    assert "System has been unregistered" in out.stdout


def test_insights_client(rc_subscribed):
    rc = rc_subscribed
    rc.insights_client.install()
    assert rc.is_pkg_installed("insights-client")
    assert "Client" in rc.insights_client.version

    rc.insights_client.configure()
    out = rc.exec("cat /etc/insights-client/insights-client.conf")
    assert rc.env in out.stdout

    assert "This host is unregistered" in rc.insights_client.status
    out = rc.insights_client.register()
    assert out.exit_status == 0
    assert "This host is registered" in rc.insights_client.status

    out = rc.insights_client.unregister()
    assert out.exit_status == 0
    assert "Successfully unregistered from the Red Hat Insights Service" in out.stdout
