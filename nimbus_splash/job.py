import os
import sys

from .utils import red_exit


def write_file(input_file: str, node_type: str, time: str,
               verbose: bool = False) -> str:
    """
    Writes slurm jobscript to file for ORCA calculation on nimbus

    Output file name is input_file with .slm extension

    Parameters
    ----------
    input_file : str
        Name of input file, including extension
    node_type : str
        Name of Nimbus node to use
    time : str
        Job time limit formatted as HH:MM:SS
    verbose : bool, default=False
        If True, prints job file name to screen


    Returns
    -------
    str
        Name of jobscript file
    """

    # Check for research allocation id environment variable
    check_envvar('CLOUD_ACC')

    job_name = os.path.splitext(input_file)[0]

    job_file = "{}.slm".format(
        job_name
    )

    with open(job_file, 'w') as j:

        j.write('#!/bin/bash\n\n')

        j.write('#SBATCH --job-name={}\n'.format(job_name))
        j.write('#SBATCH --nodes=1\n')
        j.write('#SBATCH --ntasks-per-node={}\n'.format(
            node_type.split('-')[-1])
        )
        j.write('#SBATCH --partition={}\n'.format(node_type))
        j.write('#SBATCH --account={}\n'.format(os.environ['CLOUD_ACC']))
        j.write('#SBATCH --qos={}\n'.format(node_type))
        j.write('#SBATCH --output={}.%j.o\n'.format(job_name))
        j.write('#SBATCH --error={}.%j.e\n\n'.format(job_name))

        j.write('# Job time\n')
        j.write('#SBATCH --time={}\n\n'.format(time))

        j.write('# name and path of the output file\n')
        j.write('input={}\n'.format(input_file))
        j.write('output={}.out\n'.format(job_name))
        j.write('campaigndir=$(pwd -P)\n\n')

        j.write('# Local (Node) scratch, either node itself if supported or burstbuffer\n') # noqa
        j.write('if [ -d "/mnt/resource/" ]; then\n')
        j.write(
            '    localscratch="/mnt/resource/temp_scratch_$SLURM_JOB_ID"\n'
            '    mkdir $localscratch\n'
        )
        j.write('else\n')
        j.write('    localscratch=$BURSTBUFFER\n')
        j.write('fi\n\n')

        j.write('# Copy files to localscratch\n')
        j.write('rsync -aP --exclude={} $campaigndir/ $localscratch\n'.format(
            job_file
        ))
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

        j.write('# If sigterm (eviction) copy files before job is killed\n')
        j.write('trap "rsync -aP --exclude=*.tmp $localscratch/*')
        j.write('$campaigndir; exit 15" 15\n')

        j.write('# If node dies copy files before job is killed\n')
        j.write('trap "rsync -aP --exclude=*.tmp $localscratch/*')
        j.write('$campaigndir; exit 1" 1\n')

        j.write('# If time limit reached, copy files before job is killed\n')
        j.write('trap "rsync -aP --exclude=*.tmp $localscratch/*')
        j.write('$campaigndir; exit 9" 9\n')

        j.write('# run the calculation and clean up\n')
        j.write('$(which orca) $input >> $campaigndir/$output\n\n')

        j.write('rm *.tmp\n')
        j.write('rsync -aP $localscratch/* $campaigndir\n')
        j.write('rm -r $localscratch\n')

    if verbose:
        print("\u001b[32m Submission script written to {} \033[0m".format(
            job_file
        ))

    return job_file


def check_envvar(var_str: str) -> None:
    """
    Checks specified environment variable has been defined, exits program if
    variable is not defined

    Parameters
    ----------
    var_str : str
        String name of environment variable

    Returns
    -------
    None
    """

    try:
        os.environ[var_str]
    except KeyError:
        sys.exit("Please set ${} environment variable".format(var_str))

    return


def check_input_contents(file: str, n_cores: int, max_mem: int) -> str:
    """
    Checks contents of input file.
    Specifically:
        If specified xyz file exists
        If maxcore (memory) specified is appropriate
        If specified number of cores matches number on node

    Parameters
    ----------
    var_str : str
        String name of environment variable

    Returns
    -------
    None
    """

    # Found number of cores definition
    pal_found = False

    # Found memory definition
    mem_found = False

    with open(file, 'r') as f:
        for line in f:

            # xyz file
            if 'xyzfile' in line.lower():
                xyzfile = line.split()[-1]
                if not os.path.exists(xyzfile):
                    red_exit("Error: specified xyz file does not exist")

            # Number of cores
            if '%pal nprocs' in line.lower():
                pal_found = True

                if len(line.split()) != 4:
                    red_exit("Incorrect %PAL definition")

                try:
                    n_try = int(line.split()[-2])
                except ValueError:
                    red_exit(
                        "Cannot parse number of cores in input file"
                    )
                if n_try != n_cores:
                    red_exit(
                        "Number of cores in input does not match node"
                    )

            # Number of cores
            if '%maxcore' in line.lower():
                mem_found = True

                if len(line.split()) != 2:
                    red_exit("Incorrect %maxcore definition")

                try:
                    n_try = int(line.split()[-1])
                except ValueError:
                    red_exit(
                        "Cannot parse per core memory in input file"
                    )
                if n_try > max_mem:
                    red_exit(
                        "Specified per core memory in input exceeds node limit"
                    )

    if not pal_found:
        red_exit("Cannot locate %PAL definition in input file")

    if not mem_found:
        red_exit("Cannot locate %maxcore definition in input file")

    return
