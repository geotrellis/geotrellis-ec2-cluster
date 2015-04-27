"""Helper functions to handle AMI creation with packer"""

import boto
import os
import subprocess

import logging
import urllib2
import csv

LOGGER = logging.getLogger('geotrellis_spark')


class GTAMIException(Exception):
    pass


def get_ubuntu_ami(region):
    """Gets AMI ID for current release in region"""
    response = urllib2.urlopen('http://cloud-images.ubuntu.com/query/trusty/server/released.current.txt').readlines()
    fieldnames = ['version', 'version_type', 'release_status', 'date',
                  'storage', 'arch', 'region', 'id', 'kernel',
                  'unknown_col', 'virtualization_type']
    reader = csv.DictReader(response, fieldnames=fieldnames, delimiter='\t')

    def ami_filter(ami):
        """Helper function to filter AMIs"""
        return (ami['region'] == region and
                ami['arch'] == 'amd64' and
                ami['storage'] == 'ebs-ssd' and
                ami['virtualization_type'] == 'hvm')

    amis = [row for row in reader if ami_filter(row)]
    if len(amis) == 0:
        raise GTAMIException('Did not find any ubuntu AMIs to use')
    elif len(amis) > 1:
        raise GTAMIException('Found multiple ubuntu AMIs to use, should only be one')
    return amis[0]['id']


def update_ansible_roles():
    """Function that runs command to update ansible roles to verify they are up-to-date before running packer"""
    ansible_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'ansible')
    ansible_roles_path = os.path.join(ansible_dir, 'roles')
    ansible_command = ['ansible-galaxy', 'install', '-f', '-r', 'roles.txt', '-p', ansible_roles_path]
    subprocess.check_call(ansible_command, cwd=ansible_dir)


def run_packer(machine_type, aws_profile, region, stack_type):
    """Function to run packer

    Args:
      machine_type (str): type of machine to build (e.g. mesos-leader, mesos-follower)
      aws_profile (str): aws profile name to use for authentication
      stack_type (str): type of stack this machine is for (e.g. accumulo geotrellis cluster)
    """

    # credentials
    aws_dir = os.path.expanduser('~/.aws')
    boto_config_path = os.path.join(aws_dir, 'config')
    aws_creds_path = os.path.join(aws_dir, 'credentials')
    boto.config.read([boto_config_path, aws_creds_path])
    aws_access_key_id = boto.config.get(aws_profile, 'aws_access_key_id')
    aws_secret_access_key = boto.config.get(aws_profile, 'aws_secret_access_key')

    aws_ubuntu_ami = get_ubuntu_ami(region)

    update_ansible_roles()

    # use environment variables when running packer because you cannot specify an
    # AWS profile in ~/.aws/credentials to use with packer
    env = os.environ.copy()
    env['AWS_ACCESS_KEY'] = aws_access_key_id
    env['AWS_SECRET_ACCESS_KEY'] = aws_secret_access_key
    packer_template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'template.js')
    LOGGER.info('Creating %s AMI in %s region', machine_type, region)
    packer_command = ['packer', 'build',
                      '-var', 'aws_region={}'.format(region),
                      '-var', 'aws_ubuntu_ami={}'.format(aws_ubuntu_ami),
                      '-var', 'stack_type={}'.format(stack_type),
                      '-only', machine_type,
                      packer_template_path]
    LOGGER.debug('Running Packer Command: %s', ' '.join(packer_command))
    subprocess.check_call(packer_command, env=env)
