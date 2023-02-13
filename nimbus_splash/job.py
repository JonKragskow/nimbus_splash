import os
import sys


def write_file(input_file, node_type):
    """
    Writes slurm jobscript to file for ORCA calculation on nimbus

    Output file name is input_file with .slm extension

    Parameters
    ----------
    input_file : str
        Name of input file, including extension
    node_type : str
        Name of Nimbus node to use
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
        j.write('#SBATCH --ntasks-per-node=16\n')
        j.write('#SBATCH --partition={}\n'.format(node_type))
        j.write('#SBATCH --account={}\n'.format(os.environ['CLOUD_ACC']))
        j.write('#SBATCH --qos={}\n'.format(node_type))
        j.write('#SBATCH --output={}.%j.o\n'.format(job_name))
        j.write('#SBATCH --error={}.%j.e\n\n'.format(job_name))

        j.write('# Job time\n')
        j.write('#SBATCH --time=6:00:00\n\n')

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

        j.write('# run the calculation and clean up\n')
        j.write('$(which orca) $input >> $campaigndir/$output\n\n')

        j.write('rm *.tmp\n')
        j.write('rsync -aP $localscratch/* $campaigndir\n')
        j.write('rm -r $localscratch\n')

    return


def check_envvar(var_str):
    """
    Checks specified environment variable has been defined, exits program if
    variable is not defined

    Parameters
    ----------
    var_str : str
        String name of environment variable

    """

    try:
        os.environ[var_str]
    except KeyError:
        sys.exit("Please set ${} environment variable".format(var_str))
    
    return
