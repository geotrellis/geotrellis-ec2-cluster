import ConfigParser
import boto.ec2
import majorkirby as mj

VPC_CIDR = '10.0.0.0/16'
ALLOW_ALL_CIDR = '0.0.0.0/0'

EC2_INSTANCE_TYPES = [
    'c4.8xlarge',
    'c3.2xlarge',
    'c3.4xlarge',
    'cc1.4xlarge',
    'i2.xlarge',
    'i2.2xlarge',
    'i2.4xlarge',
    'i2.8xlarge',
    'm2.4xlarge',
    'm3.large',
    'm3.2xlarge',
    'r3.large',
    'r3.2xlarge',
    'r3.4xlarge'
]


def read_file(file_name):
    """Reads an entire file and returns it as a string

    Arguments
    :param file_name: A path to a file
    """
    with open(file_name, 'r') as f:
        return f.read()


def get_config(gt_config_path, profile):
    """Loads a profile from config and returns a dict representation

    Args:
      gt_config_path (str): Path to config file to load
      profile (str): section to load from config file

    Returns:
      dict representation of config
    """
    gt_config = ConfigParser.ConfigParser()
    gt_config.optionxform = str
    gt_config.read(gt_config_path)
    return {k: v.strip('"').strip("'") for k, v in gt_config.items(profile)}


class GTCloudFormationException(Exception):
    pass

def get_recent_ami(profile_name, machine_type, stack_type, region):
    """Helper function to get latest AMI for a given stack and machine in region

    Args:
      profile_name (str): AWS profile to use to authenticate with boto
      machine_type (str): Type of machine to get AMI for (e.g. `mesos-leader`)
      stack_type (str): Type of stack AMI built for (e.g. `accumulo`)
    """

    def filter_image(image):
        image_machine_type = image.tags.get('Name')
        image_stack_type = image.tags.get('StackType')
        return all([image_machine_type == machine_type,
                    image_stack_type == stack_type,
                    image.tags.get('Created')])

    conn = boto.ec2.connect_to_region(region, profile_name=profile_name)
    images = [image for image in conn.get_all_images(owners='self') if filter_image(image)]
    if len(images) == 0:
        exc = 'Unable to find AMI satisfying machine_type: {} and stack_type: {}'.format(
            machine_type, stack_type)
        raise GTCloudFormationException(exc)
    return sorted(images, key=lambda x: x.tags['Created'], reverse=True)[0]


class GTStackNode(mj.StackNode):
    """Custom GeoTrellis stack node to add AMI property

    This custom property is used to gather the most recent AMI
    for a stack's machine type and stack type.

    If an ami_id is specified in `geotrellis-cluster.config' then
    that ami id will take precedence.
    """
    @property
    def ami(self):
        stack_type = self.get_input('StackType')
        ami_id = self.get_input(self.AMI_INPUT)
        machine_type = self.MACHINE_TYPE
        if ami_id:
            return ami_id
        else:
            ami = get_recent_ami(self.aws_profile,
                                 machine_type,
                                 stack_type,
                                 self.region)
            return ami.id
