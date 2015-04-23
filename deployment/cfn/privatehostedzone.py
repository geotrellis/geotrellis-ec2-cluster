from boto import route53

from majorkirby import CustomActionNode

import json


class R53PrivateHostedZone(CustomActionNode):
    """Sets up a Route 53 Private Hosted Zone for the VPC

    The private hosted zone is necessary for custom internal
    hosts. This does not call CloudFormation, instead it uses
    boto to create the private hosted zone because it is not
    possible to create a private hosted zone in CloudFormation.
    """
    INPUTS = {'VpcId': ['global:VpcId', 'VPC:VpcId'],
              'PrivateHostedZoneName': ['global:PrivateHostedZoneName'],
              'Region': ['global:Region'],
              'StackType': ['global:StackType']}

    def action(self):
        self.region = self.get_input('Region')
        conn = route53.connect_to_region(self.region,
                                         profile_name=self.aws_profile)
        comment = json.dumps(self.get_raw_tags())

        hosted_zones = conn.get_all_hosted_zones()

        for hosted_zone in hosted_zones['ListHostedZonesResponse']['HostedZones']:
            if ('Comment' in hosted_zone['Config'] and
                    hosted_zone['Config']['Comment'] == comment):
                self.stack_outputs = {'PrivateHostedZoneId': hosted_zone['Id'].split('/')[-1]}
                return

        hosted_zone = conn.create_hosted_zone(self.get_input('PrivateHostedZoneName'),
                                              comment=comment,
                                              private_zone=True,
                                              vpc_id=self.get_input('VpcId'),
                                              vpc_region=self.region)
        hosted_zone_id = hosted_zone['CreateHostedZoneResponse']['HostedZone']['Id']
        self.stack_outputs = {'PrivateHostedZoneId': hosted_zone_id.split('/')[-1]}
