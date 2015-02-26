VPC_CIDR = '10.0.0.0/16'
ALLOW_ALL_CIDR = '0.0.0.0/0'

EC2_REGIONS = [
    'us-east-1'
]
EC2_AVAILABILITY_ZONES = [
    'c',
]
EC2_INSTANCE_TYPES = [
    'c4.8xlarge',
    'c3.2xlarge',
    'cc1.4xlarge',
    'i2.xlarge',
    'i2.2xlarge',
    'i2.4xlarge',
    'i2.8xlarge',
    'm2.4xlarge',
    'm3.large',
    'm3.2xlarge',
    'r3.large',
    'r3.2xlarge'
]


def read_file(file_name):
    """Reads an entire file and returns it as a string

    Arguments
    :param file_name: A path to a file
    """
    with open(file_name, 'r') as f:
        return f.read()
