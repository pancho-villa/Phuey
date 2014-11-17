from sys import stdout
import argparse
import json
import logging

from phuey import Bridge, Light


logger = logging.getLogger()


def command_interpreter(command):
    python_dict = {}
    commands = command.split(',')
    for c in commands
        k, v = c.split('=')
        if v.lower() == "true":
            v = True
        elif v.lower() == "false":
            v = False
        elif v.isdigit() is True:
            v = int(v)
        python_dict[k] = v 
    return json.dumps(python_dict)

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--bridge', '-b', metavar="BRIDGEIPADDRESS")
    arg_parser.add_argument('--user', '-u', metavar="USERNAME")
    arg_parser.add_argument('--light', '-l', metavar="LIGHTID")
    arg_parser.add_argument('--command', '-c', metavar="COMMAND")
    args = arg_parser.parse_args()
    bridge_ip = args.bridge
    user = args.user
    lid = args.light
    command = command_interpreter(args.command)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(stdout)
    ch.setLevel(logging.DEBUG)
    fmt = '%(name)s - %(asctime)s - %(module)s-%(funcName)s/%(lineno)d - %(message)s'
    formatter = logging.Formatter(fmt)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


    light = Light(bridge_ip, user, lid, 'my light')
    logger.debug(command)
    light.state = json.loads(command)