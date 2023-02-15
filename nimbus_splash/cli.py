import argparse
from . import job
import subprocess
import os

from .utils import red_exit


def gen_job_func(uargs):
    '''
    Wrapper for CLI gen_job call

    Parameters
    ----------
    uargs : argparser object
        User arguments

    Returns
    -------
    None

    '''

    # Default node types - fsv2 spot
    default_from_core = {
        1: 'spot-fsv2-1',
        2: 'spot-fsv2-2',
        4: 'spot-fsv2-4',
        16: 'spot-fsv2-16',
        24: 'spot-fsv2-24',
        32: 'spot-fsv2-32',
        36: 'spot-fsv2-36',
    }

    # Currently available nodes
    supported_nodes = {
        'spot-fsv2-1',
        'spot-fsv2-2',
        'spot-fsv2-4',
        'spot-fsv2-16',
        'spot-fsv2-24',
        'spot-fsv2-32',
        'spot-fsv2-36',
        'paygo-fsv2-1',
        'paygo-fsv2-2',
        'paygo-fsv2-4',
        'paygo-fsv2-16',
        'paygo-fsv2-24',
        'paygo-fsv2-32',
        'paygo-fsv2-36',
        'paygo-hb-60',
        'paygo-hbv2-120',
        'paygo-hbv3-120',
        'paygo-hc-44',
        'paygo-ncv3-12',
        'paygo-ncv3-24',
        'paygo-ncv3-6',
        'paygo-ncv3r-24',
        'paygo-ndv2-40',
        'spot-hb-60',
        'spot-hbv2-120',
        'spot-hbv3-120',
        'spot-hc-44',
        'spot-ncv3-12',
        'spot-ncv3-24',
        'spot-ncv3-6',
        'spot-ncv3r-24',
        'spot-ndv2-40',
        'vis-ncv3-12',
        'vis-ncv3-24',
        'vis-ncv3-6',
        'vis-ndv2-40'
    }

    if uargs.node_type:
        if uargs.node_type in supported_nodes:
            node = uargs.node_type
        else:
            red_exit("Node type unsupported")
    else:
        try:
            node = default_from_core[uargs.n_cores]
        except KeyError:
            red_exit("Specified number of cores is unsupported")

    n_cores = int(node.split('-')[-1])

    # Write job file

    for file in uargs.input_files:

        # Check input exists
        if not os.path.exists(file):
            red_exit("Cannot locate input file")

        # Check contents of input file and find any dependencies
        dependencies = job.parse_input_contents(file, 4000)

        job.add_core_to_input(file, n_cores)

        job_file = job.write_file(
            file, node, uargs.time, verbose=True, dependencies=dependencies
        )

        # Submit to queue
        if not uargs.no_start:
            subprocess.call("sbatch {}".format(job_file), shell=True)

    return


def read_args(arg_list=None):
    '''
    Reader for command line arguments. Uses subReaders for individual programs

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

    gen_job = subparsers.add_parser(
        'gen_job',
        description='Generate Nimbus SLURM submission script'
    )
    gen_job.set_defaults(func=gen_job_func)

    gen_job.add_argument(
        'input_files',
        nargs='+',
        type=str,
        help='Orca input file name(s)'
    )

    node_spec = gen_job.add_mutually_exclusive_group()
    node_spec.add_argument(
        '-n',
        '--n_cores',
        type=int,
        default=16,
        help='Number of cores to use for fsv2 node, default is 16'
    )
    node_spec.add_argument(
        '-nt',
        '--node_type',
        type=str,
        help='Node to run on, default is spot-fsv2-16'
    )

    gen_job.add_argument(
        '-t',
        '--time',
        type=str,
        default='06:00:00',
        help='Time for job, formatted as HH:MM:SS, default 06:00:00'
    )

    gen_job.add_argument(
        '-ns',
        '--no_start',
        action='store_true',
        help='If specified, jobs are not submitted to nimbus queue'
    )

    # If arg_list==None, i.e. normal cli usage, parse_args() reads from
    # 'sys.argv'. The arg_list can be used to call the argparser from the
    # back end.

    # read sub-parser
    parser.set_defaults(func=lambda args: parser.print_help())
    args = parser.parse_args(arg_list)
    args.func(args)

    return args


def interface():
    read_args()
    return
