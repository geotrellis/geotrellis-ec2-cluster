from troposphere import Template, Parameter, Ref, Base64, ec2

import template_utils as utils
import troposphere.autoscaling as asg

t = Template()

t.add_version('2010-09-09')
t.add_description('A Mesos follower stack for the geotrellis-spark project.')

#
# Parameters
#
vpc_param = t.add_parameter(Parameter(
    'VpcId', Type='String', Description='Name of an existing VPC'
))

keyname_param = t.add_parameter(Parameter(
    'KeyName', Type='String', Default='geotrellis-spark-test',
    Description='Name of an existing EC2 key pair'
))

office_cidr_param = t.add_parameter(Parameter(
    'OfficeCIDR', Type='String', Default='216.158.51.82/32',
    Description='CIDR notation of office IP addresses'
))

notification_arn_param = t.add_parameter(Parameter(
    'GlobalNotificationsARN', Type='String',
    Description='Physical resource ID of an AWS::SNS::Topic for notifications'
))

mesos_follower_ami_param = t.add_parameter(Parameter(
    'MesosFollowerAMI', Type='String', Default='ami-9854cbf0',
    Description='Mesos follower AMI'
))

mesos_follower_instance_profile_param = t.add_parameter(Parameter(
    'MesosFollowerInstanceProfile', Type='String',
    Default=
    'arn:aws:iam::784347171332:instance-profile/MesosFollowerInstanceProfile',
    Description='Physical resource ID of an AWS::IAM::Role for the followers'
))

mesos_follower_subnet_param = t.add_parameter(Parameter(
    'MesosFollowerSubnet', Type='CommaDelimitedList',
    Description='A list of subnets to associate with the Mesos followers'
))

#
# Security Group Resources
#
mesos_follower_security_group = utils.create_security_group(
    t, 'sgMesosFollower', 'Enables access to the MesosFollower', vpc_param,
    ingress=[
        ec2.SecurityGroupRule(IpProtocol='tcp', CidrIp=Ref(office_cidr_param),
                              FromPort=p, ToPort=p)
        for p in [22, 5050, 5051]
    ] + [
        ec2.SecurityGroupRule(
            IpProtocol='tcp', CidrIp=utils.VPC_CIDR, FromPort=0, ToPort=65535
        )
    ],
    egress=[
        ec2.SecurityGroupRule(
            IpProtocol='tcp', CidrIp=utils.VPC_CIDR, FromPort=0, ToPort=65535
        )
    ] + [
        ec2.SecurityGroupRule(IpProtocol='tcp', CidrIp=utils.ALLOW_ALL_CIDR,
                              FromPort=p, ToPort=p)
        for p in [80, 443]
    ]
)

#
# Resources
#
mesos_follower_launch_config = t.add_resource(asg.LaunchConfiguration(
    'lcMesosFollower',
    AssociatePublicIpAddress=True,
    BlockDeviceMappings=[
        {
            "DeviceName": "/dev/sdb",
            "VirtualName": "ephemeral0"
        }
    ],
    ImageId=Ref(mesos_follower_ami_param),
    IamInstanceProfile=Ref(mesos_follower_instance_profile_param),
    InstanceType='m3.medium',
    KeyName=Ref(keyname_param),
    SecurityGroups=[Ref(mesos_follower_security_group)],
    SpotPrice='0.452',
    UserData=Base64(utils.read_file('cloud-config/follower.yml'))
))

mesos_follower_auto_scaling_group = t.add_resource(asg.AutoScalingGroup(
    'asgMesosFollower',
    AvailabilityZones=['us-east-1%s' % utils.EC2_AVAILABILITY_ZONES[0]],
    Cooldown=300,
    DesiredCapacity=1,
    HealthCheckGracePeriod=600,
    HealthCheckType='EC2',
    LaunchConfigurationName=Ref(mesos_follower_launch_config),
    MaxSize=1,
    MinSize=1,
    NotificationConfiguration=asg.NotificationConfiguration(
        TopicARN=Ref(notification_arn_param),
        NotificationTypes=[
            asg.EC2_INSTANCE_LAUNCH,
            asg.EC2_INSTANCE_LAUNCH_ERROR,
            asg.EC2_INSTANCE_TERMINATE,
            asg.EC2_INSTANCE_TERMINATE_ERROR
        ]
    ),
    # TODO: Add PlacementGroup
    VPCZoneIdentifier=Ref(mesos_follower_subnet_param),
    Tags=[asg.Tag('Name', 'MesosFollower', True)]
))

if __name__ == '__main__':
    utils.validate_cloudformation_template(t.to_json())

    file_name = __file__.replace('.py', '.json')

    with open(file_name, 'w') as f:
        f.write(t.to_json())

    print('Template validated and written to %s' % file_name)
