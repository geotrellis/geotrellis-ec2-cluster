{
  "variables": {
    "aws_region": "us-east-1",
    "aws_instance_type": "m3.medium",
    "aws_ssh_username": "ubuntu",
    "aws_access_key": "{{env `AWS_ACCESS_KEY_ID`}}",
    "aws_secret_key": "{{env `AWS_SECRET_ACCESS_KEY`}}",
    "aws_ubuntu_ami": "",
    "aws_vpc_id": "",
    "aws_subnet": ""
  },
  "builders": [
    {
      "name": "mesos-leader",
      "type": "amazon-ebs",
      "access_key": "{{user `aws_access_key`}}",
      "secret_key": "{{user `aws_secret_key` }}",
      "region": "{{user `aws_region`}}",
      "source_ami": "{{user `aws_ubuntu_ami`}}",
      "instance_type": "{{user `aws_instance_type`}}",
      "ssh_username": "{{user `aws_ssh_username`}}",
      "ami_name": "mesos-leader-{{timestamp}}",
      "tags": {
        "name": "mesos-leader"
      },
      "vpc_id": "{{user `aws_vpc_id`}}",
      "subnet_id": "{{user `aws_subnet`}}",
      "associate_public_ip_address": true
    },
    {
      "name": "mesos-follower",
      "type": "amazon-ebs",
      "access_key": "{{user `aws_access_key`}}",
      "secret_key": "{{user `aws_secret_key` }}",
      "region": "{{user `aws_region`}}",
      "source_ami": "{{user `aws_ubuntu_ami`}}",
      "instance_type": "{{user `aws_instance_type`}}",
      "ssh_username": "{{user `aws_ssh_username`}}",
      "ami_name": "mesos-follower-{{timestamp}}",
      "ami_block_device_mappings": [
        {
          "device_name": "/dev/sdb",
          "virtual_name": "ephemeral0"
        }
      ],
      "user_data_file": "cloud-config/packer.yml",
      "tags": {
        "name": "mesos-follower"
      },
      "vpc_id": "{{user `aws_vpc_id`}}",
      "subnet_id": "{{user `aws_subnet`}}",
      "associate_public_ip_address": true
    }
  ],
  "provisioners": [
    {
      "type": "shell",
      "inline": [
        "sleep 5",
        "sudo apt-get update -qq",
        "sudo apt-get install python-pip python-dev -y",
        "sudo pip install ansible==1.8.1"
      ]
    },
    {
      "type": "ansible-local",
      "playbook_file": "ansible/leader.yml",
      "playbook_dir": "ansible",
      "inventory_file": "ansible/inventory/packer-leader",
      "only": [
        "mesos-leader"
      ]
    },
    {
      "type": "ansible-local",
      "playbook_file": "ansible/follower.yml",
      "playbook_dir": "ansible",
      "inventory_file": "ansible/inventory/packer-follower",
      "only": [
        "mesos-follower"
      ]
    }
  ]
}
