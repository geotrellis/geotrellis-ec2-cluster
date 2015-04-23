
from majorkirby import GlobalConfigNode

from vpc import VPC
from leader import MesosLeader
from follower import MesosFollower
from privatehostedzone import R53PrivateHostedZone


def build_graph(aws_profile, gt_config):
    """
    Builds graphs for mesos follower and mesos leader stacks

    Args:
      aws_profile (str): name of AWS profile to use for authentication
      gt_config (dict): dictionary representation of `geotrellis-cluster.config`

    Returns:
      cloudformation stack graphs (mesos-leader, mesos-follower)
    """
    global_config = GlobalConfigNode(**gt_config)
    vpc = VPC(globalconfig=global_config, aws_profile=aws_profile)
    private_hosted_zone = R53PrivateHostedZone(globalconfig=global_config, VPC=vpc, aws_profile=aws_profile)
    mesos_leader = MesosLeader(
        globalconfig=global_config, VPC=vpc, R53PrivateHostedZone=private_hosted_zone,
        aws_profile=aws_profile)
    mesos_follower = MesosFollower(
        globalconfig=global_config, VPC=vpc, MesosLeader=mesos_leader, R53PrivateHostedZone=private_hosted_zone,
        aws_profile=aws_profile)
    return mesos_follower, mesos_leader


def build_stacks(aws_profile, gt_config):
    """Trigger actual building of graphs"""
    follower_graph, leader_graph = build_graph(aws_profile, gt_config)
    leader_graph.go()
    follower_graph.go()
