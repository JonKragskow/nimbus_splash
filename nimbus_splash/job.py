import os
import sys
import subprocess

from .utils import red_exit


def write_file(input_file: str, node_type: str, time: str,
               verbose: bool = False, dependencies: list[str] = []) -> str:
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
    dependencies : list[str]
        Additional files on which this job depends, these will be copied
        to the compute node at runtime

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

        j.write('# name and path of the input/output files and locations\n')
        j.write('input={}\n'.format(input_file))
        j.write('output={}.out\n'.format(job_name))
        j.write('campaigndir=$(pwd -P)\n')
        j.write('results=$campaigndir/{}\n\n'.format(job_name))

        j.write('# If results directory already exists, append OLD and ')
        j.write('last access time\n')
        j.write('if [ -d $results ]; then\n')
        j.write(
            '    mv $results $"results"_OLD_$(date -r $results "+%m-%d-%Y")\n')
        j.write('fi\n\n')

        j.write('# If output file already exists, append OLD and ')
        j.write('last access time\n')
        j.write('if [ -d $output ]; then\n')
        j.write(
            '    mv $output $"output"_OLD_$(date -r $output "+%m-%d-%Y")\n')
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
        j.write("rsync -aP '")

        j.write('$campaigndir/{}'.format(input_file))

        for dep in dependencies:
            j.write(' {}'.format(dep))

        j.write("' $localscratch\n")
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
        j.write(' $results; exit 15" 15\n\n')

        j.write('# If node dies copy files before job is killed\n')
        j.write('trap "rsync -aP --exclude=*.tmp $localscratch/*')
        j.write(' $results; exit 1" 1\n\n')

        j.write('# If time limit reached, copy files before job is killed\n')
        j.write('trap "rsync -aP --exclude=*.tmp $localscratch/*')
        j.write(' $results; exit 9" 9\n\n')

        j.write('# run the calculation and clean up\n')
        j.write('$(which orca) $input >> $campaigndir/$output\n\n')

        j.write('rm *.tmp\n')
        j.write('rsync -aP $localscratch/* $results\n')
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


def parse_input_contents(input_file: str, max_mem: int) -> str:
    """
    Checks contents of input file and returns file dependencies
    Specific checks:
        If specified xyz file exists
        If specified gbw file exists
        If maxcore (memory) specified is appropriate

    Parameters
    ----------
    input_file : str
        Name of orca input file
    max_mem : int
        Max memory (MB) per core on given node

    Returns
    -------
    list[str]
        Name of dependencies (files) which this input needs
    """

    # Found memory definition
    mem_found = False

    # Dependencies (files) of this input file
    dependencies = []

    with open(input_file, 'r') as f:
        for line in f:

            # xyz file
            if 'xyzfile' in line.lower():
                if len(line.split()) != 5 and line.split()[0] != '*xyzfile':
                    red_exit("Incorrect xyzfile definition")

                if len(line.split()) != 4 and line.split()[0] != '*':
                    red_exit("Incorrect xyzfile definition")

                xyzfile = line.split()[-1]

                if not os.path.exists(xyzfile):
                    red_exit("specified xyz file does not exist")

                dependencies.append(xyzfile)

            # gbw file
            if '%moinp' in line.lower():
                if len(line.split()) != 2:
                    red_exit("Incorrect gbwfile definition")

                gbwfile = line.split()[-1].replace('"', '').replace("'", "")

                if os.path.splitext(gbwfile) == os.path.splitext(input_file):
                    red_exit("GBW file cannot have same base name as input")

                if not os.path.exists(gbwfile):
                    red_exit("specified gbw file does not exist")
                dependencies.append(gbwfile)

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

    if not mem_found:
        red_exit("Cannot locate %maxcore definition in input file")

    return dependencies


def add_core_to_input(input_file: str, n_cores: int) -> None:
    """
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
    """

    new_file = "{}_tmp".format(input_file)

    with open(input_file, 'r') as fold:
        with open(new_file, 'w') as fnew:

            # Find line if already exists
            for oline in fold:
                # Number of cores
                if 'pal nprocs' in oline.lower():
                    fnew.write("%PAL NPROCS {:d} END\n".format(n_cores))
                else:
                    fnew.write("{}".format(oline))

    subprocess.call("mv {} {}".format(new_file, input_file), shell=True)

    return
