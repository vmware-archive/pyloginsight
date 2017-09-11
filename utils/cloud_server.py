#!/usr/bin/env python

from __future__ import print_function
"""
Create and destroy a Log Insight VM in the cloud for testing against.
"""

# vCloud CLI 0.1
#
# Copyright (c) 2014 VMware, Inc. All Rights Reserved.
#
# This product is licensed to you under the
# Apache License, Version 2.0 (the "License").
# You may not use this product except in compliance with the License.
#
# This product may include a number of subcomponents with
# separate copyright notices and license terms. Your use of the source
# code for the these subcomponents is subject to the terms and
# conditions of the subcomponent's license, as noted in the LICENSE file.
#

import click
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.utils import to_dict
from pyvcloud.vcd.utils import vapp_to_dict
from pyvcloud.vcd.vapp import VApp
from pyvcloud.vcd.vdc import VDC
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import abort_if_false
from vcd_cli.vcd import vcd

from lxml import objectify
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import find_link
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.vdc import Maker
from pyvcloud.vcd.vdc import OvfMaker

import logging
import uuid
import time

from lxml import etree

#logging.basicConfig(level=logging.DEBUG)


@vcd.group(short_help='manage vApps')
@click.pass_context
def vapp_custom(ctx):
    """Deploy VAPP from catalog with "Identical copy" (CustomizeOnInstantiate=false) selected
\b
    Examples
        vcd vapp list
            Get list of vApps in current virtual datacente3r.
\b
        vcd vapp info my-vapp
            Get details of the vApp 'my-vapp'.
\b
        vcd vapp create my-catalog my-template my-vapp
            Create a new vApp.
\b
        vcd vapp delete my-vapp --yes --force
            Delete a vApp.
\b
        vcd --no-wait vapp delete my-vapp --yes --force
            Delete a vApp without waiting for completion.
\b
        vcd vapp update-lease my-vapp 7776000
            Set vApp lease to 90 days.
\b
        vcd vapp update-lease my-vapp 0
            Set vApp lease to no expiration.
    """  # NOQA
    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
            if not ctx.obj['profiles'].get('vdc_in_use') or \
               not ctx.obj['profiles'].get('vdc_href'):
                raise Exception('select a virtual datacenter')
        except Exception as e:
            stderr(e, ctx)


@vapp_custom.command(short_help='show vApp details')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
def info(ctx, name):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, vdc_href=vdc_href)
        vapp = vdc.get_vapp(name)
        print(vapp)
        #stdout(vapp_to_dict(vapp), ctx)
        print("Starting connection:")
        print(etree.tostring(vapp, pretty_print=True))

    except Exception as e:
        stderr(e, ctx)


@vapp_custom.command('list', short_help='list vApps')
@click.pass_context
def list_vapps(ctx):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, vdc_href=vdc_href)
        # TODO(consider using search api/RECORDS)
        result = vdc.list_resources(EntityType.VAPP)
        stdout(result, ctx, show_id=True)
    except Exception as e:
        stderr(e, ctx)



@vapp_custom.command(short_help='create a vApp')
@click.pass_context
@click.argument('catalog',
                metavar='<catalog>',
                required=True)
@click.argument('template',
                metavar='<template>',
                required=True)
@click.argument('name',
                metavar='<name>',
                default=str(uuid.uuid4()))
@click.option('-n',
              '--network',
              'network',
              required=False,
              metavar='[network]',
              help='Network')
def create(ctx, catalog, template, name, network):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, vdc_href=vdc_href)
        vapp = instantiate_fenced_vapp(vdc, name, catalog, template, network=network, deploy=False, power_on=False)
        stdout(vapp.Tasks.Task[0], ctx)
    except Exception as e:
        stderr(e, ctx)


@vapp_custom.command(short_help='delete a vApp')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.option('-y',
              '--yes',
              is_flag=True,
              callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to delete the vApp?')
@click.option('-f',
              '--force',
              is_flag=True,
              help='Force delete running vApps')
def delete(ctx, name, force):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, vdc_href=vdc_href)
        task = vdc.delete_vapp(name, force)
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)


@vapp_custom.command('update-lease', short_help='update vApp lease')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.argument('runtime-seconds',
                metavar='<runtime-seconds>',
                required=True)
@click.argument('storage-seconds',
                metavar='[storage-seconds]',
                required=False)
def update_lease(ctx, name, runtime_seconds, storage_seconds):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, vdc_href=vdc_href)
        vapp_resource = vdc.get_vapp(name)
        vapp = VApp(client, vapp_resource=vapp_resource)
        if storage_seconds is None:
            storage_seconds = runtime_seconds
        task = vapp.set_lease(runtime_seconds, storage_seconds)
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)


def instantiate_fenced_vapp(
                     self,
                     name,
                     catalog,
                     template,
                     network=None,
                     deploy=True,
                     power_on=True):
    if self.vdc_resource is None:
        self.vdc_resource = self.client.get_resource(self.href)

    network_href = None
    if hasattr(self.vdc_resource, 'AvailableNetworks') and \
       hasattr(self.vdc_resource.AvailableNetworks, 'Network'):
        for n in self.vdc_resource.AvailableNetworks.Network:
            if network is None or n.get('name') == network:
                network_href = n.get('href')
    if network_href is None:
        raise Exception('Network not found in the Virtual Datacenter.')

    # TODO(cache some of these objects here and in Org object)
    org_href = find_link(self.vdc_resource,
                         RelationType.UP,
                         EntityType.ORG.value).href
    org = Org(self.client, org_href)
    template_resource = org.get_catalog_item(catalog, template)
    v = self.client.get_resource(template_resource.Entity.get('href'))
    n = v.xpath(
        '//ovf:NetworkSection/ovf:Network',
        namespaces={'ovf': 'http://schemas.dmtf.org/ovf/envelope/1'})
    network_name = n[0].get('{http://schemas.dmtf.org/ovf/envelope/1}name')
    deploy_param = 'true' if deploy else 'false'
    power_on_param = 'true' if power_on else 'false'
    vapp_template_params = Maker.InstantiateVAppTemplateParams(
        name=name,
        deploy=deploy_param,
        powerOn=power_on_param)
    vapp_template_params.append(
        Maker.InstantiationParams(
            Maker.NetworkConfigSection(
                OvfMaker.Info('Configuration for logical networks'),
                Maker.NetworkConfig(
                    Maker.Configuration(
                        Maker.ParentNetwork(href=network_href),
                        Maker.FenceMode('natRouted'),

                    ),
                    # Maker.IsDeployed('true'),
                    networkName=network_name
                )
            )
        )
    )
    vapp_template_params.append(
        Maker.Source(href=template_resource.Entity.get('href'))
    )
    vm = v.xpath(
        '//vcloud:VAppTemplate/vcloud:Children/vcloud:Vm',
        namespaces=NSMAP)
    for c in vm[0].NetworkConnectionSection.NetworkConnection:
        from lxml import etree
        print("Starting connection:")
        print(etree.tostring(c, pretty_print=True))

        #c.remove(c.MACAddress)
        #c.remove(c.IpAddressAllocationMode)
        tmp = c.NetworkAdapterType
        c.remove(c.NetworkAdapterType)
        c.remove(c.IpAddressAllocationMode)
        c.append(Maker.IpAddressAllocationMode('STATIC'))
        c.append(tmp)

        from lxml import etree
        print("Ending connection:")
        print(etree.tostring(c, pretty_print=True))
    ip = Maker.InstantiationParams()
    ip.append(vm[0].NetworkConnectionSection)
    gc = Maker.GuestCustomizationSection(
        OvfMaker.Info('Specifies Guest OS Customization Settings'),
        Maker.Enabled('false'),
        # Maker.AdminPasswordEnabled('false'),
        Maker.ComputerName(name)
    )
    ip.append(gc)
    vapp_template_params.append(
        Maker.SourcedItem(
            Maker.Source(href=vm[0].get('href'),
                         id=vm[0].get('id'),
                         name=vm[0].get('name'),
                         type=vm[0].get('type')),
            Maker.VmGeneralParams(
                Maker.Name(name),
                Maker.NeedsCustomization('false')
            ),
            ip
        )
    )
    from lxml import etree
    print(etree.tostring(vapp_template_params, pretty_print=True))
    # return None
    return self.client.post_resource(
        self.href+'/action/instantiateVAppTemplate',
        vapp_template_params,
        EntityType.INSTANTIATE_VAPP_TEMPLATE_PARAMS.value)


def first_vm_in_vapp(vapp):
    if vapp.vapp_resource is None:
        vapp.vapp_resource = vapp.client.get_resource(vapp.href)

    if hasattr(vapp.vapp_resource, 'Children') and \
            hasattr(vapp.vapp_resource.Children, 'Vm'):
        for vm in vapp.vapp_resource.Children.Vm:
            return vm
    raise Exception('can\'t find VM')


def get_ip(vdc, client, vapp_name):
    vapp_resource = vdc.get_vapp(vapp_name)
    vapp = VApp(client, vapp_resource=vapp_resource)
    result = {}

    vm = first_vm_in_vapp(vapp)
    items = vm.xpath(
        '//ovf:VirtualHardwareSection/ovf:Item',
        namespaces=NSMAP)
    for item in items:
        connection = item.find('rasd:Connection', NSMAP)
        if connection is not None:
            return connection.get('{http://www.vmware.com/vcloud/v1.5}ipAddress')  # NOQA
    raise Exception('can\'t find IP')

from vcd_cli.vm import vm

@vm.command(short_help='IP of first VM in VAPP')
@click.pass_context
@click.argument('vapp-name',
                metavar='<vapp-name>',
                required=True)
def ip(ctx, vapp_name):
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

@vm.command(short_help='IP of first VM in VAPP')
@click.pass_context
@click.argument('vapp-name',
                metavar='<vapp-name>',
                required=True)
@click.option('--env/--no-env', default=False)
def externalip(ctx, vapp_name, env):
    try:
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
    except Exception as e:
        raise
        stderr(e, ctx)

def mapping(private_address):
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
        wait = requests.post('https://%s/api/v1/deployment/waitUntilStarted' % external_ip, verify=False, json={})

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
    import socket
    socket.setdefaulttimeout(1)

    import requests
    s = requests.Session()
    a = requests.adapters.HTTPAdapter(max_retries=1)
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
            except BaseException as e:
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
