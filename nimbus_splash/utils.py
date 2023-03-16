import sys


def red_exit(string):
    return sys.exit('\u001b[31m Error: {} \033[0m'.format(string))


def get_opt_coords(file_name: str) -> tuple[list[str], list[float]]:
    '''
    Extracts coordinates from orca optimisation cycle
    '''

    n_cycles = 0

    with open(file_name, 'r') as f:
        for line in f:
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

    if n_cycles == 0:
        red_exit(
            'Cannot find optimisation cycle coordinates in {}'.format(
                file_name
            )
        )

    return labels, coords


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
