VPC_CIDR = '10.0.0.0/16'
ALLOW_ALL_CIDR = '0.0.0.0/0'

EC2_REGIONS = [
    'us-east-1'
]
EC2_AVAILABILITY_ZONES = [
    'c',
]
EC2_INSTANCE_TYPES = [
    't2.medium'
]


def read_file(file_name):
    """Reads an entire file and returns it as a string

    Arguments
    :param file_name: A path to a file
    """
    with open(file_name, 'r') as f:
        return f.read()
