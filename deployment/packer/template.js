{
  "variables": {
    "aws_region": "us-east-1",
    "aws_ssh_username": "ubuntu",
    "aws_ubuntu_ami": ""
  },
  "builders": [
    {
      "name": "mesos-leader",
      "type": "amazon-ebs",
      "region": "{{user `aws_region`}}",
      "source_ami": "{{user `aws_ubuntu_ami`}}",
      "instance_type": "r3.large",
      "ssh_username": "{{user `aws_ssh_username`}}",
      "ami_name": "mesos-leader-{{timestamp}}",
      "run_tags": {
        "PackerBuilder": "amazon-ebs"
      },
      "tags": {
        "Name": "mesos-leader",
        "Created": "{{ isotime }}"
      },
      "associate_public_ip_address": true
    },
    {
      "name": "mesos-follower",
      "type": "amazon-ebs",
      "region": "{{user `aws_region`}}",
      "source_ami": "{{user `aws_ubuntu_ami`}}",
      "instance_type": "i2.2xlarge",
      "ssh_username": "{{user `aws_ssh_username`}}",
      "ami_name": "mesos-follower-{{timestamp}}",
      "ami_block_device_mappings": [
        {
          "device_name": "/dev/xvdb",
          "virtual_name": "ephemeral0"
        },
        {
          "device_name": "/dev/xvdc",
          "virtual_name": "ephemeral1"
        }
      ],
      "user_data_file": "cloud-config/packer.yml",
      "run_tags": {
        "PackerBuilder": "amazon-ebs"
      },
      "tags": {
        "Name": "mesos-follower",
        "Created": "{{ isotime }}"
      },
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
        "sudo pip install ansible==1.8.2"
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
