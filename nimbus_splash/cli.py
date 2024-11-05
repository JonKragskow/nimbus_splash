import argparse
from . import job
import subprocess
import os
import re
import xyz_py as xyzp

from . import utils as ut


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
        # 'paygo-ncv3-12',
        # 'paygo-ncv3-24',
        # 'paygo-ncv3-6',
        # 'paygo-ncv3r-24',
        # 'paygo-ndv2-40',
        'spot-hb-60',
        'spot-hbv2-120',
        'spot-hbv3-120',
        'spot-hc-44',
        # 'spot-ncv3-12',
        # 'spot-ncv3-24',
        # 'spot-ncv3-6',
        # 'spot-ncv3r-24',
        # 'spot-ndv2-40',
        # 'vis-ncv3-12',
        # 'vis-ncv3-24',
        # 'vis-ncv3-6',
        # 'vis-ndv2-40'
    ]

    cores_per_node = {
        node: int(node.split('-')[-1])
        for node in supported_nodes
    }

    total_node_memory = {
        'spot-fsv2-2': 3500 * 2,
        'spot-fsv2-4': 3500 * 4,
        'spot-fsv2-8': 3500 * 8,
        'spot-fsv2-16': 3500 * 16,
        'spot-fsv2-32': 3500 * 32,
        'paygo-fsv2-2': 3500 * 2,
        'paygo-fsv2-4': 3500 * 4,
        'paygo-fsv2-8': 3500 * 8,
        'paygo-fsv2-16': 3500 * 16,
        'paygo-fsv2-32': 3500 * 32,
        'paygo-hbv2-120': 456000,
        'paygo-hbv3-120': 448000,
        'paygo-hc-44': 352000,
        'paygo-hb-60': 228000,
        # 'paygo-ncv3-6': 112000,
        # 'paygo-ncv3-12': 224000,
        # 'paygo-ncv3-24': 448000,
        # 'paygo-ncv3r-24': 18500,
        # 'paygo-ndv2-40': 672000,
        'spot-hbv2-120': 456000,
        'spot-hbv3-120': 448000,
        'spot-hb-60': 228000,
        'spot-hc-44': 352000,
        # 'spot-ncv3-6': 112000,
        # 'spot-ncv3-12': 224000,
        # 'spot-ncv3-24': 448000,
        # 'spot-ncv3r-24': 18500,
        # 'spot-ndv2-40': 672000,
        # 'vis-ncv3-6': 112000,
        # 'vis-ncv3-12': 224000,
        # 'vis-ncv3-24': 448000,
        # 'vis-ndv2-40': 672000
    }

    if uargs.node_type in supported_nodes:
        node = uargs.node_type
    else:
        ut.red_exit("Node type unsupported")

    # Read email environment variable
    try:
        email = os.environ['SPLASH_EMAIL']
    except KeyError:
        email = ''

    # Write job file
    for file in uargs.input_files:

        if not os.path.isabs(file):
            file = os.path.join(os.getcwd(), file)

        # Check input exists
        if not os.path.exists(file):
            ut.red_exit("Cannot locate {}".format(file))

        # Check contents of input file and find any file dependencies
        dependencies = job.parse_input_contents(
            file,
            total_node_memory[node],
            cores_per_node[node]
        )

        # Look for old gbw in results directory, if it exists
        results_name = ut.gen_results_name(file)
        if 'gbw' not in dependencies and os.path.exists(results_name) and not uargs.no_guess: # noqa
            old_gbw = '{}.gbw'.format(
                os.path.split(os.path.splitext(file)[0])[1]
            )
            # If a file is located, send it to compute node for orca
            # to use as guess MO
            if os.path.exists(os.path.join(results_name, old_gbw)):
                dependencies['gbw'] = old_gbw
                ut.cprint(
                    f'Using {old_gbw} in {results_name} as input MO in {file}',
                    'black_yellowbg'
                )

        # Check file dependencies exist
        dependency_paths = job.locate_dependencies(dependencies, file)

        # Check formatting of xyz file
        if 'xyz' in dependencies.keys() and not uargs.skip_xyz:
            try:
                xyzp.check_xyz(
                    dependency_paths['xyz'],
                    allow_indices=False
                )
            except ValueError as e:
                ut.red_exit(
                    f'{e}\n Use -sx to skip this check'
                )

        if uargs.verbose:
            print(dependencies)
            print(dependency_paths)

        job_file = job.write_file(
            file, node, uargs.time, verbose=True,
            dependency_paths=ut.flatten_recursive(
                list(dependency_paths.values())
            ),
            orca_module=uargs.orca_module,
            email=email
        )

        # Submit to queue
        if not uargs.no_start:
            subprocess.call("sbatch {}".format(job_file), shell=True)

    return


def rst_opt_func(uargs, job_args):
    '''
    Wrapper for command line call to rst_opt
    Restarts optimisation calculation when only the output file is available
    '''

    path, raw_file = os.path.split(uargs.output_file)
    head = os.path.splitext(raw_file)[0]

    # Extract coordinates from output file
    labels, coords, opt_yn = ut.get_opt_coords(uargs.output_file)

    # Extract input information from output file
    input_info = ut.get_input_section(uargs.output_file)

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
        ut.cprint(
            'Optimisation complete, restarting only for frequencies',
            'blue'
        )

    # Create -rst input file
    new_input = os.path.join(new_folder, "{}-rst.inp".format(head))
    with open(new_input, 'w') as f:
        f.write(input_info)

    # Run submit on new calculation
    read_args(
        [
            "submit",
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

    submit = subparsers.add_parser(
        'submit',
        description='Generate Nimbus SLURM submission script'
    )
    submit.set_defaults(func=submit_func)

    submit.add_argument(
        'input_files',
        nargs='+',
        type=str,
        help='Orca input file name(s)'
    )

    default_compute = ut.get_envvar('SPLASH_DEFAULT_INSTANCE')
    if not len(default_compute):
        default_compute = 'spot-fsv2-16'

    submit.add_argument(
        '-nt',
        '--node_type',
        default=default_compute,
        type=str,
        help=f'Node to run on, default is {default_compute}'
    )

    submit.add_argument(
        '-t',
        '--time',
        type=str,
        default='24:00:00',
        help='Time for job, formatted as HH:MM:SS, default 24:00:00'
    )

    default_module = ut.get_envvar('SPLASH_ORCA_MODULE')
    if not len(default_module):
        default_module = 'ORCA/6.0.0'

    submit.add_argument(
        '-o',
        '--orca_module',
        type=str,
        default=default_module,
        help='Name of orca module e.g. ORCA/6.0.0'
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
