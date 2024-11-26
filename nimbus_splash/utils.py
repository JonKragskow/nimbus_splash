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
