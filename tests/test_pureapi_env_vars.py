import os
import pytest

@pytest.mark.forked
def test_env_version():
    version = '516'
    os.environ['PURE_API_VERSION'] = version
    domain = 'experts.umn.edu'
    os.environ['PURE_API_DOMAIN'] = domain
    import pureapi
    assert pureapi.default_version == os.environ.get('PURE_API_VERSION')
    assert pureapi.default_version == version
    assert pureapi.default_domain == os.environ.get('PURE_API_DOMAIN')
    assert pureapi.default_domain == domain

    assert (
        pureapi.construct_base_url()
        ==
        f'{pureapi.default_protocol}://{domain}/{pureapi.default_path}/{version}/'
    )
