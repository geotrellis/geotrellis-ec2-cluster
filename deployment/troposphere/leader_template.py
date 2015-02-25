from troposphere import Template, Parameter, Ref, GetAtt, Tags, Base64, \
    Select, ec2

import template_utils as utils
import troposphere.route53 as r53

t = Template()

t.add_version('2010-09-09')
t.add_description('A Mesos leader stack for the geotrellis-spark project.')

#
# Parameters
#
vpc_param = t.add_parameter(Parameter(
    'VpcId', Type='String', Description='Name of an existing VPC'
))

private_hosted_zone_id_param = t.add_parameter(Parameter(
    'PrivateHostedZoneId', Type='String',
    Description='Hosted zone ID for private record set'
))

keyname_param = t.add_parameter(Parameter(
    'KeyName', Type='String', Default='geotrellis-spark-test',
    Description='Name of an existing EC2 key pair'
))

office_cidr_param = t.add_parameter(Parameter(
    'OfficeCIDR', Type='String', Default='216.158.51.82/32',
    Description='CIDR notation of office IP addresses'
))

mesos_leader_ami_param = t.add_parameter(Parameter(
    'MesosLeaderAMI', Type='String', Default='ami-9854cbf0',
    Description='Mesos leader AMI'
))

mesos_leader_instance_profile_param = t.add_parameter(Parameter(
    'MesosLeaderInstanceProfile', Type='String',
    Default='MesosLeaderInstanceProfile',
    Description='Physical resource ID of an AWS::IAM::Role for the leader'
))

mesos_leader_instance_type_param = t.add_parameter(Parameter(
    'MesosLeaderInstanceType', Type='String', Default='r3.large',
    Description='Leader EC2 instance type',
    AllowedValues=utils.EC2_INSTANCE_TYPES,
    ConstraintDescription='must be a valid EC2 instance type.'
))

mesos_leader_subnet_param = t.add_parameter(Parameter(
    'MesosLeaderSubnet', Type='CommaDelimitedList',
    Description='A list of subnets to associate with the Mesos leaders'
))

#
# Security Group Resources
#
mesos_leader_security_group = t.add_resource(ec2.SecurityGroup(
    'sgMesosLeader',
    GroupDescription='Enables access to the MesosLeader',
    VpcId=Ref(vpc_param),
    SecurityGroupIngress=[
        ec2.SecurityGroupRule(IpProtocol='tcp', CidrIp=Ref(office_cidr_param),
                              FromPort=p, ToPort=p)
        for p in [22, 1723, 4040, 5050, 8080, 50070, 50095]
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

#
# EC2 Instance Resources
#
mesos_leader = t.add_resource(ec2.Instance(
    'MesosLeader',
    BlockDeviceMappings=[
        {
            "DeviceName": "/dev/sda1",
            "Ebs": {"VolumeSize": "256"}
        }
    ],
    InstanceType=Ref(mesos_leader_instance_type_param),
    KeyName=Ref(keyname_param),
    ImageId=Ref(mesos_leader_ami_param),
    IamInstanceProfile=Ref(mesos_leader_instance_profile_param),
    NetworkInterfaces=[
        ec2.NetworkInterfaceProperty(
            Description='ENI for MesosLeader',
            GroupSet=[Ref(mesos_leader_security_group)],
            SubnetId=Select("0", Ref(mesos_leader_subnet_param)),
            AssociatePublicIpAddress=True,
            DeviceIndex=0,
            DeleteOnTermination=True,
        )
    ],
    Tags=Tags(Name='MesosLeader')
))

#
# Route 53 Resources
#
mesos_leader_private_dns = t.add_resource(r53.RecordSetGroup(
    'dnsPrivateRecords',
    HostedZoneId=Ref(private_hosted_zone_id_param),
    RecordSets=[
        r53.RecordSet(
            'dnsZookeeper',
            Name='zookeeper.service.geotrellis-spark.internal.',
            Type='A',
            TTL='60',
            ResourceRecords=[GetAtt(mesos_leader, 'PrivateIp')]
        ),
        r53.RecordSet(
            'dnsMesosLeader',
            Name='mesos-leader.service.geotrellis-spark.internal.',
            Type='A',
            TTL='60',
            ResourceRecords=[GetAtt(mesos_leader, 'PrivateIp')]
        ),
        r53.RecordSet(
            'dnsNameNode',
            Name='namenode.service.geotrellis-spark.internal.',
            Type='A',
            TTL='60',
            ResourceRecords=[GetAtt(mesos_leader, 'PrivateIp')]
        ),
        r53.RecordSet(
            'dnsAccumulo',
            Name='accumulo-leader.service.geotrellis-spark.internal.',
            Type='A',
            TTL='60',
            ResourceRecords=[GetAtt(mesos_leader, 'PrivateIp')]
        )
    ]
))

if __name__ == '__main__':
    print t.to_json()
