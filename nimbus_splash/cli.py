import argparse
from . import job
import subprocess
import os
import re
import xyz_py as xyzp

from .utils import red_exit, get_opt_coords, get_input_section, blue_print


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

    # Currently available nodes
    supported_nodes = [
        'spot-fsv2-2',
        'spot-fsv2-4',
        'spot-fsv2-8',
        'spot-fsv2-16',
        'spot-fsv2-32',
        'paygo-fsv2-2',
        'paygo-fsv2-4',
        'paygo-fsv2-8',
        'paygo-fsv2-16',
        'paygo-fsv2-32',
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
    ]

    cores_per_node = {
        node: int(node.split('-')[-1])
        for node in supported_nodes
    }

    total_node_memory = {
        'spot-fsv2-2': 4000,
        'spot-fsv2-4': 8000,
        'spot-fsv2-8': 16000,
        'spot-fsv2-16': 32000,
        'spot-fsv2-32': 64000,
        'paygo-fsv2-2': 4000,
        'paygo-fsv2-4': 8000,
        'paygo-fsv2-8': 16000,
        'paygo-fsv2-16': 32000,
        'paygo-fsv2-32': 64000,
        'paygo-hbv2-120': 456000,
        'paygo-hbv3-120': 448000,
        'paygo-hc-44': 352000,
        'paygo-ncv3-6': 112000,
        'paygo-ncv3-12': 224000,
        'paygo-ncv3-24': 448000,
        'paygo-ncv3r-24': 18500,
        'paygo-ndv2-40': 672000,
        'spot-hbv2-120': 456000,
        'spot-hbv3-120': 448000,
        'spot-hc-44': 352000,
        'spot-ncv3-6': 112000,
        'spot-ncv3-12': 224000,
        'spot-ncv3-24': 448000,
        'spot-ncv3r-24': 18500,
        'spot-ndv2-40': 672000,
        'vis-ncv3-6': 112000,
        'vis-ncv3-12': 224000,
        'vis-ncv3-24': 448000,
        'vis-ndv2-40': 672000
    }

    if uargs.node_type in supported_nodes:
        node = uargs.node_type
    else:
        red_exit("Node type unsupported")

    if uargs.n_cores:
        if cores_per_node[node] < uargs.n_cores:
            red_exit("Specified number of cores exceeds node limit")
        else:
            n_cores = uargs.n_cores
    else:
        n_cores = cores_per_node[node]

    # Write job file
    for file in uargs.input_files:

        # Check input exists
        if not os.path.exists(file):
            red_exit("Cannot locate {}".format(file))

        # Check contents of input file and find any file dependencies
        _, input_deps_rel = job.parse_input_contents(
            file, total_node_memory[node] / n_cores
        )

        # Check for old results folder and look at contents
        # to see if any restart capable files exist
        result_deps = job.parse_results_contents(file)

        # Resolve different versions of same filetypes
        dependencies = job.resolve_deps(input_deps_rel, result_deps)

        # Add number of cores to input file
        job.add_core_to_input(file, n_cores)

        job_file = job.write_file(
            file, node, uargs.time, verbose=True, dependencies=dependencies
        )

        # Submit to queue
        if not uargs.no_start:
            subprocess.call("sbatch {}".format(job_file), shell=True)

    return


def rst_opt_func(uargs, job_args):

    path, raw_file = os.path.split(uargs.output_file)
    head = os.path.splitext(raw_file)[0]

    # Extract coordinates from output file
    labels, coords, opt_yn = get_opt_coords(uargs.output_file)

    # Extract input information from output file
    input_info = get_input_section(uargs.output_file)

    # Create rst folder
    new_folder = os.path.join(path, 'rst')
    os.mkdir(new_folder)

    # Create -rst xyz file
    new_xyz = os.path.join(new_folder, "{}-rst.xyz".format(head))
    xyzp.save_xyz(new_xyz, labels, coords, verbose=False)

    # Edit xyz file name in input_info
    input_info = re.sub(
        r"[\-a-z0-9A-Z_]+\.xyz",
        "{}-rst.xyz".format(head),
        input_info
    )

    # If optimised, delete opt keyword from input
    if opt_yn:
        input_info = re.sub(
            r"\bopt\b(?!-)(?!\.)",
            "",
            input_info
        )
        blue_print("Optimisation complete, restarting only for frequencies")

    # Create -rst input file
    new_input = os.path.join(new_folder, "{}-rst.inp".format(head))
    with open(new_input, 'w') as f:
        f.write(input_info)

    # Run gen_job on new calculation
    read_args(
        [
            "gen_job",
            new_input,
            *job_args
        ]
    )

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

    gen_job.add_argument(
        '-n',
        '--n_cores',
        type=int,
        default=False,
        help='Number of cores to use on given node, default uses all cores'
    )
    gen_job.add_argument(
        '-nt',
        '--node_type',
        default='spot-fsv2-16',
        type=str,
        help='Node to run on, default is spot-fsv2-16'
    )

    gen_job.add_argument(
        '-t',
        '--time',
        type=str,
        default='24:00:00',
        help='Time for job, formatted as HH:MM:SS, default 24:00:00'
    )

    gen_job.add_argument(
        '-ns',
        '--no_start',
        action='store_true',
        help='If specified, jobs are not submitted to nimbus queue'
    )

    rst_opt = subparsers.add_parser(
        'rst_opt',
        description='Restart optimisation from output file'
    )
    rst_opt.set_defaults(func=rst_opt_func)

    rst_opt.add_argument(
        'output_file',
        type=str,
        help='Orca output file name(s) (must contain coordinates from optimisation)' # noqa
    )

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
