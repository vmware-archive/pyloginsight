#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

"""
vcd-cli extention to create and destroy a Log Insight VM in the cloud for testing against.
"""

from pyvcloud.vcd.vapp import VApp
from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.client import NSMAP
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import vcd, click
from vcd_cli.vm import vm

import logging
import time

from requests.adapters import HTTPAdapter


def first_vm_in_vapp(vapp):
    """
    :param vapp: pyvcloud.vcd.vapp.VApp
    :return: pyvcloud.vcd.vm.Vm:
    """
    if vapp.vapp_resource is None:
        vapp.vapp_resource = vapp.client.get_resource(vapp.href)

    if hasattr(vapp.vapp_resource, 'Children') and \
            hasattr(vapp.vapp_resource.Children, 'Vm'):
        for vm in vapp.vapp_resource.Children.Vm:
            return vm
    raise Exception('can\'t find VM')


def get_ip(vdc, client, vapp_name):
    """
    :param vdc: client
    :param client: connection to a vCloud Director service
    :param vapp_name: string
    :return: str, IP address
    """
    vapp_resource = vdc.get_vapp(vapp_name)
    vapp = VApp(client, vapp_resource=vapp_resource)

    vm = first_vm_in_vapp(vapp)
    items = vm.xpath(
        '//ovf:VirtualHardwareSection/ovf:Item',
        namespaces=NSMAP)
    for item in items:
        connection = item.find('rasd:Connection', NSMAP)
        if connection is not None:
            return connection.get('{http://www.vmware.com/vcloud/v1.5}ipAddress')  # NOQA
    raise Exception('can\'t find IP')


@vm.command(short_help='IP of first VM in VAPP')
@click.pass_context
@click.argument('vapp-name',
                metavar='<vapp-name>',
                required=True)
def ip(ctx, vapp_name):
    """Retrive the IP address of the first VM within a VApp"""
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, vdc_href=vdc_href)

        internal_ip = get_ip(vdc, client, vapp_name)

        result = {
            'internal': internal_ip,
        }
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)

@vm.command(short_help='External IP of first VM in VAPP')
@click.pass_context
@click.argument('vapp-name',
                metavar='<vapp-name>',
                required=True)
@click.option('--env/--no-env', default=False)
def externalip(ctx, vapp_name, env):
    """External IP of first VM in VAPP"""
    client = ctx.obj['client']
    vdc_href = ctx.obj['profiles'].get('vdc_href')
    vdc = VDC(client, vdc_href=vdc_href)

    internal_ip = get_ip(vdc, client, vapp_name)

    if env:
        print('IP="{}"'.format(mapping(internal_ip)))
        return

    result = {
        'external': mapping(internal_ip),
        'internal': internal_ip,
    }
    stdout(result, ctx)

def mapping(private_address):
    """Given a private IP address, map to the public IP:Port -- inverse of the NAT rule."""
    last_octet = int(private_address.split('.')[-1])
    external = "207.189.188.118"
    port = 2000 + last_octet
    return "%s:%s" % (external, port)


@vm.command(short_help='Bootstrap LI')
@click.pass_context
@click.argument('vapp-name',
                metavar='<vapp-name>',
                required=True)
def bootstrap_li(ctx, vapp_name):
    """Given a VAPP containing a LI VM, identify the public IP and boostrap a standalone (1-node) cluster."""
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, vdc_href=vdc_href)

        internal_ip = get_ip(vdc, client, vapp_name)

        external_ip = mapping(internal_ip)

        import requests

        logging.info("Boostrapping")
        response = requests.post('https://%s/api/v1/deployment/new' % external_ip, verify=False, json={
            "user": {
                "userName": "admin",
                "password": "VMware123!",
                "email": "admin-integration-test@localhost"
            }
        })

        logging.info("Waiting for bootstrap to finish and service to start")
        requests.post('https://%s/api/v1/deployment/waitUntilStarted' % external_ip, verify=False, json={})

        result = {
            'status': response.status_code,
            'text': response.text
        }

        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)


@vm.command(short_help='Wait until external port is accessible')
@click.pass_context
@click.argument('vapp-name',
                metavar='<vapp-name>',
                required=True)
def publiclyaccessible(ctx, vapp_name):
    """Given a VAPP, poll the first VM's public interface until it responds to LI API requests"""
    import socket
    socket.setdefaulttimeout(1)

    import requests
    s = requests.Session()
    a = HTTPAdapter(max_retries=1)
    s.mount('http://', a)

    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, vdc_href=vdc_href)

        logging.info("Waiting for IP to be assigned")
        while True:

            try:
                internal_ip = get_ip(vdc, client, vapp_name)
                external_ip = mapping(internal_ip)
            except BaseException:
                logging.warning("No IP yet")
                time.sleep(1)
                continue

            url = 'https://%s/api/v1/version' % external_ip
            logging.info("Making connection to {}".format(url))
            try:
                wait = s.get(url, verify=False, timeout=2)
                if wait.status_code in (400, 401, 403):
                    result = {'response': external_ip}
                    stdout(result, ctx)
                    return
            except BaseException as e:
                logging.warning(e)
                time.sleep(1)
                continue

    except Exception as e:
        stderr(e, ctx)

if __name__ == '__main__':
    vcd()
