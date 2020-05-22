import os

def remove_env_vars():
    '''Removes test env vars from the current working directory

    This function is for cleaning up between tests. Note the potentially
    dangerous assumption that tests will never create environment
    variables named anything other than `PURE_API_VERSION`,  or
    `PURE_API_DOMAIN`. If that assumption is no longer true, this function
    must be updated accordingly. Failure to do so may cause test
    failures.
    '''
    for env_var in ('PURE_API_VERSION', 'PURE_API_DOMAIN'):
        if env_var in os.environ:
            os.environ.pop(env_var)

def pytest_runtest_setup(item):
    '''Pre-test cleanup of dotenv files and env vars

    We do this before each test invocation in case a previous test
    failed to clean up after itself.
    '''
    remove_env_vars()

def pytest_runtest_teardown(item, nextitem):
    '''Post-test cleanup of dotenv files and env vars

    We do this here rather than in test functions because, if an
    assertion fails, any code following that assertion will not be
    executed.
    '''
    remove_env_vars()

