#!/usr/bin/env python3

import argparse
from datetime import datetime
import json
import signal
from subprocess import run
import sys
from xmlrpc.server import SimpleXMLRPCServer


knx_address = None
log_fd = None
state_file = None
device_states = {}
registered_functions = []


def register_function(func):
    registered_functions.append(func)


def parse_arguments():
    global knx_address
    global state_file

    parser = argparse.ArgumentParser()
    parser.add_argument('--bind-address', type=str, default='0.0.0.0',
                        help='bind address of xmlrpc service')
    parser.add_argument('--bind-port', type=int, default=8000,
                        help='bind port of xmlrpc service')
    parser.add_argument('--hostname', help='knxd hostname', type=str,
                        default='knxpi')
    parser.add_argument('--log-file', help='logfile name', type=str,
                        default='knxctl.log')
    parser.add_argument('--state-file', help='statefile name', type=str,
                        default='knxctl.state')
    args = parser.parse_args()
    state_file = args.state_file
    knx_address = args.hostname
    return args


def handler(signum, frame):
    save_device_states(state_file)
    sys.exit()


def log_action(message):
    log_fd.write('{:%Y-%m-%d %H:%M:%S} {}\n'.format(datetime.now(), message))


def run_knxtool(address):
    cmd = [
        'knxtool',
        'groupswrite',
        'ip:{}'.format(knx_address),
        '{}'.format(address),
        '{:d}'.format(device_states[address]),
    ]
    log_action(' '.join(cmd))
    run(cmd)


@register_function
def get_device_states():
    return device_states


def load_device_states(file_name):
    global device_states
    with open(file_name) as fd:
        device_states = json.load(fd)


def save_device_states(file_name):
    with open(file_name, 'w') as fd:
        json.dump(device_states, fd)


def toggle_device(address):
    global device_states
    if address not in device_states:
        device_states[address] = False
    device_states[address] ^= True
    run_knxtool(address)


def enable_device(address):
    global device_states
    device_states[address] = True
    run_knxtool(address)


def disable_device(address):
    global device_states
    device_states[address] = False
    run_knxtool(address)


@register_function
def toggle_blinds(address):
    toggle_device(address)


@register_function
def close_blinds(address):
    enable_device(address)


@register_function
def stop_blinds(address):
    _address = address.split('/')
    _address[2] = str(int(_address[2]) + 1)
    address = '/'.join(_address)
    enable_device(address)


@register_function
def open_blinds(address):
    disable_device(address)


@register_function
def toggle_lights(address):
    toggle_device(address)


@register_function
def turn_on_lights(address):
    enable_device(address)


@register_function
def turn_off_lights(address):
    disable_device(address)


def main():
    ''' The main procedure '''
    global log_fd

    args = parse_arguments()
    try:
        load_device_states(state_file)
    except IOError:
        pass
    log_fd = open(args.log_file, 'a')
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    # ininiate xmlrpc service
    server = SimpleXMLRPCServer(
        (args.bind_address, args.bind_port), allow_none=True)
    for func in registered_functions:
        server.register_function(func)
    server.register_introspection_functions()
    server.serve_forever()


if __name__ == '__main__':
    main()
