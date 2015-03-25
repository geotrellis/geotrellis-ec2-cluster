{
  "variables": {
    "aws_access_key": "",
    "aws_secret_key": "",
    "aws_region": "{{ env `AWS_DEFAULT_REGION`}}",
    "aws_ssh_username": "ubuntu",
    "aws_ubuntu_ami": ""
  },
  "builders": [
    {
      "name": "mesos-leader",
      "type": "amazon-ebs",
      "access_key": "{{ user `aws_access_key`}}",
      "secret_key": "{{ user `aws_secret_key`}}",
      "region": "{{user `aws_region`}}",
      "source_ami": "{{user `aws_ubuntu_ami`}}",
      "instance_type": "m3.large",
      "ssh_username": "{{user `aws_ssh_username`}}",
      "ami_name": "mesos-leader-{{timestamp}}",
      "user_data_file": "cloud-config/packer-leader.yml",
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
      "access_key": "{{ user `aws_access_key`}}",
      "secret_key": "{{ user `aws_secret_key`}}",
      "region": "{{user `aws_region`}}",
      "source_ami": "{{user `aws_ubuntu_ami`}}",
      "instance_type": "m3.large",
      "ssh_username": "{{user `aws_ssh_username`}}",
      "ami_name": "mesos-follower-{{timestamp}}",
      "ami_block_device_mappings": [
        {
          "device_name": "/dev/sdb",
          "virtual_name": "ephemeral0"
        }
      ],
      "user_data_file": "cloud-config/packer-follower.yml",
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
