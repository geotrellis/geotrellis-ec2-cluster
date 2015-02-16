#!/bin/bash

set -e

if env | grep -q "GEOTRELLIS_SPARK_DEPLOY_DEBUG"; then
  set -x
fi

function get_latest_ubuntu_ami() {
  # 1. Get list of daily Ubuntu AMIs
  # 2. Filter AMIs with EBS instance store, amd64 architecture, and in
  #    AWS_DEFAULT_REGION
  # 3. Filter again by HVM AMIs
  # 4. Sort by date in reverse
  # 5. Take the top row
  # 6. Take the 8th column
  curl -s "http://cloud-images.ubuntu.com/query/trusty/server/daily.txt" \
    | egrep "ebs\s+amd64\s+${AWS_DEFAULT_REGION}" \
    | grep "hvm" \
    | sort -k4 -r \
    | head -n1 \
    | cut -f8
}

function get_stack_outputs() {
  aws cloudformation describe-stacks \
    --stack-name "${1}" \
    --query "Stacks[*].Outputs[*].[OutputKey, OutputValue]"
}

function wait_for_stack() {
  local n=0

  until [ $n -ge 15 ]  # 15 * 60 = 900 = 15 minutes
  do
    echo "Waiting for stack..."

    aws cloudformation describe-stacks \
      --stack-name "${1}" \
      | cut -f"7,8" \
      | egrep -q "(CREATE|UPDATE|ROLLBACK)_COMPLETE" && break

    n=$[$n+1]
    sleep 60
  done

  aws cloudformation describe-stacks \
    --stack-name "${1}"
}

function get_latest_internal_ami() {
  # 1. Get list of AMIs owned by this account
  # 2. Filter by type (only argument to this function)
  # 3. Filter again for the IMAGES row
  # 4. Sort by AMI name (contains a date created timestamp)
  # 5. Take the top row
  # 6. Take the 4th column
  aws ec2 describe-images \
    --owners self \
    | grep "${1}" \
    | grep IMAGES \
    | sort -k5 -r \
    | head -n1 \
    | cut -f5
}

function create_ami() {
  # Build an AMI for the application servers
  packer build \
    -only="${1}" \
    -var "aws_ubuntu_ami=$(get_latest_ubuntu_ami)" \
    packer/template.js
}

case "$1" in

  create-vpc-stack)
    # Create VPC stack
    aws cloudformation create-stack
      --stack-name "GeoTrellisSparkVPC" \
      --template-body "file://troposphere/vpc_template.json"

    wait_for_stack "GeoTrellisSparkVPC"
    ;;


  create-private-hosted-zones)
    # Get CloudFormation VPC stack outputs
    AWS_VPC_STACK_OUTPUTS=$(get_stack_outputs "GeoTrellisSparkVPC")

    # Create private DNS hosted zone
    aws route53 create-hosted-zone \
      --name geotrellis-spark.internal \
      --caller-reference "create-hosted-zone-$(date +"%Y-%m-%d-%H:%M")" \
      --vpc "VPCRegion=${AWS_DEFAULT_REGION},VPCId=$(echo "${AWS_VPC_STACK_OUTPUTS}" | grep "VpcId" | cut -f2)" \
      --hosted-zone-config "Comment=create-hosted-zone"
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

    aws cloudformation create-stack \
      --stack-name "GeoTrellisSparkMesosLeaders" \
      --template-body "file://troposphere/leader_template.json" \
      --parameters ${AWS_STACK_PARAMS}

    wait_for_stack "GeoTrellisSparkMesosLeaders"
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
    aws cloudformation create-stack \
      --stack-name "GeoTrellisSparkMesosFollowers" \
      --template-body "file://troposphere/follower_template.json" \
      --parameters ${AWS_STACK_PARAMS}

    wait_for_stack "GeoTrellisSparkMesosFollowers"
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
    echo "    - create-private-hosted-zones"
    echo "    - create-leader-stack"
    echo "    - create-follower-stack"
    echo "    - create-leader-ami"
    echo "    - create-follower-ami"
    exit 1
    ;;

esac

exit 0
