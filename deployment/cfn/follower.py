"""Mesos Follower Node"""

from troposphere import (
    Parameter,
    Tags,
    Ref,
    Base64,
    ec2)

import template_utils as utils
import troposphere.autoscaling as asg


class MesosFollower(utils.GTStackNode):
    """Stack node for mesos follower machines

    This sets up a CloudFormation stack for mesos follower
    machines.

    Most of the configuration comes from the `geotrellis-cluster.config`
    file; however, it does depend on a few outputs from the VPC stack
    """

    INPUTS = {
        'NameSpace': ['global:NameSpace'],
        'AvailabilityZone': ['VPC:AvailabilityZone'],
        'Tags': ['global:Tags'],
        'Region': ['global:Region'],
        'StackType': ['global:StackType'],
        'KeyName': ['global:KeyName'],
        'IPAccess': ['global:IPAccess'],
        'PrivateHostedZoneId': ['VPC:PrivateHostedZoneId'],
        'MesosFollowerAMI': ['global:MesosFollowerAMI'],
        'NumFollowers': ['global:NumFollowers'],
        'MesosFollowerInstanceProfile': ['global:MesosFollowerInstanceProfile'],
        'MesosFollowerSpotPrice': ['global:MesosFollowerSpotPrice'],
        'MesosSubnet': ['VPC:MesosSubnet'],
        'MesosFollowerInstanceType': ['global:MesosFollowerInstanceType'],
        'VpcId': ['global:VpcId', 'VPC:VpcId']
    }

    ATTRIBUTES = {'NameSpace': 'NameSpace'}

    DEFAULTS = {
        'Tags': {},
        'MesosFollowerSpotPrice': None,
        'NumFollowers': '2',
        'MesosFollowerAMI': None
    }

    MACHINE_TYPE = 'mesos-follower'
    AMI_INPUT = 'MesosFollowerAMI'

    def set_up_stack(self):
        self.region = self.get_input('Region')

        vpc_param = self.add_parameter(Parameter(
            'VpcId', Type='String', Description='Name of an existing VPC'
        ), source='VpcId')

        keyname_param = self.add_parameter(Parameter(
            'KeyName', Type='String', Default='geotrellis-spark-test',
            Description='Name of an existing EC2 key pair'
        ), source='KeyName')

        ip_access = self.get_input('IPAccess')
        office_cidr_param = self.add_parameter(Parameter(
            'OfficeCIDR', Type='String', Default=ip_access,
            Description='CIDR notation of office IP addresses'
        ), source='IPAccess')

        mesos_follower_ami_param = self.add_parameter(Parameter(
            'MesosFollowerAMI', Type='String',
            Description='Mesos follower AMI'
        ), source='MesosFollowerAMI')

        mesos_follower_instance_profile_param = self.add_parameter(Parameter(
            'MesosFollowerInstanceProfile', Type='String',
            Default='MesosFollowerInstanceProfile',
            Description='Physical resource ID of an AWS::IAM::Role for the followers'
        ), source='MesosFollowerInstanceProfile')

        mesos_follower_instance_type_param = self.add_parameter(Parameter(
            'MesosFollowerInstanceType', Type='String', Default='i2.2xlarge',
            Description='Follower EC2 instance type',
            AllowedValues=utils.EC2_INSTANCE_TYPES,
            ConstraintDescription='must be a valid EC2 instance type.'
        ), source='MesosFollowerInstanceType')

        mesos_follower_subnet_param = self.add_parameter(Parameter(
            'MesosSubnet', Type='CommaDelimitedList',
            Description='A list of subnets to associate with the Mesos leaders'
        ), source='MesosSubnet')

        mesos_follower_security_group = self.add_resource(ec2.SecurityGroup(
            'sgMesosFollower',
            GroupDescription='Enables access to the MesosFollower',
            VpcId=Ref(vpc_param),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(IpProtocol='tcp', CidrIp=Ref(office_cidr_param),
                                      FromPort=p, ToPort=p)
                for p in [22, 5050, 5051]
            ] + [
                ec2.SecurityGroupRule(
                    IpProtocol='tcp', CidrIp=utils.VPC_CIDR, FromPort=0, ToPort=65535
                )
            ],
            SecurityGroupEgress=[
                ec2.SecurityGroupRule(
                    IpProtocol='tcp', CidrIp=utils.VPC_CIDR, FromPort=0, ToPort=65535
                )
            ] + [
                ec2.SecurityGroupRule(IpProtocol='tcp', CidrIp=utils.ALLOW_ALL_CIDR,
                                      FromPort=p, ToPort=p)
                for p in [80, 443]
            ],
            Tags=Tags(Name='sgMesosFollower')
        ))

        extra_launch_config_args = dict(
            AssociatePublicIpAddress=True,
            ImageId=self.ami,
            IamInstanceProfile=Ref(mesos_follower_instance_profile_param),
            InstanceType=Ref(mesos_follower_instance_type_param),
            KeyName=Ref(keyname_param),
            SecurityGroups=[Ref(mesos_follower_security_group)],
            UserData=Base64(utils.read_file('cloud-config/%s-follower.yml' % self.get_input('StackType')))
        )

        mesos_follower_spot_price = self.get_input('MesosFollowerSpotPrice')
        if mesos_follower_spot_price:
            extra_launch_config_args['SpotPrice'] = mesos_follower_spot_price

        mesos_follower_launch_config = self.add_resource(asg.LaunchConfiguration(
            'lcMesosFollower',
            BlockDeviceMappings=[
                {
                    "DeviceName": "/dev/sdb",
                    "VirtualName": "ephemeral0"
                },
                {
                    "DeviceName": "/dev/sdc",
                    "VirtualName": "ephemeral1"
                },
                {
                    "DeviceName": "/dev/sdd",
                    "VirtualName": "ephemeral2"
                },
                {
                    "DeviceName": "/dev/sde",
                    "VirtualName": "ephemeral3"
                },
                {
                    "DeviceName": "/dev/sdf",
                    "VirtualName": "ephemeral4"
                },
                {
                    "DeviceName": "/dev/sdg",
                    "VirtualName": "ephemeral5"
                },
                {
                    "DeviceName": "/dev/sdh",
                    "VirtualName": "ephemeral6"
                },
                {
                    "DeviceName": "/dev/sdi",
                    "VirtualName": "ephemeral7"
                }
            ],
            **extra_launch_config_args
        ))

        availability_zone = self.get_input('AvailabilityZone')
        num_followers = self.get_input('NumFollowers')
        self.add_resource(asg.AutoScalingGroup(
            'asgMesosFollower',
            AvailabilityZones=[availability_zone],
            Cooldown=300,
            DesiredCapacity=num_followers,
            HealthCheckGracePeriod=600,
            HealthCheckType='EC2',
            LaunchConfigurationName=Ref(mesos_follower_launch_config),
            MaxSize=num_followers,
            MinSize=num_followers,
            VPCZoneIdentifier=Ref(mesos_follower_subnet_param),
            Tags=[asg.Tag('Name', 'MesosFollower', True)]
        ))
