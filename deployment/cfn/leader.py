from troposphere import (
    Parameter,
    Ref,
    GetAtt,
    Tags,
    Base64,
    ec2)

import template_utils as utils
import troposphere.route53 as r53


class MesosLeader(utils.GTStackNode):
    """Leader stack"""

    INPUTS = {
        'NameSpace': ['global:NameSpace'],
        'Tags': ['global:Tags'],
        'StackType': ['global:StackType'],
        'KeyName': ['global:KeyName'],
        'IPAccess': ['global:IPAccess'],
        'Region': ['global:Region'],
        'PrivateHostedZoneId': ['R53PrivateHostedZone:PrivateHostedZoneId'],
        'MesosLeaderAMI': ['global:MesosLeaderAMI'],
        'MesosLeaderInstanceProfile': ['global:MesosLeaderInstanceProfile'],
        'MesosSubnet': ['VPC:MesosSubnet'],
        'MesosLeaderInstanceType': ['global:MesosLeaderInstanceType'],
        'VpcId': ['global:VpcId', 'VPC:VpcId']
    }

    DEFAULTS = {
        'Tags': {},
        'MesosLeaderAMI': None
    }

    ATTRIBUTES = {'NameSpace': 'NameSpace'}

    MACHINE_TYPE = 'mesos-leader'
    AMI_INPUT = 'MesosLeaderAMI'

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

        private_hosted_zone_id_param = self.add_parameter(Parameter(
            'PrivateHostedZoneId', Type='String',
            Description='Hosted zone ID for private record set'
        ), source='PrivateHostedZoneId')

        mesos_leader_ami_param = self.add_parameter(Parameter(
            'MesosLeaderAMI', Type='String',
            Description='Mesos leader AMI'
        ), source='MesosLeaderAMI')

        mesos_leader_instance_profile_param = self.add_parameter(Parameter(
            'MesosLeaderInstanceProfile', Type='String',
            Default='MesosLeaderInstanceProfile',
            Description='Physical resource ID of an AWS::IAM::Role for the leader'
        ), source='MesosLeaderInstanceProfile')

        mesos_leader_instance_type_param = self.add_parameter(Parameter(
            'MesosLeaderInstanceType', Type='String', Default='r3.large',
            Description='Leader EC2 instance type',
            AllowedValues=utils.EC2_INSTANCE_TYPES,
            ConstraintDescription='must be a valid EC2 instance type.'
        ), source='MesosLeaderInstanceType')

        mesos_leader_subnet_param = self.add_parameter(Parameter(
            'MesosSubnet', Type='CommaDelimitedList',
            Description='A list of subnets to associate with the Mesos leaders'
        ), source='MesosSubnet')

        mesos_leader_security_group = self.add_resource(ec2.SecurityGroup(
            'sgMesosLeader',
            GroupDescription='Enables access to the MesosLeader',
            VpcId=Ref(vpc_param),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(IpProtocol='tcp', CidrIp=Ref(office_cidr_param),
                                      FromPort=p, ToPort=p)
                for p in [
                        22,     # SSH
                        1723,   # PPTPD
                        2181,   # Zookeeper
                        4040,   # Spark
                        5050,   # Mesos
                        8080,   # Marathon
                        8081,   # Graphite Web
                        8090,   # Grafana
                        9200,   # ElasticSearch
                        50070,  # HDFS
                        50095   # Accumulo
                ]
            ] + [
                ec2.SecurityGroupRule(
                    IpProtocol='tcp', CidrIp=utils.VPC_CIDR, FromPort=0, ToPort=65535
                )
            ],
            SecurityGroupEgress=[
                ec2.SecurityGroupRule(
                    IpProtocol='-1', CidrIp=utils.ALLOW_ALL_CIDR,
                    FromPort=0, ToPort=65535
                )
            ],
            Tags=Tags(Name='sgMesosLeader')
        ))


        ## EC2 Instance Resources
        mesos_subnet = self.get_input('MesosSubnet')
        mesos_leader_instance = self.create_resource(ec2.Instance(
            'MesosLeader',
            BlockDeviceMappings=[
                {
                    "DeviceName": "/dev/sda1",
                    "Ebs": {"VolumeSize": "256"}
                }
            ],
            InstanceType=Ref(mesos_leader_instance_type_param),
            KeyName=Ref(keyname_param),
            ImageId=self.ami,
            IamInstanceProfile=Ref(mesos_leader_instance_profile_param),
            NetworkInterfaces=[
                ec2.NetworkInterfaceProperty(
                    Description='ENI for MesosLeader',
                    GroupSet=[Ref(mesos_leader_security_group)],
                    SubnetId=mesos_subnet,
                    AssociatePublicIpAddress=True,
                    DeviceIndex=0,
                    DeleteOnTermination=True,
                )
            ],
            UserData=Base64(utils.read_file('cloud-config/leader.yml')),
            Tags=Tags(Name='MesosLeader')
        ))

        ## Route 53 Resources
        self.create_resource(r53.RecordSetGroup(
            'dnsPrivateRecords',
            HostedZoneId=Ref(private_hosted_zone_id_param),
            RecordSets=[
                r53.RecordSet(
                    'dnsZookeeper',
                    Name='zookeeper.service.geotrellis-spark.internal.',
                    Type='A',
                    TTL='60',
                    ResourceRecords=[GetAtt(mesos_leader_instance, 'PrivateIp')]
                ),
                r53.RecordSet(
                    'dnsMesosLeader',
                    Name='mesos-leader.service.geotrellis-spark.internal.',
                    Type='A',
                    TTL='60',
                    ResourceRecords=[GetAtt(mesos_leader_instance, 'PrivateIp')]
                ),
                r53.RecordSet(
                    'dnsNameNode',
                    Name='namenode.service.geotrellis-spark.internal.',
                    Type='A',
                    TTL='60',
                    ResourceRecords=[GetAtt(mesos_leader_instance, 'PrivateIp')]
                ),
                r53.RecordSet(
                    'dnsAccumulo',
                    Name='accumulo-leader.service.geotrellis-spark.internal.',
                    Type='A',
                    TTL='60',
                    ResourceRecords=[GetAtt(mesos_leader_instance, 'PrivateIp')]
                ),
                r53.RecordSet(
                    'dnsMonitoring',
                    Name='monitoring.service.geotrellis-spark.internal.',
                    Type='A',
                    TTL='60',
                    ResourceRecords=[GetAtt(mesos_leader_instance, 'PrivateIp')]
                )
            ]
        ))
