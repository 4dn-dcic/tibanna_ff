import sys
import pytest
from invoke import run, task
from tibanna_4dn.core import API as API_4dn
from tibanna_cgap.core import API as API_cgap
from tibanna_ffcommon.vars import DEV_SUFFIX


@task
def test(ctx, watch=False, last_failing=False, no_flake=False, k='',  extra='',
         ignore='', ignore_pony=False, no_post=False, deployment=False, subnets=None, security_groups=None):
    """Run the tests.
    Note: --watch requires pytest-xdist to be installed.
    """
    if not deployment:
        if not no_flake:
            flake()
        args = ['-rxs', ]
        if k:
            args.append('-k %s' % k)
        args.append(extra)
        if watch:
            args.append('-f')
        else:
            args.append('--cov-report')
            args.append('xml')
            args.append('--cov-report')
            args.append('html')
        if last_failing:
            args.append('--lf')
        if ignore:
            args.append('--ignore')
            args.append(ignore)
        if ignore_pony:
            args.append('--ignore')
            args.append('tests/tibanna/pony')
        if no_post:
            args.append('--ignore')  # skip tests that posts items to portal
            args.append('tests/tibanna/pony/test_pony_utils_post.py')
            args.append('tests/tibanna/zebra/test_zebra_utils_post.py')
        args.append('tests/tibanna/')
        args.append('--ignore')
        args.append('tests/post_deployment/')
        retcode = pytest.main(args)
        if retcode != 0:
            print("test failed exiting")
            sys.exit(retcode)
        return retcode
    else:
        # subnets and security_groups are strings, but since we call the core API directly and not the tibanna_4dn/tibanna_cgap CLI, we need to convert it to a list
        API_4dn().deploy_pony(suffix=DEV_SUFFIX, subnets=[subnets], security_groups=[security_groups], env="data")
        API_4dn().deploy_pony(suffix=DEV_SUFFIX, subnets=[subnets], security_groups=[security_groups], env="webdev")
        API_cgap().deploy_zebra(suffix=DEV_SUFFIX, subnets=[subnets], security_groups=[security_groups], env="cgap")
        API_cgap().deploy_zebra(suffix=DEV_SUFFIX, subnets=[subnets], security_groups=[security_groups], env="cgapwolf")
        pytest.main(['--workers', '100', 'tests/post_deployment'])


def flake():
    """Run flake8 on codebase."""
    run('flake8 .', echo=True)
    print("flake8 passed!!!")
