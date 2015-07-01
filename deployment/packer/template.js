{
  "variables": {
    "aws_region": "",
    "aws_ssh_username": "ubuntu",
    "aws_ubuntu_ami": "",
    "stack_type": ""
  },
  "builders": [
    {
      "name": "mesos-leader",
      "type": "amazon-ebs",
      "region": "{{user `aws_region`}}",
      "source_ami": "{{user `aws_ubuntu_ami`}}",
      "instance_type": "m3.large",
      "ssh_username": "{{user `aws_ssh_username`}}",
      "ami_name": "mesos-leader-{{timestamp}}",
      "user_data_file": "cloud-config/packer-{{user `stack_type`}}-leader.yml",
      "run_tags": {
        "PackerBuilder": "amazon-ebs"
      },
      "tags": {
        "Name": "mesos-leader",
        "Created": "{{ isotime }}",
        "StackType": "{{ user `stack_type` }}"
      },
      "associate_public_ip_address": true
    },
    {
      "name": "mesos-follower",
      "type": "amazon-ebs",
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
      "user_data_file": "cloud-config/packer-{{user `stack_type`}}-follower.yml",
      "run_tags": {
        "PackerBuilder": "amazon-ebs"
      },
      "tags": {
        "Name": "mesos-follower",
        "Created": "{{ isotime }}",
        "StackType": "{{ user `stack_type` }}"
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
        "sudo pip install ansible==1.9.0.1"
      ]
    },
    {
      "type": "ansible-local",
      "playbook_file": "ansible/{{user `stack_type`}}-leader.yml",
      "playbook_dir": "ansible",
      "inventory_file": "ansible/inventory/packer-{{user `stack_type`}}-leader",
      "only": [
        "mesos-leader"
      ]
    },
    {
      "type": "ansible-local",
      "playbook_file": "ansible/{{user `stack_type`}}-follower.yml",
      "playbook_dir": "ansible",
      "inventory_file": "ansible/inventory/packer-{{user `stack_type`}}-follower",
      "only": [
        "mesos-follower"
      ]
    }
  ]
}
