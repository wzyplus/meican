import argparse
from meican.config import add_config_command
from meican.meican import add_meican_command

def main():
    parser = argparse.ArgumentParser(prog='meican', description='')
    commands = parser.add_subparsers(title='commands')

    add_config_command(commands)
    add_meican_command(commands)

    kwargs = vars(parser.parse_args())
    if not kwargs:
        parser.print_help()
        return

    handler = kwargs.pop('__command_handler')
    handler(**kwargs)


if __name__ == "__main__":
    main()
