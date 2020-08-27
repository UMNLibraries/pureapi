import pytest

from pureapi import common

def pytest_addoption(parser):
    parser.addoption(
        '--integration',
        action='store_true',
        default=False,
        help='Run integration tests. Requires env var config. See README.'
    )

def pytest_configure(config):
    config.addinivalue_line('markers', 'integration: mark test as an integration test')

def pytest_collection_modifyitems(config, items):
    if config.getoption('--integration'):
        # --integration given in cli: do not skip integration tests
        return
    skip_integration = pytest.mark.skip(reason='need --integration option to run')
    for item in items:
        if 'integration' in item.keywords:
            item.add_marker(skip_integration)

@pytest.fixture(params=common.versions)
def version(request):
    return request.param
