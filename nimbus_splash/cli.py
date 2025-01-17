import argparse
from . import job
import subprocess
import os
import pathlib
import warnings

from . import utils as ut
from . import config as cfg
from .__version__ import __version__


def custom_formatwarning(msg, *args, **kwargs):
    # ignore everything except the message
    return ut.cstring(str(msg) + '\n', 'black_yellowbg')


warnings.formatwarning = custom_formatwarning


def orca_modules_func(uargs):
    '''
    Wrapper for CLI orca_modules call

    Parameters
    ----------
    uargs : argparser object
        User arguments

    Returns
    -------
    None
    '''

    # Print orca versions

    ut.cprint(
        f'    ORCA MODULES KNOWN TO NIMBUS_SPLASH V{__version__}',
        'green'
    )

    for instance, options in cfg.ORCA_MODULES.items():
        ut.cprint('*************************************************', 'green')
        ut.cprint(f'{instance}', 'cyan')
        for version, module in options.items():
            ut.cprint(f'    {version}: {module}', 'cyan')

    ut.cprint('*************************************************', 'green')

    ut.cprint(
        'Contact Dr Jon Kragskow to add missing modules to splash',
        'green'
    )

    return


def submit_func(uargs):
    '''
    Wrapper for CLI submit call

    Parameters
    ----------
    uargs : argparser object
        User arguments

    Returns
    -------
    None
    '''

    if len(ut.get_envvar('SPLASH_ORCA_MODULE')):
        ut.red_exit(
            (
                'SPLASH_ORCA_MODULE environment variableis deprecated\n'
                'Please ee nimbus_splash documentation\n'
                'And set SPLASH_ORCA_VERSION instead'
            )
        )

    if uargs.instance in cfg.ORCA_SUPPORTED_INSTANCES:
        instance = uargs.instance
    else:
        ut.red_exit('Error: instance {uargs.instance} unsupported')

    # Read email environment variable
    try:
        email = os.environ['SPLASH_EMAIL']
    except KeyError:
        email = ''

    # Write job file
    for file in uargs.input_files:

        # Check input exists
        if not file.exists:
            ut.red_exit('Cannot locate {}'.format(file.name))

        # Check contents/format of input file and any file dependencies
        # with warnings.catch_warnings(record=True) as w:
        try:
            dependencies = job.parse_input_contents(
                file,
                instance_name=instance,
                skip_xyz=uargs.skip_xyz
            )
        except (ValueError, FileNotFoundError) as err:
            ut.red_exit(str(err))

            # if w:
            #     ut.cprint(str(w[0]), 'black_yellowbg')

        if uargs.verbose:
            print(dependencies)

        # Check for research allocation id environment variable
        raid = ut.get_envvar('SPLASH_RAID')
        if not len(raid):
            ut.red_exit('Please set SPLASH_RAID environment variable')

        job_file = job.write_file(
            file, instance, uargs.time, verbose=True,
            dependencies=list(dependencies.values()),
            orca_version=uargs.orca_version,
            research_allocation_id=raid,
            email=email
        )

        # Submit to queue
        if not uargs.no_start:
            subprocess.call('sbatch {}'.format(job_file), shell=True)

    return


def read_args(arg_list=None):
    '''
    Reader for command line arguments.
    Uses sub parsers for individual programs

    Parameters
    ----------
        args : argparser object
            command line arguments

    Returns
    -------
        None
    '''

    description = '''
    A package for working with Orca on Bath's Cloud HPC service
    '''

    epilog = '''
    To display options for a specific program, use splash \
    PROGRAMFILETYPE -h
    '''
    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='prog')

    submit = subparsers.add_parser(
        'submit',
        description='Generate Nimbus SLURM submission script'
    )
    submit.set_defaults(func=submit_func)

    submit.add_argument(
        'input_files',
        nargs='+',
        type=pathlib.Path,
        help='Orca input file name(s)'
    )

    default_instance = ut.get_envvar('SPLASH_DEFAULT_INSTANCE')
    if default_instance not in cfg.ORCA_SUPPORTED_INSTANCES:
        default_instance = 'spot-fsv2-16'

    submit.add_argument(
        '-i',
        '--instance',
        default=default_instance,
        type=str,
        help=f'Instance to run on, default is {default_instance}'
    )

    submit.add_argument(
        '-t',
        '--time',
        type=str,
        default='24:00:00',
        help='Time for job, formatted as HH:MM:SS, default 24:00:00'
    )

    default_version = ut.get_envvar('SPLASH_ORCA_VERSION')
    if not len(default_version):
        default_version = '6.0.1'

    submit.add_argument(
        '-o',
        '--orca_version',
        type=str,
        default=default_version,
        help='Version of orca to use e.g. 6.0.1'
    )

    submit.add_argument(
        '-sx',
        '--skip_xyz',
        action='store_true',
        help='Skip formatting check for .xyz file'
    )

    submit.add_argument(
        '-ns',
        '--no_start',
        action='store_true',
        help='If specified, jobs are not submitted to nimbus queue'
    )

    submit.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='If specified, debug information is printed to screen'
    )

    submit.add_argument(
        '-ng',
        '--no_guess',
        action='store_true',
        help=(
            'If specified, gbw files found in results directory will not be'
            'used automatically'
        )
    )

    versions = subparsers.add_parser(
        'orca_modules',
        description='Print orca modules known to splash'
    )
    versions.set_defaults(func=orca_modules_func)

    # If argument list is none, then call function func
    # which is assigned to help function
    parser.set_defaults(func=lambda user_args: parser.print_help())

    # read sub-parser
    _args, _ = parser.parse_known_args(arg_list)

    # select parsing option based on sub-parser
    if _args.prog in ['rst_opt']:
        args, job_args = parser.parse_known_args(arg_list)
        args.func(args, job_args)
    else:
        args = parser.parse_args(arg_list)
        args.func(args)
    return args


def interface():
    read_args()
    return
