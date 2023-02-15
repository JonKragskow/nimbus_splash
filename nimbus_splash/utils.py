import sys


def red_exit(string):
    return sys.exit("\u001b[31m Error: {} \033[0m".format(string))
