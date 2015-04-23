from troposphere import (
    Template,
    Parameter,
    Output,
    Ref,
    Tags,
    ec2)

import template_utils as utils
from majorkirby import StackNode
import boto
import boto.ec2


class VPC(StackNode):
    INPUTS = {'Tags': ['global:Tags'],
              'Region': ['global:Region'],
              'StackType': ['global:StackType'],
              'IPAccess': ['global:IPAccess']}

    DEFAULTS = {
        'Tags': {},
    }

    def set_up_stack(self):
        super(VPC, self).set_up_stack()
        tags = self.get_input('Tags').copy()
        tags.update({'StackType': 'VPC'})

        self.region = self.get_input('Region')

        ip_access = self.get_input('IPAccess')
        self.add_parameter(Parameter(
            'OfficeCIDR', Type='String', Default='{}/32'.format(ip_access),
            Description='CIDR notation of office IP addresses to allow access from'
        ))
        vpc = self.create_resource(
            ec2.VPC(
                'GeoTrellisSparkVPC', CidrBlock=utils.VPC_CIDR, EnableDnsSupport=True,
                EnableDnsHostnames=True,
                Tags=Tags(Name='GeoTrellisSparkVPC')
            ), output='VpcId'
        )

        gateway = self.create_resource(ec2.InternetGateway(
            'InternetGateway', Tags=Tags(Name='InternetGateway')
        ))

        gateway_attachment = self.create_resource(ec2.VPCGatewayAttachment(
            'VPCGatewayAttachment', VpcId=Ref(vpc), InternetGatewayId=Ref(gateway)
        ))

        public_route_table = self.create_resource(ec2.RouteTable(
            'PublicRouteTable', VpcId=Ref(vpc), Tags=Tags(Name='PublicRouteTable')
        ))

        self.create_resource(ec2.Route(
            'PublicRoute', RouteTableId=Ref(public_route_table),
            DestinationCidrBlock=utils.ALLOW_ALL_CIDR,
            DependsOn=gateway_attachment.title, GatewayId=Ref(gateway)
        ))

        region = self.get_input('Region')
        conn = boto.ec2.connect_to_region(region)
        zone = conn.get_all_zones()[0]

        self.add_output(Output('AvailabilityZone', Value=zone.name))

        public_subnet = self.create_resource(ec2.Subnet(
            '{zone}PublicSubnet'.format(zone=zone.name.title().replace('-', '')),
            VpcId=Ref(vpc), CidrBlock='10.0.1.0/24',
            AvailabilityZone='{}'.format(zone.name),
            Tags=Tags(Name='{}PublicSubnet'.format(zone.name.title().replace('-', '')))
        ), output='MesosSubnet')

        self.create_resource(ec2.SubnetRouteTableAssociation(
            '%sPublicRouteTableAssociation' % public_subnet.title,
            SubnetId=Ref(public_subnet),
            RouteTableId=Ref(public_route_table)
        ))
