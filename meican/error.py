import sys

ERROR_INVALID_PASSWORD = 1
ERROR_INVALID_RESTAURANT = 2
ERROR_INVALID_TIME = 3
ERROR_CONFIG_NOT_FOUND = 20
ERROR_CONFIG_OPTION_INVALID = 21

def fatal(code, msg, *args):
    print(msg % args)
    sys.exit(code)
