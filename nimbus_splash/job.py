import pathlib
from orto import extractor as oe
import xyz_py as xyzp
import warnings

from . import utils as ut
from . import config as cfg


def write_file(input_file: str | pathlib.Path, instance_name: str, time: str,
               dependencies: dict[str, str | pathlib.Path],
               orca_version: str, research_allocation_id: str,
               verbose: bool = False, email: str = '',
               job_name: str = None) -> str:
    '''
    Writes slurm jobscript to file for ORCA calculation on nimbus

    Output file name is input_file with .slm extension

    Parameters
    ----------
    input_file : str | pathlib.Path
        Full path to input file, including extension
    instance_name : str
        Name of Nimbus instance to use e.g. spot-hc-44
    time : str
        Job time limit formatted as HH:MM:SS
    verbose : bool, default=False
        If True, prints job file name to screen
    dependencies : dict[str | pathlib.Path]
        Files required by job - e.g. xyz, gbw, hess
    orca_version: str
        string name of orca version
        e.g. 5.0.4
    research_allocation_id: str
        Research allocation ID
    email: str, optional
        If provided, adds the specified email to the jobscript.\n
        Users recieve an email for all changes in job status
    job_name: str, optional
        Name of job. If not provided, then job name defaults to stem of
        input file

    Returns
    -------
    str
        Name of jobscript file

    Raises
    ------
    ValueError
        If ORCA version not available on instance
    '''

    # Check instance's ORCA compatibility
    if instance_name not in cfg.ORCA_SUPPORTED_INSTANCES:
        raise ValueError(
            f'Specified instance {instance_name} does not support ORCA'
        )

    # Find relevant orca module for given instance
    try:
        orca_module = cfg.ORCA_MODULES[instance_name.split('-')[1]][orca_version] # noqa
    except KeyError:
        raise ValueError(
            f'ORCA version {orca_version} not available on instance {instance_name}' # noqa
        )

    # Get raw name of input file excluding path
    input_file = pathlib.Path(input_file)

    # Convert dependencies to Path objects
    dependencies: list[pathlib.Path] = [
        pathlib.Path(dep) for dep in dependencies
    ]

    # Name of job
    if job_name is None:
        job_name = input_file.stem

    job_file = pathlib.Path.joinpath(input_file.parent, f'{job_name}.slm')

    with open(job_file, 'w') as j:

        j.write('#!/bin/bash\n\n')

        j.write(f'#SBATCH --job-name={job_name}\n')
        j.write('#SBATCH --nodes=1\n')
        j.write('#SBATCH --ntasks-per-node={}\n'.format(
            cfg.INSTANCE_TOTAL_CORES[instance_name]
        ))
        j.write(f'#SBATCH --partition={instance_name}\n')
        j.write(f'#SBATCH --account={research_allocation_id}\n')
        j.write(f'#SBATCH --qos={instance_name}\n')
        j.write(f'#SBATCH --output={job_name}.%j.o\n')
        j.write(f'#SBATCH --error={job_name}.%j.e\n')

        # Stop slurm from killing the job if the node fails
        # and stop slurm from resubmitting the job if the node fails
        # n.b. this also prevents a requeue in the case of a higher priority
        # job pushing this one off of the node - swings and roundabouts!
        j.write('#SBATCH --no-kill\n')
        j.write('#SBATCH --no-requeue\n')

        if len(email):
            j.write(f'#SBATCH --mail-user={email}\n')
            j.write('#SBATCH --mail-type=ALL\n')

        j.write('#SBATCH --signal=B:USR1\n\n')

        j.write('# Job time\n')
        j.write(f'#SBATCH --time={time}\n\n')

        j.write('# This job script was written by nimbus_splash')

        j.write('# name and path of the input/output files and locations\n')
        j.write(f'input={input_file}\n')
        j.write(f'output={job_name}.out\n')
        j.write(f'campaigndir={input_file.parent.absolute()}\n')
        j.write(f'results=$campaigndir/{input_file.stem}_results\n\n')

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
        j.write('    mv $output "$output"_OLD_$(date -r $output "+%Y-%m-%d-%H-%M-%S")\n') # noqa
        j.write('fi\n\n')

        j.write('# Copy files to localscratch\n')
        j.write('rsync -aP ')

        j.write(f'{input_file.absolute()}')

        for dep in dependencies:
            j.write(f' {dep.absolute()}')

        j.write(' $localscratch\n')
        j.write('cd $localscratch\n\n')

        j.write('# Write date and instance type to output\n')
        j.write('date > $campaigndir/$output\n')
        j.write('uname -n >> $campaigndir/$output\n\n')

        j.write('# Module system setup\n')
        j.write('source /apps/build/easy_build/scripts/id_instance.sh\n')
        j.write('source /apps/build/easy_build/scripts/setup_modules.sh\n\n')

        j.write('# Load orca\n')
        j.write('module purge\n')
        j.write(f'module load {orca_module}\n\n')

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

        j.write('else\n')
        j.write('    mkdir $results\n')
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
        if job_file.parent == pathlib.Path.cwd():
            ut.cprint(f'Submission script written to {job_file.name}', 'green')
        else:
            ut.cprint(f'Submission script written to {job_file}', 'green')

    return job_file


def parse_input_contents(input_file: str | pathlib.Path,
                         instance_name: str,
                         skip_xyz: bool = False) -> dict[str, pathlib.Path]:
    '''
    Checks contents of input file and returns file dependencies\n

    Parameters
    ----------
    input_file: str | pathlib.Path
        Full path to orca input file
    instance_name: str
        Name of Nimbus instance e.g. spot-fsv2-32
    skip_xyz: bool, default False
        If True, skips checking of xyz file formatting

    Returns
    -------
    dict[str, pathlib.Path]
        Relative paths of files required by this this input file\n
        Key is identifier (xyz, gbw, hess), Value is file name as Path object

    Raises
    ------
    ValueError
        If errors encountered in input file format or xyz file format
    FileNotFound
        If xyz, gbw, or hessian file cannot be found
    '''

    # Convert to Path object
    input_file = pathlib.Path(input_file)

    # Dependencies (files) of this input file
    dependencies = dict()

    # Load number of procs and amount of memory from orca input file
    try:
        n_procs = oe.NProcsInputExtractor.extract(input_file)[0]
    except oe.DataNotFoundError:
        raise ValueError(f'Missing Number of processors in {input_file}')

    try:
        maxcore = oe.MaxCoreInputExtractor.extract(input_file)[0]
    except oe.DataNotFoundError:
        raise ValueError(f'Missing Max Core Memory in {input_file}')

    # Check against selected instance
    if n_procs > cfg.INSTANCE_TOTAL_CORES[instance_name]:
        string = 'Error: Specified number of cores'
        string += f' {n_procs:d} in {input_file} exceeds '
        string += f'instance limit of {cfg.INSTANCE_TOTAL_CORES[instance_name]:d} cores' # noqa
        raise ValueError(string)

    # Check against selected instance
    if maxcore * n_procs > cfg.INSTANCE_TOTAL_MEM[instance_name]:
        string = 'Warning: Specified amount of memory'
        string += f' {maxcore:d} * {n_procs:d} = {n_procs*maxcore:d} in {input_file} exceeds ' # noqa
        string += f'instance limit of {cfg.INSTANCE_TOTAL_MEM[instance_name]:d} MB' # noqa
        warnings.warn(string)

    # Get xyz file name and check it exists and is formatted correctly
    try:
        xyz_file = oe.XYZFileInputExtractor.extract(input_file)
    except oe.DataNotFoundError:
        xyz_file = []

    try:
        xyzline = oe.XYZInputExtractor.extract(input_file)
    except oe.DataNotFoundError:
        xyzline = []

    if not len(xyz_file) and not len(xyzline):
        raise ValueError(
            'Error: missing or incorrect *xyzfile or *xyz line in input'
        )

    if len(xyz_file) > 1 or len(xyzline) > 1 or len(xyz_file + xyzline) > 1: # noqa
        raise ValueError(
            'Error: multiple *xyzfile or *xyz lines in input. Only one can be present' # noqa
        )

    if len(xyz_file):
        xyz_file = pathlib.Path(xyz_file[0])
        if not xyz_file.is_file():
            raise FileNotFoundError(
                'Error: xyz file specified in input cannot be found'
            )
        dependencies['xyz'] = xyz_file

        if not skip_xyz:
            try:
                xyzp.check_xyz(
                    xyz_file.absolute(),
                    allow_indices=False
                )
            except xyzp.XYZError as e:
                raise ValueError(
                    f'{e}\n Use -sx to skip this check at your peril'
                )

    # Check if MORead and/or MOInp are present
    try:
        moread = oe.MOReadExtractor.extract(input_file)
    except oe.DataNotFoundError:
        moread = []
    try:
        moinp = oe.MOInpExtractor.extract(input_file)
    except oe.DataNotFoundError:
        moinp = []

    # Error if only one word present or if more than one of each word
    if len(moinp) ^ len(moread):
        raise ValueError('Error: Missing one of MOInp or MORead')
    if len(moinp) + len(moread) > 2:
        raise ValueError('Error: Multiple MORead and/or MOInp detected')

    if len(moinp):
        # Error if input orbitals have same stem as input file
        moinp = pathlib.Path(moinp[0])
        if moinp.stem == input_file.stem:
            raise ValueError(
                'Error: Stem of orbital and input files cannot match'
            )

        # Error if cannot find orbital file
        if not moinp.exists():
            raise FileNotFoundError(
                f'Error: Cannot find orbital file - {moinp}'
            )

        dependencies['gbw'] = moinp

    # Check if Hessname is present
    try:
        hess = oe.HessNameInputExtractor.extract(input_file)
    except oe.DataNotFoundError:
        hess = []

    if len(hess):
        hess = pathlib.Path(hess[0])
        if hess.stem == input_file.stem:
            raise ValueError(
                'Error: Stem of hessian and input files cannot match'
            )

        # Error if cannot find orbital file
        if not hess.exists():
            raise FileNotFoundError(
                f'Error: Cannot find Hessian file - {hess}'
            )

        dependencies['hess'] = hess

    return dependencies
