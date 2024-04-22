import sys
import os


def red_exit(string):
    cprint(string, 'red')
    sys.exit(-1)
    return


def cprint(string: str, color: str):
    '''
    Prints colorised output to screen

    Parameters
    ----------
    string: str
        String to print
    color: str {red, green, yellow, blue, magenta, cyan, white}
        String name of color

    Returns
    -------
    None
    '''

    ccodes = {
        'red': '\u001b[31m',
        'green': '\u001b[32m',
        'yellow': '\u001b[33m',
        'blue': '\u001b[34m',
        'magenta': '\u001b[35m',
        'cyan': '\u001b[36m',
        'white': '\u001b[37m',
        'black_yellowbg': '\u001b[30;43m\u001b[K',
        'white_bluebg': '\u001b[37;44m\u001b[K',
    }
    end = '\033[0m\u001b[K'

    # Count newlines at neither beginning nor end
    num_c_nl = string.rstrip('\n').lstrip('\n').count('\n')

    # Remove right new lines to count left new lines
    num_l_nl = string.rstrip('\n').count('\n') - num_c_nl
    l_nl = ''.join(['\n'] * num_l_nl)

    # Remove left new lines to count right new lines
    num_r_nl = string.lstrip('\n').count('\n') - num_c_nl
    r_nl = ''.join(['\n'] * num_r_nl)

    # Remove left and right newlines, will add in again later
    _string = string.rstrip('\n').lstrip('\n')

    print('{}{}{}{}{}'.format(l_nl, ccodes[color], _string, end, r_nl))

    return


def get_opt_coords(file_name: str) -> tuple[list[str], list[float]]:
    '''
    Extracts coordinates from orca optimisation cycle

    Parameters
    ----------
    file_name: str
        Name of file to check

    Returns
    -------
    list[str]
        Labels
    list[float]
        Coordinates (3,n_atoms)
    bool
        True if stationary point found
    '''

    opt_yn = False

    n_cycles = 0

    with open(file_name, 'r') as f:
        for line in f:
            # Optimisation not finished
            if 'GEOMETRY OPTIMIZATION CYCLE' in line:
                n_cycles += 1
                labels = []
                coords = []
                for _ in range(5):
                    line = next(f)
                while len(line.split()) == 4:
                    labels.append(line.split()[0])
                    coords.append([float(val) for val in line.split()[1:]])
                    line = next(f)
            # Optimisation finished, read again
            if '*** FINAL ENERGY EVALUATION AT THE STATIONARY POINT ***' in line: # noqa
                labels = []
                coords = []
                opt_yn = True
                for _ in range(6):
                    line = next(f)
                while len(line.split()) == 4:
                    labels.append(line.split()[0])
                    coords.append([float(val) for val in line.split()[1:]])
                    line = next(f)

    if n_cycles == 0:
        red_exit(
            'Cannot find optimisation cycle coordinates in {}'.format(
                file_name
            )
        )

    return labels, coords, opt_yn


def get_input_section(file_name: str) -> str:
    '''
    Extracts Input section from orca output file
    '''

    input_str = ''

    with open(file_name, 'r') as f:
        for line in f:
            if 'INPUT FILE' in line:
                for _ in range(3):
                    line = next(f)
                while '****END OF INPUT****' not in line:
                    input_str += '{}'.format(line[line.index('> ') + 2:])
                    line = next(f)

    if not len(input_str):
        red_exit(
            'Cannot find input section in {}'.format(
                file_name
            )
        )

    return input_str


def gen_job_name(input_file: str) -> str:
    return os.path.splitext(os.path.split(input_file)[1])[0]


def gen_results_name(input_file: str) -> str:
    return '{}_results'.format(gen_job_name(input_file))


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
        if var_str == 'SPLASH_RAID':
            try:
                os.environ['CLOUD_ACC']
            except KeyError:
                red_exit(f'Please set ${var_str} environment variable')
            cprint(
                'CLOUD_ACC is deprecated, replace with SPLASH_RAID in .bashrc',
                'black_yellowbg'
            )
        red_exit(f'Please set ${var_str} environment variable')

    return


def get_envvar(var_str: str) -> str:
    '''
    Gets specified environment variable
    If undefined then returns empty string

    Parameters
    ----------
    var_str : str
        String name of environment variable

    Returns
    -------
    str
        Value of environment variable, or empty is not defined
    '''

    try:
        val = os.environ[var_str]
    except KeyError:
        val = ''

    return val


def flatten_recursive(to_flat: list[list]) -> list:
    '''
    Flatten a list of lists recursively.

    Parameters
    ----------
    to_flat: list

    Returns
    -------
    list
        Input list flattened to a single list
    '''

    if to_flat == []:
        return to_flat
    if isinstance(to_flat[0], list):
        return flatten_recursive(to_flat[0]) + flatten_recursive(to_flat[1:])
    return to_flat[:1] + flatten_recursive(to_flat[1:])
