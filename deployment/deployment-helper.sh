#!/bin/bash

set -e

export AWS_DEFAULT_REGION="us-east-1"
export AWS_DEFAULT_OUTPUT="text"
export AWS_KEY_NAME="geotrellis-spark-test"
export AWS_SNS_TOPIC="arn:aws:sns:us-east-1:784347171332:topicGlobalNotifications"

function get_latest_ubuntu_ami() {
  # 1. Get list of daily Ubuntu AMIs
  # 2. Filter AMIs with EBS instance store, amd64 architecture, and in
  #    AWS_DEFAULT_REGION
  # 3. Filter again by HVM AMIs
  # 4. Sort by date in reverse
  # 5. Take the top row
  # 6. Take the 8th column
  curl -s "http://cloud-images.ubuntu.com/query/trusty/server/daily.txt" \
    | grep "ebs\tamd64\t${AWS_DEFAULT_REGION}" \
    | grep "hvm" \
    | sort -k4 -r \
    | head -n1 \
    | cut -f8
}

function get_stack_outputs() {
  aws cloudformation describe-stacks --profile geotrellis-spark-test \
    --stack-name "${1}" \
    --output text --query "Stacks[*].Outputs[*].[OutputKey, OutputValue]"
}

function get_latest_internal_ami() {
  # 1. Get list of AMIs owned by this account
  # 2. Filter by type (only argument to this function)
  # 3. Filter again for the IMAGES row
  # 4. Sort by AMI name (contains a date created timestamp)
  # 5. Take the top row
  # 6. Take the 4th column
  aws ec2 describe-images --owners self \
    | grep "${1}" \
    | grep IMAGES \
    | sort -k5 -r \
    | head -n1 \
    | cut -f4
}

function create_ami() {
  # Get CloudFormation VPC stack outputs
  AWS_VPC_STACK_OUTPUTS=$(get_stack_outputs "GeoTrellisSparkVPC")

  # Build an AMI for the application servers
  # TODO: Remove --debug
  packer build --debug \
    -only="${1}" \
    -var "aws_ubuntu_ami=$(get_latest_ubuntu_ami)" \
    -var "aws_vpc_id=$(echo "${AWS_VPC_STACK_OUTPUTS}" | grep "VpcId" | cut -f2)" \
    -var "aws_subnet=$(echo "${AWS_VPC_STACK_OUTPUTS}" | grep "MesosSubnet" | cut -f2)" \
    packer/template.js
}

case "$1" in

  create-vpc-stack)
    # Create VPC stack
    aws cloudformation create-stack --profile geotrellis-spark-test \
      --stack-name "GeoTrellisSparkVPC" \
      --template-body "file://troposphere/vpc_template.json"
    ;;


  create-leader-stack)
    # Get CloudFormation VPC stack outputs
    AWS_VPC_STACK_OUTPUTS=$(get_stack_outputs "GeoTrellisSparkVPC")

    AWS_VPC_ID=$(echo "${AWS_VPC_STACK_OUTPUTS}" | grep "VpcId" | cut -f2)
    AWS_MESOS_SUBNET=$(echo "${AWS_VPC_STACK_OUTPUTS}" | grep "MesosSubnet" | cut -f2)
    MESOS_LEADER_AMI=$(get_latest_internal_ami "mesos-leader")

    # Build parameters argument
    AWS_STACK_PARAMS="ParameterKey=KeyName,ParameterValue=${AWS_KEY_NAME}"
    AWS_STACK_PARAMS="${AWS_STACK_PARAMS} ParameterKey=VpcId,ParameterValue=${AWS_VPC_ID}"
    AWS_STACK_PARAMS="${AWS_STACK_PARAMS} ParameterKey=MesosLeaderAMI,ParameterValue=${MESOS_LEADER_AMI}"
    AWS_STACK_PARAMS="${AWS_STACK_PARAMS} ParameterKey=MesosLeaderSubnet,ParameterValue=${AWS_MESOS_SUBNET}"

    aws cloudformation create-stack --profile geotrellis-spark-test \
      --stack-name "GeoTrellisSparkMesosLeaders" \
      --template-body "file://troposphere/leader_template.json" \
      --parameters ${AWS_STACK_PARAMS}
    ;;


  create-follower-stack)
    # Get CloudFormation VPC stack outputs
    AWS_VPC_STACK_OUTPUTS=$(get_stack_outputs "GeoTrellisSparkVPC")

    AWS_VPC_ID=$(echo "${AWS_VPC_STACK_OUTPUTS}" | grep "VpcId" | cut -f2)
    AWS_MESOS_SUBNET=$(echo "${AWS_VPC_STACK_OUTPUTS}" | grep "MesosSubnet" | cut -f2)
    MESOS_FOLLOWER_AMI=$(get_latest_internal_ami "mesos-follower" )

    # Build parameters argument
    AWS_STACK_PARAMS="ParameterKey=KeyName,ParameterValue=${AWS_KEY_NAME}"
    AWS_STACK_PARAMS="${AWS_STACK_PARAMS} ParameterKey=VpcId,ParameterValue=${AWS_VPC_ID}"
    AWS_STACK_PARAMS="${AWS_STACK_PARAMS} ParameterKey=GlobalNotificationsARN,ParameterValue=${AWS_SNS_TOPIC}"
    AWS_STACK_PARAMS="${AWS_STACK_PARAMS} ParameterKey=MesosFollowerAMI,ParameterValue=${MESOS_FOLLOWER_AMI}"
    AWS_STACK_PARAMS="${AWS_STACK_PARAMS} ParameterKey=MesosFollowerSubnet,ParameterValue=${AWS_MESOS_SUBNET}"

    # Create cluster follower server stack
    aws cloudformation create-stack --profile geotrellis-spark-test \
      --stack-name "GeoTrellisSparkMesosFollowers" \
      --template-body "file://troposphere/follower_template.json" \
      --parameters ${AWS_STACK_PARAMS}
    ;;


  create-leader-ami)
    create_ami "mesos-leader"
    ;;


  create-follower-ami)
    create_ami "mesos-follower"
    ;;


  *)
    echo "Usage: deployment-helper.sh {command}"
    echo ""
    echo "  Commands:"
    echo ""
    echo "    - create-vpc-stack"
    echo "    - create-leader-stack"
    echo "    - create-follower-stack"
    echo "    - create-leader-ami"
    echo "    - create-follower-ami"
    exit 1
    ;;

esac

exit 0
