import os
import errno
import configparser
from meican import error


class Config():

    def __init__(self):
        self.__config_filename = os.path.expanduser('~/.config/meican/meican.ini')
        self.__config = configparser.ConfigParser()
        self.__config.read(self.__config_filename)

    def get(self, section, option, default=None):
        return self.__config.get(section, option, fallback=default)

    def set(self, section, option, value):
        if section not in self.__config:
            self.__config[section] = {}
        self.__config.set(section, option, value)
        return self

    def write(self):
        if not os.path.exists(os.path.dirname(self.__config_filename)):
            try:
                os.makedirs(os.path.dirname(self.__config_filename))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        with open(self.__config_filename, mode='w') as fp:
            self.__config.write(fp)


def add_config_command(commands):
    config_parser = commands.add_parser('config', help='get or set options')
    config_parser.add_argument('option')
    config_parser.add_argument('value', nargs='?')
    config_parser.set_defaults(__command_handler=__command_config)


def __command_config(option, value):
    parts = option.split('.')
    if len(parts) != 2:
        error.fatal(error.ERROR_CONFIG_OPTION_INVALID, 'option must have two parts seperated by `.`')

    if value is None:
        value = Config().get(parts[0], parts[1])
        if value is not None:
            print(value)
    else:
        Config().set(parts[0], parts[1], value).write()

if __name__ == "__main__":
    print(Config().get('a', 'b', 'ssss'))
