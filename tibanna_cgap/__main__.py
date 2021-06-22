"""
CLI for tibanna_cgap package
"""

# -*- coding: utf-8 -*-
import argparse
import inspect
from tibanna_ffcommon._version import __version__  # for now use the same version as tibanna
# from botocore.errorfactory import ExecutionAlreadyExists
from .vars import (
    TIBANNA_DEFAULT_STEP_FUNCTION_NAME
)
# do not delete imported but unused functions below.
from .core import API
from tibanna.__main__ import Subcommands as _Subcommands
from tibanna.__main__ import (
    users,
)
PACKAGE_NAME = 'tibanna_cgap'


class Subcommands(_Subcommands):

    default_sfn = TIBANNA_DEFAULT_STEP_FUNCTION_NAME

    def __init__(self):
        pass

    @property
    def descriptions(self):
        desc = super().descriptions
        desc['deploy_zebra'] = 'deploy tibanna zebra to AWS cloud (zebra is for CGAP only)'
        return desc

    @property
    def args(self):
        _args = super().args
        _args['deploy_zebra'] = \
            [{'flag': ["-s", "--suffix"],
              'help': "suffix (e.g. 'dev') to add to the end of the name of" +
                      "tibanna_zebra and AWS Lambda functions within the same usergroup"},
             {'flag': ["-g", "--usergroup"],
              'default': '',
              'help': "Tibanna usergroup to share the permission to access buckets and run jobs"},
             {'flag': ["-t", "--subnets"],
              'nargs': '+',
              'help': "subnet IDs, separated by commas"},
             {'flag': ["-r", "--security-groups"],
              'nargs': '+',
              'help': "security groups, separated by commas"},
             {'flag': ["-e", "--env"],
              'help': "env name"}]

        _args['deploy_core'] = \
            [{'flag': ["-n", "--name"],
              'help': "name of the lambda function to deploy (e.g. run_task_awsem)"},
             {'flag': ["-s", "--suffix"],
              'help': "suffix (e.g. 'dev') to add to the end of the name of the AWS " +
                      "Lambda function, within the same usergroup"},
             {'flag': ["-g", "--usergroup"],
              'default': '',
              'help': "Tibanna usergroup for the AWS Lambda function"},
             {'flag': ["-t", "--subnets"],
              'nargs': '+',
              'help': "subnet IDs, separated by commas"},
             {'flag': ["-r", "--security-groups"],
              'nargs': '+',
              'help': "security groups, separated by commas"},
             {'flag': ["-e", "--env"],
              'help': "env name"},
             {'flag': ["-q", "--quiet"],
              'action': "store_true",
              'help': "minimize standard output from deployment"}]

        _args['kill'] = \
            [{'flag': ["-e", "--exec-arn"],
              'help': "execution arn of the specific job to kill"},
             {'flag': ["-j", "--job-id"],
              'help': "job id of the specific job to kill (alternative to --exec-arn/-e)"}]

        _args['kill_all'] = \
            [{'flag': ["-s", "--sfn"],
              'help': "tibanna step function name (e.g. 'tibanna_unicorn_monty'); " +
                      "your current default is %s)" % TIBANNA_DEFAULT_STEP_FUNCTION_NAME,
              'default': TIBANNA_DEFAULT_STEP_FUNCTION_NAME}]

        return _args


def deploy_core(name, suffix=None, usergroup='', subnets=None, security_groups=None, env=None, quiet=False):
    """
    New method of deploying packaged lambdas (BETA)
    """
    API().deploy_core(name=name, suffix=suffix, usergroup=usergroup, subnets=subnets,
                      security_groups=security_groups, env=env, quiet=quiet)


def deploy_zebra(suffix=None, usergroup='', subnets=None, security_groups=None, env=None):
    """deploy tibanna zebra to AWS cloud (zebra is for CGAP only)"""
    API().deploy_zebra(suffix=suffix, usergroup=usergroup, subnets=subnets,
                       security_groups=security_groups, env=env)


def run_workflow(input_json, sfn=TIBANNA_DEFAULT_STEP_FUNCTION_NAME, jobid='', sleep=3):
    API().run_workflow(input_json=input_json, sfn=sfn, jobid=jobid, sleep=sleep, verbose=True)


def list_sfns(numbers=False):
    """list all step functions, optionally with a summary (-n)"""
    API().list_sfns(numbers=numbers)


def log(exec_arn=None, job_id=None, exec_name=None, sfn=TIBANNA_DEFAULT_STEP_FUNCTION_NAME,
        runjson=False, postrunjson=False, top=False, top_latest=False):
    """print execution log, run json (-r), postrun json (-p) or top (-t) for a job"""
    print(API().log(exec_arn, job_id, exec_name, sfn, runjson=runjson, postrunjson=postrunjson,
                    top=top, top_latest=top_latest))


def kill_all(sfn=TIBANNA_DEFAULT_STEP_FUNCTION_NAME):
    """kill all the running jobs on a step function"""
    API().kill_all(sfn)


def kill(exec_arn=None, job_id=None):
    """kill a specific job"""
    API().kill(exec_arn, job_id)


def rerun(exec_arn, sfn=TIBANNA_DEFAULT_STEP_FUNCTION_NAME, app_name_filter=None,
          instance_type=None, shutdown_min=None, ebs_size=None, ebs_type=None, ebs_iops=None,
          overwrite_input_extra=None, key_name=None, name=None):
    """ rerun a specific job"""
    API().rerun(exec_arn, sfn=sfn,
                app_name_filter=app_name_filter, instance_type=instance_type, shutdown_min=shutdown_min,
                ebs_size=ebs_size, ebs_type=ebs_type, ebs_iops=ebs_iops,
                overwrite_input_extra=overwrite_input_extra, key_name=key_name, name=name)


def rerun_many(sfn=TIBANNA_DEFAULT_STEP_FUNCTION_NAME, stopdate='13Feb2018', stophour=13,
               stopminute=0, offset=0, sleeptime=5, status='FAILED', app_name_filter=None,
               instance_type=None, shutdown_min=None, ebs_size=None, ebs_type=None, ebs_iops=None,
               overwrite_input_extra=None, key_name=None, name=None):
    """rerun all the jobs that failed after a given time point
    filtered by the time when the run failed (stopdate, stophour (24-hour format), stopminute)
    By default, stophour should be the same as your system time zone. This can be changed by setting a different offset.
    If offset=5, for instance, that means your stoptime=12 would correspond to your system time=17.
    Sleeptime is sleep time in seconds between rerun submissions.
    By default, it reruns only 'FAILED' runs, but this can be changed by resetting status.

    Examples

    rerun_many('tibanna_zebra-dev')
    rerun_many('tibanna_zebra', stopdate= '14Feb2018', stophour=14, stopminute=20)
    """
    API().rerun_many(sfn=sfn, stopdate=stopdate, stophour=stophour,
                     stopminute=stopminute, offset=offset, sleeptime=sleeptime, status=status,
                     app_name_filter=app_name_filter, instance_type=instance_type, shutdown_min=shutdown_min,
                     ebs_size=ebs_size, ebs_type=ebs_type, ebs_iops=ebs_iops,
                     overwrite_input_extra=overwrite_input_extra, key_name=key_name, name=name)


def stat(sfn=TIBANNA_DEFAULT_STEP_FUNCTION_NAME, status=None, long=False, nlines=None):
    """print out executions with details
    status can be one of 'RUNNING'|'SUCCEEDED'|'FAILED'|'TIMED_OUT'|'ABORTED'
    """
    API().stat(sfn=sfn, status=status, verbose=long, n=nlines)


def plot_metrics(job_id, sfn=TIBANNA_DEFAULT_STEP_FUNCTION_NAME, force_upload=False, update_html_only=False,
                 endtime='', do_not_open_browser=False):
    """create a resource metrics report html"""
    API().plot_metrics(job_id=job_id, sfn=sfn, force_upload=force_upload, update_html_only=update_html_only,
                       endtime=endtime, open_browser=not do_not_open_browser)


def add_user(user, usergroup):
    """add a user to a tibanna group"""
    API().add_user(user=user, usergroup=usergroup)


def cleanup(usergroup, suffix='', purge_history=False, do_not_remove_iam_group=False, do_not_ignore_errors=False, quiet=False):
    API().cleanup(user_group_name=usergroup, suffix=suffix, do_not_remove_iam_group=do_not_remove_iam_group,
                  ignore_errors=not do_not_ignore_errors, purge_history=purge_history, verbose=not quiet)


def main(Subcommands=Subcommands):
    """
    Execute the program from the command line
    """
    scs = Subcommands()

    # the primary parser is used for tibanna -v or -h
    primary_parser = argparse.ArgumentParser(prog=PACKAGE_NAME, add_help=False)
    primary_parser.add_argument('-v', '--version', action='version',
                                version='%(prog)s ' + __version__)
    # the secondary parser is used for the specific run mode
    secondary_parser = argparse.ArgumentParser(prog=PACKAGE_NAME, parents=[primary_parser])
    # the subparsers collect the args used to run the hic2cool mode
    subparsers = secondary_parser.add_subparsers(
        title=PACKAGE_NAME + ' subcommands',
        description='choose one of the following subcommands to run ' + PACKAGE_NAME,
        dest='subcommand',
        metavar='subcommand: {%s}' % ', '.join(scs.descriptions.keys())
    )
    subparsers.required = True

    def add_arg(name, flag, **kwargs):
        subparser[name].add_argument(flag[0], flag[1], **kwargs)

    def add_args(name, argdictlist):
        for argdict in argdictlist:
            add_arg(name, **argdict)

    subparser = dict()
    for sc, desc in scs.descriptions.items():
        subparser[sc] = subparsers.add_parser(sc, help=desc, description=desc)
        if sc in scs.args:
            add_args(sc, scs.args[sc])

    # two step argument parsing
    # first check for top level -v or -h (i.e. `tibanna -v`)
    (primary_namespace, remaining) = primary_parser.parse_known_args()
    # get subcommand-specific args
    args = secondary_parser.parse_args(args=remaining, namespace=primary_namespace)
    subcommandf = eval(args.subcommand)
    sc_args = [getattr(args, sc_arg) for sc_arg in inspect.getargspec(subcommandf).args]
    # run subcommand
    subcommandf(*sc_args)


if __name__ == '__main__':
    main()
