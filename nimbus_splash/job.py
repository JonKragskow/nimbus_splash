import os
import subprocess

from . import utils as ut

ORCA_MODULE = 'ORCA/5.0.4'


def write_file(input_file: str, node_type: str, time: str,
               dependency_paths: dict[str, str],
               verbose: bool = False,
               email: str = '') -> str:
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
    dependency_paths : list[str]
        Full path to each file required by this job
    email: str, optional
        If provided, adds the specified email to the jobscript.\n
        Users recieve an email for all changes in job status

    Returns
    -------
    str
        Name of jobscript file
    '''

    # Check for research allocation id environment variable
    ut.check_envvar('SPLASH_RAID')

    # Get raw name of input file excluding path
    inpath, in_raw = os.path.split(input_file)

    # Name of job
    job_name = ut.gen_job_name(input_file)

    # Name of results directory
    results_name = ut.gen_results_name(input_file)

    # Job file to write to, must use path if present in input_file
    job_file = os.path.join(
        inpath,
        f'{job_name}.slm'
    )

    # Path of input file
    calc_dir = os.path.abspath(inpath)

    with open(job_file, 'w') as j:

        j.write('#!/bin/bash\n\n')

        j.write(f'#SBATCH --job-name={job_name}\n')
        j.write('#SBATCH --nodes=1\n')
        j.write('#SBATCH --ntasks-per-node={}\n'.format(
            node_type.split('-')[-1])
        )
        j.write(f'#SBATCH --partition={node_type}\n')
        j.write('#SBATCH --account={}\n'.format(os.environ['SPLASH_RAID']))
        j.write(f'#SBATCH --qos={node_type}\n')
        j.write(f'#SBATCH --output={job_name}.%j.o\n')
        j.write(f'#SBATCH --error={job_name}.%j.e\n')

        if len(email):
            j.write(f'#SBATCH --mail-user={email}\n')
            j.write('#SBATCH --mail-type=ALL\n')

        j.write('#SBATCH --signal=B:USR1\n\n')

        j.write('# Job time\n')
        j.write(f'#SBATCH --time={time}\n\n')

        j.write('# name and path of the input/output files and locations\n')
        j.write(f'input={in_raw}\n')
        j.write(f'output={job_name}.out\n')
        j.write(f'campaigndir={calc_dir}\n')
        j.write(f'results=$campaigndir/{results_name}\n\n')

        j.write('# Local (Node) scratch, either node itself if supported ')
        j.write('or burstbuffer\n')
        j.write('if [ -d "/mnt/resource/" ]; then\n')
        j.write(
            '    localscratch="/mnt/resource/temp_scratch_$SLURM_JOB_ID"\n'
            '    mkdir $localscratch\n'
        )
        j.write('else\n')
        j.write('    localscratch=$BURSTBUFFER\n')
        j.write('fi\n\n')

        j.write('# If output file already exists, append OLD and ')
        j.write('last access time\n')
        j.write('if [ -f $output ]; then\n')
        j.write(
            '    mv $output "$output"_OLD_$(date -r $output "+%Y-%m-%d-%H-%M-%S")\n') # noqa
        j.write('fi\n\n')

        j.write('# Copy files to localscratch\n')
        j.write('rsync -aP ')

        j.write(f'{input_file}')

        for dep in dependency_paths:
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
        j.write(f'module load {ORCA_MODULE}\n\n')

        j.write('# UCX transport protocols for MPI\n')
        j.write('export UCX_TLS=self,tcp,sm\n\n')

        j.write('# If timeout, evicted, cancelled, then manually end orca\n')

        j.write("trap 'echo signal recieved in BATCH!; kill -15 ")
        j.write('"${PID}"; wait "${PID}";')
        j.write("' SIGINT SIGTERM USR1 15\n\n")

        j.write('# Run calculation in background\n')
        j.write('# Catch the PID var for trap, and wait for process to end\n')
        j.write('$(which orca) $input >> $campaigndir/$output &\n')
        j.write('PID="$!"\n')
        j.write('wait "${PID}"\n\n')

        j.write('# Clean up and copy back files\n')

        j.write('# Check for existing results directory\n')
        j.write('cd $campaigndir\n')
        j.write('# If results directory already exists, append OLD and ')
        j.write('last access time\n')
        j.write('if [ -d $results ]; then\n')
        j.write(
            '    mv $results "$results"_OLD_$(date -r $results "+%Y-%m-%d-%H-%M-%S")\n') # noqa
        
        j.write('else')
        j.write('    mkdir $results')
        j.write('fi\n\n')
        j.write('cd $localscratch\n')

        j.write(
            'if compgen -G "$localscratch/*.res.Gradients" > /dev/null; then\n'
            '    rsync -aP --exclude=*.tmp* $localscratch/*.res.Gradients $results\n' # noqa
            'fi\n'
        )
        j.write(
            'if compgen -G "$localscratch/*.res.Dipoles" > /dev/null; then\n'
            '    rsync -aP --exclude=*.tmp* $localscratch/*.res.Dipoles $results\n' # noqa
            'fi\n'
        )
        j.write(
            'if compgen -G "$localscratch/*.res.Ramans" > /dev/null; then\n'
            '    rsync -aP --exclude=*.tmp* $localscratch/*.res.Ramans $results\n' # noqa
            'fi\n'
        )
        j.write(
            'if compgen -G "$localscratch/*.res.Nacmes" > /dev/null; then\n'
            '    rsync -aP --exclude=*.tmp* $localscratch/*.res.Nacmes $results\n' # noqa
            'fi\n'
        )

        j.write('rsync -aP --exclude=*.tmp* $localscratch/* $results\n')
        j.write('rm -r $localscratch\n')

    if verbose:
        if os.path.split(job_file)[0] == os.getcwd():
            pp_jf = os.path.split(job_file)[1]
        else:
            pp_jf = job_file
        ut.cprint(f'Submission script written to {pp_jf}', 'green')

    return job_file


def parse_input_contents(input_file: str, max_mem: int,
                         max_cores: int) -> dict[str, str]:
    '''
    Checks contents of input file and returns file dependencies\n
    Also checks if maxcore (memory) specified is appropriate

    Parameters
    ----------
    input_file : str
        Full path to orca input file
    max_mem : int
        Max memory (MB) total on node
    max_cores : int
        Maximum number of cores on node

    Returns
    -------
    dict[str, str]
        Relative paths of files required by this this input file\n
        Key is identifier (xyz, gbw, hess), Value is file name
    '''

    # Found memory and cores
    mem_found = False
    core_found = False

    # MO Sections
    mo_read = False
    mo_inp = False

    # Dependencies (files) of this input file
    # as full paths
    dependencies = dict()

    # Path of input file
    inpath = os.path.split(input_file)[0]

    # head of input file
    inhead = os.path.split(os.path.splitext(input_file)[0])[1]

    # If input file is in cwd then no need to print massive path for errors
    if inpath == os.getcwd():
        e_input_file = os.path.split(input_file)[1]
    else:
        e_input_file = input_file

    with open(input_file, 'r') as f:
        for line in f:

            # xyz file
            if 'xyzfile' in line.lower() and '!' not in line:
                if len(line.split()) != 5 and line.split()[0] != '*xyzfile':
                    ut.red_exit(
                        f'Incorrect xyzfile definition in {e_input_file}'
                    )

                if len(line.split()) != 4 and line.split()[0] != '*':
                    ut.red_exit(
                        f'Incorrect xyzfile definition in {e_input_file}'
                    )

                xyzfile = line.split()[-1]

                # Check if contains path info, if so error
                if os.sep in xyzfile:
                    ut.red_exit(
                        f'Path provided for xyz file in {e_input_file}'
                    )

                dependencies['xyz'] = xyzfile

            # gbw file
            if '%moinp' in line.lower():
                mo_inp = True
                if len(line.split()) != 2:
                    ut.red_exit(
                        f'Incorrect gbw file definition in {e_input_file}'
                    )
                if abs(line.count('"') - line.count("'")) != 2:
                    ut.red_exit(
                        f'Missing quotes around gbw file name in {e_input_file}' # noqa
                    )

                gbw_file = line.split()[-1].replace('"', '').replace("'", "")

                # Check if contains path info, if so error
                if os.sep in gbw_file:
                    ut.red_exit(
                        f'Path provided for gbw file in {e_input_file}'
                    )
                dependencies['gbw'] = gbw_file

                # Check gbw doesnt have same name as input
                if os.path.splitext(gbw_file)[0] == inhead:
                    ut.red_exit(
                        f'gbw file in {e_input_file} has same name as input'
                    )

            if 'hessname' in line.lower():
                if len(line.split()) != 2:
                    ut.red_exit(
                        f'Incorrect hessian file definition in {e_input_file}'
                    )
                if abs(line.count('"') - line.count("'")) != 2:
                    ut.red_exit(
                        f'Missing quotes around hessian file name in {e_input_file}' # noqa
                    )

                hess_file = line.split()[-1].replace('"', '').replace("'", "")

                # Check if contains path info, if so error
                if os.sep in hess_file:
                    ut.red_exit(
                        f'Path provided for hessian file in {e_input_file}'
                    )
                # Check hess doesnt have same name as input
                if os.path.splitext(hess_file)[0] == inhead:
                    ut.red_exit(
                        f'hessian file in {e_input_file} has same name as input' # noqa
                    )
                dependencies['hess'] = hess_file

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
                    n_mb = int(line.split()[-1])
                except ValueError:
                    ut.red_exit(
                        f'Cannot parse per core memory in {e_input_file}'
                    )

            # Number of cores
            if 'pal nprocs' in line.lower():
                n_cores = int(line.split()[2])
                core_found = True

                if n_cores > max_cores:

                    string = 'Error: Specified number of cores'
                    string += f' {n_cores:d} in {input_file} exceeds '
                    string += f'node limit of {max_cores:d} cores'

                    ut.red_exit(string)

    if mo_inp ^ mo_read:
        ut.red_exit(
            f'Only one of moread and %moinp specified in {e_input_file}'
        )

    if not core_found:
        n_cores = max_cores
        ut.cprint(
            f'Cannot locate %pal nprocs definition in {e_input_file}',
            'black_yellowbg'
        )
        ut.cprint(
            f'Adding {max_cores:d} cores to input file\n',
            'black_yellowbg'
        )
        add_core_to_input(input_file, n_cores)

    if not mem_found:
        n_mb = max_mem / n_cores
        ut.cprint(
            f'Cannot locate %maxcore definition in {e_input_file}',
            'black_yellowbg'
        )
        ut.cprint(
            f'Adding {n_mb:.0f}MB of memory to input file\n',
            'black_yellowbg'
        )
        add_mem_to_input(input_file, n_mb)

    # Check memory doesnt exceed per-core limit
    if n_mb > max_mem / n_cores:

        string = 'Warning! Specified per core memory of'
        string += f' {n_mb:d} MB in {input_file} exceeds'
        string += ' node limit of {:.2f} MB'.format(max_mem / n_cores)

        ut.cprint(string, 'black_yellowbg')

    return dependencies


def locate_dependencies(files: dict[str, str],
                        input_file: str) -> dict[str, str]:
    '''
    Locates each dependency in either input directory or results directory

    Parameters
    ----------
    files: dict[str, str]
        Keys are filetype [xyz, gbw] \n
        Values are name file (no path information)
    input_file: str
        Full path of input file

    Returns
    -------
    dict[str, str]
        Absolute path of each file, keys are same as `files`.
    '''

    results_name = ut.gen_results_name(input_file)
    in_path = os.path.split(input_file)[0]

    dependency_paths = {}

    for file_type, file_name in files.items():

        # Potential path of current file if in input directory
        curr = os.path.join(in_path, file_name)
        # Potential path of current file if in results directory
        res = os.path.join(in_path, results_name, file_name)

        # gbw check both currdir/results_name and then currdir
        if file_type == 'gbw':
            if os.path.exists(res):
                dependency_paths[file_type] = os.path.abspath(res)
            elif os.path.exists(curr):
                dependency_paths[file_type] = os.path.abspath(curr)
            else:
                ut.red_exit(
                    f'{file_type} file specified in {input_file} cannot be found' # noqa
                )
        else:
            if os.path.exists(curr):
                dependency_paths[file_type] = os.path.abspath(curr)
            else:
                ut.red_exit(
                    f'{file_type} file specified in {input_file} cannot be found' # noqa
                )

    return dependency_paths


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

    new_file = f'{input_file}_tmp'

    with open(input_file, 'r') as fold:
        with open(new_file, 'w') as fnew:

            # Find line if already exists
            for oline in fold:
                # Number of cores
                if '%pal nprocs' in oline.lower():
                    fnew.write(f'%PAL NPROCS {n_cores:d} END\n')
                    found = True
                else:
                    fnew.write('{}'.format(oline))

            # Add if missing
            if not found:
                fnew.write(f'%PAL NPROCS {n_cores:d} END\n')

    subprocess.call('mv {} {}'.format(new_file, input_file), shell=True)

    return


def add_mem_to_input(input_file: str, mem: float) -> None:
    '''
    Adds memory (maxcore) definition to specified input file

    Parameters
    ----------
    input_file : str
        Name of orca input file
    mem : int
        Amount of memory to specify in MB

    Returns
    -------
    None
    '''

    found = False

    new_file = f'{input_file}_tmp'

    with open(input_file, 'r') as fold:
        with open(new_file, 'w') as fnew:

            # Find line if already exists
            for oline in fold:
                # Number of cores
                if '%maxcore' in oline.lower():
                    fnew.write(f'%maxcore {mem:f}\n')
                    found = True
                else:
                    fnew.write('{}'.format(oline))

            # Add if missing
            if not found:
                fnew.write(f'%maxcore {mem:.0f}\n')

    subprocess.call('mv {} {}'.format(new_file, input_file), shell=True)

    return
