from troposphere import Template, Parameter, Ref, Output, Tags, ec2

import template_utils as utils

t = Template()

t.add_version('2010-09-09')
t.add_description('A VPC stack for the geotrellis-spark project.')

#
# Parameters
#
office_cidr_param = t.add_parameter(Parameter(
    'OfficeCIDR', Type='String', Default='216.158.51.82/32',
    Description='CIDR notation of office IP addresses'
))

#
# VPC Resources
#
vpc = t.add_resource(ec2.VPC(
    'GeoTrellisSparkVPC', CidrBlock=utils.VPC_CIDR, EnableDnsSupport=True,
    EnableDnsHostnames=True,
    Tags=Tags(Name='GeoTrellisSparkVPC')
))

gateway = t.add_resource(ec2.InternetGateway(
    'InternetGateway', Tags=Tags(Name='InternetGateway')
))

gateway_attachment = t.add_resource(ec2.VPCGatewayAttachment(
    'VPCGatewayAttachment', VpcId=Ref(vpc), InternetGatewayId=Ref(gateway)
))

public_route_table = t.add_resource(ec2.RouteTable(
    'PublicRouteTable', VpcId=Ref(vpc), Tags=Tags(Name='PublicRouteTable')
))

t.add_resource(ec2.Route(
    'PublicRoute', RouteTableId=Ref(public_route_table),
    DestinationCidrBlock=utils.ALLOW_ALL_CIDR,
    DependsOn=gateway_attachment.title, GatewayId=Ref(gateway)
))

availability_zone = utils.EC2_AVAILABILITY_ZONES[0]

public_subnet = t.add_resource(ec2.Subnet(
    'USEast1%sPublicSubnet' % availability_zone.upper(), VpcId=Ref(vpc),
    CidrBlock='10.0.1.0/24',
    AvailabilityZone='us-east-1%s' % availability_zone,
    Tags=Tags(Name='USEast1%sPublicSubnet' % availability_zone.upper())
))

t.add_resource(ec2.SubnetRouteTableAssociation(
    '%sPublicRouteTableAssociation' % public_subnet.title,
    SubnetId=Ref(public_subnet),
    RouteTableId=Ref(public_route_table)
))

#
# Outputs
#
t.add_output([
    Output(
        'VpcId',
        Description='VPC ID',
        Value=Ref(vpc)
    ),
    Output(
        'MesosSubnet',
        Description='Subnet associated with the Mesos cluster',
        Value=Ref(public_subnet)
    )
])

if __name__ == '__main__':
    utils.validate_cloudformation_template(t.to_json())

    file_name = __file__.replace('.py', '.json')

    with open(file_name, 'w') as f:
        f.write(t.to_json())

    print('Template validated and written to %s' % file_name)
