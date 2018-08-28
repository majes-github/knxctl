#!/usr/bin/env python

import argparse
import xmlrpclib


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--hostname', help='knxctl hostname', type=str,
                        default='localhost')
    parser.add_argument('--port', type=int, default=8000,
                        help='port of knxctl service')
    parser.add_argument('--action', type=str, help='knx device action')
    parser.add_argument('--address', type=str, help='knx bus address')

    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()
    url = 'http://{hostname}:{port}/'
    proxy = xmlrpclib.ServerProxy(url.format(**args.__dict__))

    if args.action:
        if not args.address:
            raise Exception('No knx bus address specified!')
        if args.action not in proxy.system.listMethods():
            raise Exception('No valid action!')
        # Call the remote procedure
        getattr(proxy, args.action)(args.address)
    else:
        print proxy.get_device_states()


if __name__ == '__main__':
    main()
