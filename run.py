# -*- coding: utf-8 -*-
import sys
import json
from argparse import ArgumentParser
from contextlib import contextmanager

import napalm
from brewtils.decorators import system, command, parameter
from brewtils.plugin import RemotePlugin
from napalm.base import constants as c

PARAMETERS = {
    'template_name': {
        'key': 'template_name',
        'type': 'String',
        'description': 'Identifies the template name.',
        'display_name': 'Template Name',
        'optional': False,
    },
    'template_source': {
        'key': 'template_source',
        'type': 'String',
        'description': 'Custom config template rendered and loaded on device.',
        'display_name': 'Template Source',
        'optional': True,
        'default': None,
        'nullable': True,
    },
    'template_path': {
        'key': 'template_path',
        'type': 'String',
        'description': 'Absolute path to directory for the configuration templates.',
        'display_name': 'Template Path',
        'default': None,
        'nullable': True,
    },
    'template_vars': {
        'key': 'template_vars',
        'type': 'Dictionary',
        'description': 'Dictionary with arguments to be used when the template is rendered.',
        'default': None,
        'nullable': True,
    },
    'filename': {
        'key': 'filename',
        'type': 'String',
        'description': 'Path to the file containing the desired configuration. By default is None.',
        'optional': True,
        'default': None,
        'nullable': True,
    },
    'config': {
        'key': 'config',
        'type': 'String',
        'description': 'String containing the desired configuration',
        'optional': True,
        'default': None,
        'nullable': True,
    },
    'destination': {
        'key': 'destination',
        'type': 'String',
        'description': 'The destination prefix to be used when filtering the routes.',
        'optional': True,
        'default': None,
        'nullable': True,
    },
    'protocol': {
        'key': 'protocol',
        'type': 'String',
        'description': 'Retrieve the routes only for a specific protocol.',
        'optional': True,
        'default': None,
        'nullable': True,
    },
    'interface': {
        'key': 'interface',
        'type': 'String',
        'description': 'Specify an interface',
        'default': '',
        'optional': True,
    },
    'group': {
        'key': 'group',
        'type': 'String',
        'default': '',
        'optional': True,
        'description': 'Returns the configuration of a specific BGP group.',
    },
    'neighbor': {
        'key': 'neighbor',
        'type': 'String',
        'default': '',
        'optional': True,
        'description': 'Returns the configuration of a specific BGP neighbor.',
    },
    'neighbor_address': {
        'key': 'neighbor_address',
        'type': 'String',
        'description': 'Retuns the statistics for a spcific BGP neighbor.',
        'default': '',
        'optional': True,
    },
    'ping_destination': {
        'key': 'destination',
        'type': 'String',
        'description': 'Host or IP Address of the destination.',
        'optional': False,
    },
    'ping_source': {
        'key': 'source',
        'type': 'String',
        'description': 'Source address of echo request',
        'optional': True,
        'default': c.PING_SOURCE,
        'nullable': True,
    },
    'ping_ttl': {
        'key': 'ttl',
        'type': 'Integer',
        'description': 'Maximum number of hops',
        'optional': True,
        'default': c.PING_TTL,
        'nullable': True,
    },
    'ping_timeout': {
        'key': 'timeout',
        'type': 'Integer',
        'description': 'Maximum seconds to wait after sending final packet',
        'optional': True,
        'default': c.PING_TIMEOUT,
        'nullable': True,
    },
    'ping_size': {
        'key': 'size',
        'type': 'Integer',
        'description': 'Size of request (bytes)',
        'optional': True,
        'default': c.PING_SIZE,
        'nullable': True,
    },
    'ping_count': {
        'key': 'count',
        'type': 'Integer',
        'description': 'Number of ping request to send',
        'optional': True,
        'default': c.PING_COUNT,
        'nullable': True,
    },
    'ping_vrf': {
        'key': 'vrf',
        'type': 'String',
        'description': 'Virtual routing and forwarding.',
        'optional': True,
        'default': c.PING_VRF,
        'nullable': True,
    },
    'traceroute_destination': {
        'key': 'destination',
        'type': 'String',
        'description': 'Host or IP Address of the destination.',
        'optional': False,
    },
    'traceroute_source': {
        'key': 'source',
        'type': 'String',
        'description': 'Use a specific IP Address to execute the traceroute',
        'optional': True,
        'default': c.TRACEROUTE_SOURCE,
        'nullable': True,
    },
    'traceroute_ttl': {
        'key': 'ttl',
        'type': 'Integer',
        'description': 'Maximum number of hops',
        'optional': True,
        'default': c.TRACEROUTE_TTL,
        'nullable': True,
    },
    'traceroute_timeout': {
        'key': 'timeout',
        'type': 'Integer',
        'description': 'Number of seconds to wait for response.',
        'optional': True,
        'default': c.TRACEROUTE_TIMEOUT,
        'nullable': True,
    },
    'traceroute_vrf': {
        'key': 'vrf',
        'type': 'String',
        'description': 'Virtual routing and forwarding.',
        'optional': True,
        'default': c.TRACEROUTE_VRF,
        'nullable': True,
    },
    'retrieve': {
        'key': 'retrieve',
        'type': 'String',
        'description': 'Which configuration type you want to '
                       'populate, default is all of them, the rest '
                       'will be set to ""',
        'optional': True,
        'default': 'all',
    },
    'network_instance_name': {
        'key': 'name',
        'type': 'String',
        'description': 'Name of the network instance to return, default '
                       'is all.',
        'optional': True,
        'default': 'all',

    },
    'validation_file': {
        'key': 'validation_file',
        'type': 'String',
        'description': 'Path to the file containing compliance definition. '
                       'Default is None',
        'optional': True,
        'default': None,
        'nullable': True,
    },
    'validation_source': {
        'key': 'validation_source',
        'type': 'Dictionary',
        'description': 'Dictionary containing compliance rules.',
        'optional': True,
        'default': None,
        'nullable': True,
    }
}


@system
class NapalmPlugin(object):
    """Plugin that wraps NAPALM's EOS Driver"""

    def __init__(self,
                 driver,
                 hostname,
                 username,
                 password,
                 timeout=60,
                 optional_args=None):
        self._driver = driver
        self._init_params = {
            'hostname': hostname,
            'username': username,
            'password': password,
            'timeout': timeout,
            'optional_args': optional_args or {}
        }
        self._device = None
        self._externally_managed = False

    @contextmanager
    def _connect(self):
        if self._externally_managed:
            yield self._device
        elif self._device:
            yield self._device
        else:
            self._open(external=False)
            yield self._device
            self._close(external=False)

    def _open(self, external=True):
        self._externally_managed = external
        if self._device is None:
            self._device = self._driver(**self._init_params)
            self._device.open()

    def _close(self, external=True):
        if self._device is None:
            return
        elif self._externally_managed and not external:
            raise ValueError("Cannot close a connection that is being externally managed. "
                             "You shouldn't be seeing this message.")

        self._device.close()
        self._device = None
        self._externally_managed = False

    @command
    def open(self):
        """Opens a connection to the device."""
        return self._open(external=True)

    @command
    def close(self):
        """Closes the connection to the device."""
        self._close(external=True)

    @command
    def is_alive(self):
        """Returns a flag with the connection state."""
        with self._connect() as device:
            return device.is_alive()

    @parameter(**PARAMETERS['template_name'])
    @parameter(**PARAMETERS['template_source'])
    @parameter(**PARAMETERS['template_path'])
    @parameter(**PARAMETERS['template_vars'], is_kwarg=True)
    def load_template(self, template_name, template_source=None,
                      template_path=None, **template_vars):
        """Will load a templated configuration on the device."""
        with self._connect() as device:
            return device.load_template(template_name,
                                        template_source=template_source,
                                        template_path=template_path,
                                        **template_vars)

    @parameter(**PARAMETERS['filename'])
    @parameter(**PARAMETERS['config'])
    def load_replace_candidate(self, filename=None, config=None):
        """Populates the candidate configuration."""
        with self._connect() as device:
            return device.load_replace_candidate(filename=filename,
                                                 config=config)

    @parameter(**PARAMETERS['filename'])
    @parameter(**PARAMETERS['config'])
    def load_merge_candidate(self, filename=None, config=None):
        """Populates the candidate configuration."""
        with self._connect() as device:
            return device.load_merge_candidate(filename=filename,
                                               config=config)

    @command
    def compare_config(self):
        """Compare the loaded configuration."""
        with self._connect() as device:
            return device.compare_config()

    @command
    def commit_config(self):
        """Commits the changes requested by the candidate."""
        with self._connect() as device:
            return device.commit_config()

    @command
    def discard_config(self):
        """Discards the configuration loaded into the candidate."""
        with self._connect() as device:
            return device.discard_config()

    @command
    def rollback(self):
        """If changes were made, revert changes to the original state."""
        with self._connect() as device:
            return device.rollback()

    @command
    def get_facts(self):
        """Returns a dictionary of information."""
        with self._connect() as device:
            return device.get_facts()

    @command
    def get_interfaces(self):
        """Gets interfaces."""
        with self._connect() as device:
            return device.get_interfaces()

    @command
    def get_lldp_neighbors(self):
        """Gets all LLDP neighbors."""
        with self._connect() as device:
            return device.get_lldp_neighbors()

    @command
    def get_bgp_neighbors(self):
        """Gets all BGP neighbors."""
        with self._connect() as device:
            return device.get_bgp_neighbors()

    @command
    def get_environment(self):
        """Gets the environment of the device."""
        with self._connect() as device:
            return device.get_environment()

    @command
    def get_interfaces_counters(self):
        """Gets interface counters of the device."""
        with self._connect() as device:
            return device.get_interfaces_counters()

    @parameter(**PARAMETERS['interface'])
    def get_lldp_neighbors_detail(self, interface=''):
        """Gets LLDP Neighbors of the device with more detail."""
        with self._connect() as device:
            return device.get_lldp_neighbors_detail(interface=interface)

    @parameter(**PARAMETERS['group'])
    @parameter(**PARAMETERS['neighbor'])
    def get_bgp_config(self, group='', neighbor=''):
        """Gets BGP config for the device."""
        with self._connect() as device:
            return device.get_bgp_config(group=group,
                                         neighbor=neighbor)

    @parameter(**PARAMETERS['neighbor_address'])
    def get_bgp_neighbors_detail(self, neighbor_address=''):
        """Gets BGP neighbors in detail."""
        with self._connect() as device:
            return device.get_bgp_neighbors_detail(
                neighbor_address=neighbor_address
            )

    @command
    def get_arp_table(self):
        """Get the ARP table of the device."""
        with self._connect() as device:
            return device.get_arp_table()

    @command
    def get_ntp_peers(self):
        """Returns the NTP peers configuration as dictionary."""
        with self._connect() as device:
            return device.get_ntp_peers()

    @command
    def get_ntp_servers(self):
        """Returns the NTP servers configuration as dictionary."""
        with self._connect() as device:
            return device.get_ntp_servers()

    @command
    def get_ntp_stats(self):
        """Returns a list of NTP synchronization statistics."""
        with self._connect() as device:
            return device.get_ntp_stats()

    @command
    def get_interfaces_ip(self):
        """Returns all configured IP addresses on all interfaces as a dictionary of dictionaries."""
        with self._connect() as device:
            return device.get_interfaces_ip()

    @command
    def get_mac_address_table(self):
        """Get MAC Addresses Table of the device."""
        with self._connect() as device:
            return device.get_mac_address_table()

    @parameter(**PARAMETERS['destination'])
    @parameter(**PARAMETERS['protocol'])
    def get_route_to(self, destination='', protocol=''):
        """Get available routes to the destination."""
        with self._connect() as device:
            return device.get_route_to(
                destination=destination,
                protocol=protocol
            )

    @command
    def get_snmp_information(self):
        """Returns a dict of dicts containing SNMP configuration."""
        with self._connect() as device:
            return device.get_snmp_information()

    @command
    def get_probes_config(self):
        """Returns a dictionary with the probes configured on the device."""
        with self._connect() as device:
            return device.get_probes_config()

    @command
    def get_probes_results(self):
        """Returns a dictionary with the results of the probes."""
        with self._connect() as device:
            return device.get_probes_results()

    @parameter(**PARAMETERS['ping_destination'])
    @parameter(**PARAMETERS['ping_destination'])
    @parameter(**PARAMETERS['ping_destination'])
    @parameter(**PARAMETERS['ping_destination'])
    @parameter(**PARAMETERS['ping_destination'])
    @parameter(**PARAMETERS['ping_destination'])
    @parameter(**PARAMETERS['ping_destination'])
    def ping(self, destination, source=c.PING_SOURCE, ttl=c.PING_TTL,
             timeout=c.PING_TIMEOUT, size=c.PING_SIZE,
             count=c.PING_COUNT, vrf=c.PING_VRF):
        """Executes ping on the device and returns a dictionary with the result."""
        with self._connect() as device:
            device.ping(destination=destination,
                        source=source,
                        ttl=ttl,
                        timeout=timeout,
                        size=size,
                        count=count,
                        vrf=vrf)

    @parameter(**PARAMETERS['traceroute_destination'])
    @parameter(**PARAMETERS['traceroute_source'])
    @parameter(**PARAMETERS['traceroute_ttl'])
    @parameter(**PARAMETERS['traceroute_timeout'])
    @parameter(**PARAMETERS['traceroute_vrf'])
    def traceroute(self,
                   destination,
                   source=c.TRACEROUTE_SOURCE,
                   ttl=c.TRACEROUTE_TTL,
                   timeout=c.TRACEROUTE_TIMEOUT,
                   vrf=c.TRACEROUTE_VRF):
        """Executes traceroute on the device and returns a dictionary with the result."""
        with self._connect() as device:
            return device.traceroute(
                destination,
                source=source,
                ttl=ttl,
                timeout=timeout,
                vrf=vrf)

    @command
    def get_users(self):
        """Returns a dictionary with the configured users."""
        with self._connect() as device:
            return device.get_users()

    @command
    def get_optics(self):
        """Fetches the power usage on the various transceivers"""
        with self._connect() as device:
            return device.get_optics()

    @parameter(**PARAMETERS['retrieve'])
    def get_config(self, retrieve='all'):
        """Return the configuration of a device."""
        with self._connect() as device:
            return device.get_config(retrieve=retrieve)

    @parameter(**PARAMETERS['network_instance_name'])
    def get_network_instances(self, name=''):
        """Return a dictionary of network instances (VRFs) configured, including default/global"""
        with self._connect() as device:
            return device.get_network_instances(name=name)

    @command
    def get_firewall_policies(self):
        """Gets firewall policy for the device."""
        with self._connect() as device:
            return device.get_firewall_policies()

    @command
    def get_ipv6_neighbors_table(self):
        """Get IPv6 neighbors table information."""
        with self._connect() as device:
            return device.get_ipv6_neighbors_table()

    @command
    def compliance_report(self, validation_file=None, validation_source=None):
        """Return a compliance report."""
        with self._connect() as device:
            return device.compliance_report(
                validation_file=validation_file,
                validation_source=validation_source
            )


def parse_args(cli_args):
    parser = ArgumentParser(description='Starts a plugin using NAPALM '
                                        'for the specified device')
    parser.add_argument('driver',
                        help='The driver to run',
                        choices=napalm.SUPPORTED_DRIVERS,
                        type=str)
    parser.add_argument('--hostname',
                        help='The hostname of the device',
                        type=str)
    parser.add_argument('-u', '--username',
                        help='The username of the device',
                        type=str)
    parser.add_argument('-p', '--password',
                        dest='password',
                        type=str,
                        help='The password of the device')
    parser.add_argument('-t', '--timeout',
                        type=int,
                        help='Timeout for the device',
                        default=60)
    parser.add_argument('-d', '--device-config',
                        dest='device_config',
                        type=str,
                        help='The configuration to use for the device (overrides CLI)')
    parser.add_argument('--bg-host',
                        dest='bg_host',
                        type=str,
                        help='The hostname for Beer Garden',
                        default='localhost')
    parser.add_argument('--bg-port',
                        dest='bg_port',
                        type=int,
                        help='The port for Beer Garden',
                        default=2337)
    parser.add_argument('--ssl',
                        help='Beer Garden SSL Enabled flag',
                        action='store_true',
                        default=False)
    parser.add_argument('--ca-cert',
                        help='Certificate Authority to use',
                        dest='ca_cert',
                        type=str,
                        default=None)
    parser.add_argument('--client-cert',
                        help='Client certificate to use for '
                             'beer-garden connection',
                        dest='client_cert',
                        type=str,
                        default=None)
    parser.add_argument('--plugin-name',
                        help='Plugin Name to use defaults to '
                             '(${driver}-plugin)',
                        type=str,
                        dest='plugin_name')
    parser.add_argument('--ca-verify',
                        help='Verify the beer-garden certificate',
                        dest='ca_verify',
                        action='store_true',
                        default=False)
    parser.add_argument('-b', '--bg-config',
                        help='Path to beer-garden config '
                             '(overrides CLI options)',
                        dest='bg_config',
                        type=str)

    args_to_return = vars(parser.parse_args(cli_args))
    if args_to_return['device_config']:
        with open(args_to_return['device_config']) as device_config:
            args_to_return.update(json.load(device_config))

    if args_to_return['bg_config']:
        with open(args_to_return['bg_config']) as bg_config:
            args_to_return.update(json.load(bg_config))

    if not args_to_return['plugin_name']:
        args_to_return['plugin_name'] = args_to_return['driver'] + '-plugin'

    required_items = ['hostname', 'username', 'password',
                      'timeout', 'bg_host', 'bg_port', 'ssl',
                      'ca_cert', 'client_cert', 'plugin_name',
                      'ca_verify']

    for item in required_items:
        if item not in args_to_return:
            print("No %s provided." % item)
            sys.exit(1)

    return {
        'driver': napalm.get_network_driver(args_to_return['driver']),
        'hostname': args_to_return['hostname'],
        'username': args_to_return['username'],
        'password': args_to_return['password'],
        'timeout': args_to_return['timeout'],
        'optional_args': args_to_return.get('optional_args', {}),
    }, {
        'bg_host': args_to_return['bg_host'],
        'bg_port': args_to_return['bg_port'],
        'ssl_enabled': args_to_return['ssl'],
        'ca_cert': args_to_return['ca_cert'],
        'client_cert': args_to_return['client_cert'],
        'name': args_to_return['plugin_name'],
        'description': 'Command and control for %s '
                       'device' % args_to_return['driver'],
        'ca_verify': args_to_return['ca_verify'],
        'version': napalm.__version__,
    }


if __name__ == '__main__':
    napalm_args, bg_args = parse_args(sys.argv[1:])
    client = NapalmPlugin(**napalm_args)
    plugin = RemotePlugin(client, **bg_args)
    plugin.run()
