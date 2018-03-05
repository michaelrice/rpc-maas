#!/usr/bin/env python

# Copyright 2017, Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import time

import ipaddr
from maas_common import get_auth_ref
from maas_common import get_magnum_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
from magnumclient.common.apiclient import exceptions as exc


def check(auth_ref, args):
    magnum_endpoint = '{protocol}://{ip}:{port}9511/v1'.format(
        ip=args.ip,
        protocol=args.protocol,
        port=args.port
    )

    try:
        if args.ip:
            magnum = get_magnum_client(endpoint=magnum_endpoint)
        else:
            magnum = get_magnum_client()

        api_is_up = True
    except exc.HttpError as e:
        api_is_up = False
        metric_bool('client_success', False, m_name='maas_magnum')
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_magnum')
        status_err(str(e), m_name='maas_magnum')
    else:
        metric_bool('client_success', True, m_name='maas_magnum')
        # time something arbitrary
        start = time.time()
        magnum.cluster_templates.list()
        end = time.time()
        milliseconds = (end - start) * 1000

    status_ok(m_name='maas_magnum')
    metric_bool('magnum_api_local_status', api_is_up, m_name='maas_magnum')
    if api_is_up:
        # only want to send other metrics if api is up
        metric('magnum_api_local_response_time',
               'double',
               '%.3f' % milliseconds,
               'ms')


def main(args):
    auth_ref = get_auth_ref()
    check(auth_ref, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Magnum API against local or remote address')
    parser.add_argument('ip', nargs='?', type=ipaddr.IPv4Address,
                        help="Check Magnum API against "
                        " local or remote address")
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--port',
                        action='store',
                        default='9511',
                        help='Port that the magnum API service is running on')
    parser.add_argument('--protocol',
                        action='store',
                        default='http',
                        help='Protocol for magnum API service')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)
