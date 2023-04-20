import os
import sys
import subprocess

from . import utils as ut


def write_file(input_file: str, node_type: str, time: str,
               verbose: bool = False, dependencies: list[str] = []) -> str:
    '''
    Writes slurm jobscript to file for ORCA calculation on nimbus

    Output file name is input_file with .slm extension

    Parameters
    ----------
    input_file : str
        Full path to input file, including extension
    node_type : str
        Name of Nimbus node to use
    time : str
        Job time limit formatted as HH:MM:SS
    verbose : bool, default=False
        If True, prints job file name to screen
    dependencies : list[str]
        Full paths of additional files on which this job depends,
        these will be copied to the compute node at runtime

    Returns
    -------
    str
        Name of jobscript file
    '''

    # Check for research allocation id environment variable
    check_envvar('CLOUD_ACC')

    # Get raw name of input file excluding path
    inpath, in_raw = os.path.split(input_file)

    # Name of job
    job_name = os.path.splitext(in_raw)[0]

    # Job file to write to, must use path if present in input_file
    job_file = os.path.join(
        inpath,
        '{}.slm'.format(job_name)
    )

    # Path of jobfile, input, xyz, gbw etc
    if not len(inpath):
        calc_dir = os.path.abspath(os.getcwd())
    else:
        calc_dir = os.path.abspath(inpath)

    with open(job_file, 'w') as j:

        j.write('#!/bin/bash\n\n')

        j.write(f'#SBATCH --job-name={job_name}\n')
        j.write('#SBATCH --nodes=1\n')
        j.write('#SBATCH --ntasks-per-node={}\n'.format(
            node_type.split('-')[-1])
        )
        j.write(f'#SBATCH --partition={node_type}\n')
        j.write('#SBATCH --account={}\n'.format(os.environ['CLOUD_ACC']))
        j.write(f'#SBATCH --qos={node_type}\n')
        j.write(f'#SBATCH --output={job_name}.%j.o\n')
        j.write(f'#SBATCH --error={job_name}.%j.e\n')
        j.write('#SBATCH --signal=B:USR1\n\n')

        j.write('# Job time\n')
        j.write(f'#SBATCH --time={time}\n\n')

        j.write('# name and path of the input/output files and locations\n')
        j.write(f'input={in_raw}\n')
        j.write(f'output={job_name}.out\n')
        j.write(f'campaigndir={calc_dir}\n')
        j.write(f'results=$campaigndir/{job_name}\n\n')

        j.write('# If results directory already exists, append OLD and ')
        j.write('last access time\n')
        j.write('if [ -d $results ]; then\n')
        j.write(
            '    mv $results "$results"_OLD_$(date -r $results "+%m-%d-%Y")\n')
        j.write('fi\n\n')

        j.write('# If output file already exists, append OLD and ')
        j.write('last access time\n')
        j.write('if [ -d $output ]; then\n')
        j.write(
            '    mv $output "$output"_OLD_$(date -r $output "+%m-%d-%Y")\n')
        j.write('fi\n\n')

        j.write('# Local (Node) scratch, either node itself if supported')
        j.write('or burstbuffer\n')
        j.write('if [ -d "/mnt/resource/" ]; then\n')
        j.write(
            '    localscratch="/mnt/resource/temp_scratch_$SLURM_JOB_ID"\n'
            '    mkdir $localscratch\n'
        )
        j.write('else\n')
        j.write('    localscratch=$BURSTBUFFER\n')
        j.write('fi\n\n')

        j.write('# Copy files to localscratch\n')
        j.write('rsync -aP ')

        j.write(f'$campaigndir/{in_raw}')

        for dep in dependencies:
            j.write(f' {dep}')

        j.write(' $localscratch\n')
        j.write('cd $localscratch\n\n')

        j.write('# write date and node type to output\n')
        j.write('date > $campaigndir/$output\n')
        j.write('uname -n >> $campaigndir/$output\n\n')

        j.write('# Module system setup\n')
        j.write('source /apps/build/easy_build/scripts/id_instance.sh\n')
        j.write('source /apps/build/easy_build/scripts/setup_modules.sh\n\n')

        j.write('# Load orca\n')
        j.write('module purge\n')
        j.write('module load ORCA/5.0.1-gompi-2021a\n\n')

        j.write('# UCX transport protocols for MPI\n')
        j.write('export UCX_THS=self,tcp,sm\n\n')

        j.write('# If timeout, evicted, cancelled, then manually end orca\n')

        j.write("trap 'echo signal recieved in BATCH!; kill -15 ")
        j.write('"${PID}"; wait "${PID}";')
        j.write("' SIGINT SIGTERM USR1 15\n\n")

        j.write('# Run calculation in background\n')
        j.write('# Catch the PID var for trap, and wait for process to end\n')
        j.write('$(which orca) $input >> $campaigndir/$output &\n')
        j.write('PID="$!"\n')
        j.write('wait "${PID}"\n\n')

        j.write('Clean up and copy back files\n')
        j.write('rsync -aP --exclude=*.tmp* $localscratch/* $results\n')
        j.write('rm -r $localscratch\n')

    if verbose:
        if os.path.split(input_file)[0] == os.getcwd():
            pp_jf = os.path.split(input_file)[1]
        else:
            pp_jf = job_file
        ut.cprint(f'Submission script written to {pp_jf}', 'green')

    return job_file


def check_envvar(var_str: str) -> None:
    '''
    Checks specified environment variable has been defined, exits program if
    variable is not defined

    Parameters
    ----------
    var_str : str
        String name of environment variable

    Returns
    -------
    None
    '''

    try:
        os.environ[var_str]
    except KeyError:
        sys.exit('Please set ${} environment variable'.format(var_str))

    return


def parse_input_contents(input_file: str, max_mem: int) -> str:
    '''
    Checks contents of input file and returns file dependencies
    Specific checks:
        If specified xyz file exists
        If specified gbw file exists
        If maxcore (memory) specified is appropriate

    Parameters
    ----------
    input_file : str
        Full path to orca input file
    max_mem : int
        Max memory (MB) per core on given node

    Returns
    -------
    dict[str: str]
        Names of dependencies (files) which this input needs
        key is identifier (xyz, gbw), value is file name
    '''

    # Found memory definition
    mem_found = False

    # MO Sections
    mo_read = False
    mo_inp = False

    # Dependencies (files) of this input file
    # as full paths
    dependencies = dict()

    # Path of input file
    inpath = os.path.split(input_file)[0]

    # If input file is in cwd then no need to print massive path for errors
    if inpath == os.getcwd():
        e_input_file = os.path.split(input_file)[1]
    else:
        e_input_file = input_file


    with open(input_file, 'r') as f:
        for line in f:

            # xyz file
            if 'xyzfile' in line.lower():
                if len(line.split()) != 5 and line.split()[0] != '*xyzfile':
                    ut.red_exit(
                        f'Incorrect xyzfile definition in {e_input_file}'
                    )

                if len(line.split()) != 4 and line.split()[0] != '*':
                    ut.red_exit(
                        f'Incorrect xyzfile definition in {e_input_file}'
                    )

                xyzfile = line.split()[-1]

                # Check if absolute, if not then absolutize using input path
                if not os.path.isabs(xyzfile):
                    xyzfile = os.path.join(inpath, xyzfile)

                dependencies['xyz'] = os.path.abspath(xyzfile)

            # gbw file
            if '%moinp' in line.lower():
                mo_inp = True
                if len(line.split()) != 2:
                    ut.red_exit(
                        f'Incorrect gbw_file definition in {e_input_file}'
                    )

                gbw_file = line.split()[-1].replace('"', '').replace("'", "")

                # Check if absolute, if not then absolutize using input path
                if not os.path.isabs(gbw_file):
                    gbw_file = os.path.join(inpath, gbw_file)

                dependencies['gbw'] = os.path.abspath(gbw_file)

            if 'moread' in line.lower():
                mo_read = True

            # Per core memory
            if '%maxcore' in line.lower():
                mem_found = True

                if len(line.split()) != 2:
                    ut.red_exit(
                        f'Incorrect %maxcore definition in {e_input_file}'
                    )

                try:
                    n_try = int(line.split()[-1])
                except ValueError:
                    ut.red_exit(
                        f'Cannot parse per core memory in {e_input_file}'
                    )
                if n_try > max_mem:
                    ut.red_exit(
                        f'Specified per core memory in {e_input_file} exceeds node limit' # noqa
                    )

    if mo_inp ^ mo_read:
        ut.red_exit(
            f'Only one of moread and %moinp specified in {e_input_file}'
        )

    if not mem_found:
        ut.red_exit(f'Cannot locate %maxcore definition in {e_input_file}')

    return dependencies


def check_dependencies(files: dict[str: str], input_file: str):
    '''
    Checks the existence of each file in a dict of files with absolute path

    Parameters
    ----------
    files: dict[str: str]
        Keys are filetype e.g. xyz, gbw
        Values are absolute path of file
    input_file: str
        Name of input file, used in error message if dependencies cannot be found
    '''

    for file_type, file_name in files.items():
        if not os.path.exists(file_name):
            ut.red_exit(
                f'{file_type} file specified in {input_file} cannot be found'
            )

    return


def add_core_to_input(input_file: str, n_cores: int) -> None:
    '''
    Adds number of cores (NPROCS) definition to specified input file

    Parameters
    ----------
    input_file : str
        Name of orca input file
    n_cores : int
        Number of cores to specify

    Returns
    -------
    None
    '''

    found = False

    new_file = '{}_tmp'.format(input_file)

    with open(input_file, 'r') as fold:
        with open(new_file, 'w') as fnew:

            # Find line if already exists
            for oline in fold:
                # Number of cores
                if 'pal nprocs' in oline.lower():
                    fnew.write('%PAL NPROCS {:d} END\n'.format(n_cores))
                    found = True
                else:
                    fnew.write('{}'.format(oline))

            # Add if missing
            if not found:
                fnew.write('\n%PAL NPROCS {:d} END\n'.format(n_cores))

    subprocess.call('mv {} {}'.format(new_file, input_file), shell=True)

    return
