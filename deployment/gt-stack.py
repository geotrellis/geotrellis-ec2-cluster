#!/usr/bin/env python
"""Commands for setting up a GeoTrellis Spark stack on AWS"""

import argparse
import os

from cfn.stacks import build_stacks
from cfn.template_utils import get_config
from packer.gt_packer import run_packer


current_file_dir = os.path.dirname(os.path.realpath(__file__))


def launch_stacks(gt_config, aws_profile, **kwargs):
    build_stacks(aws_profile, gt_config)


def create_ami(machine_type, aws_profile, gt_config, **kwargs):
    run_packer(machine_type,
               aws_profile=aws_profile,
               region=gt_config['Region'],
               stack_type=gt_config['StackType'])


def main():
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument('--aws-profile', default='default',
                               help='AWS profile to use for launching stack and other resources')
    common_parser.add_argument('--gt-config-path', help='Path to GeoTrellis stack config',
                               default=os.path.join(current_file_dir, 'geotrellis-cluster.config'))
    common_parser.add_argument('--gt-profile', default='accumulo',
                               help='GeoTrellis stack profile to use for launching stacks')

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='GeoTrellis Stack Commands')

    # Launch GeoTrellis Stack
    gt_stacks = subparsers.add_parser('launch-stacks', help='Launch GeoTrellis Spark Stack',
                                parents=[common_parser,])
    gt_stacks.set_defaults(func=launch_stacks)

    # AMI Management
    gt_ami = subparsers.add_parser('create-ami', help='Create AMI for GeoTrellis-Spark Stack',
                                   parents=[common_parser,])
    gt_ami.add_argument('machine_type', help='Type of AMI to build for GeoTrellis-Spark')
    gt_ami.set_defaults(func=create_ami)

    # Parse and Run
    args = parser.parse_args()
    gt_config = get_config(args.gt_config_path, args.gt_profile)
    args.func(gt_config=gt_config, **vars(args))

if __name__ == '__main__':
    main()