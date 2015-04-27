# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.require_version ">= 1.5"
require "yaml"

# Deserialize Ansible Galaxy installation metadata for a role
def galaxy_install_info(role_name)
  role_path = File.join("deployment", "ansible", "roles", role_name)
  galaxy_install_info = File.join(role_path, "meta", ".galaxy_install_info")

  if (File.directory?(role_path) || File.symlink?(role_path)) && File.exists?(galaxy_install_info)
    YAML.load_file(galaxy_install_info)
  else
    { install_date: "", version: "0.0.0" }
  end
end

# Uses the contents of roles.txt to ensure that ansible-galaxy is run
# if any dependencies are missing
def install_dependent_roles
  ansible_directory = File.join("deployment", "ansible")
  ansible_roles_txt = File.join(ansible_directory, "roles.txt")

  File.foreach(ansible_roles_txt) do |line|
    role_name, role_version = line.split(",")
    role_path = File.join(ansible_directory, "roles", role_name)
    galaxy_metadata = galaxy_install_info(role_name)

    if galaxy_metadata["version"] != role_version.strip
      unless system("ansible-galaxy install -f -r #{ansible_roles_txt} -p #{File.dirname(role_path)}")
        $stderr.puts "\nERROR: An attempt to install Ansible role dependencies failed."
        exit(1)
      end

      break
    end
  end
end

# Install missing role dependencies based on the contents of roles.txt
if [ "up", "provision", "status" ].include?(ARGV.first)
  install_dependent_roles
end

ANSIBLE_INVENTORY_PATH = "deployment/ansible/inventory/development"
VAGRANT_PROXYCONF_ENDPOINT = ENV["VAGRANT_PROXYCONF_ENDPOINT"]
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/trusty64"

  # Wire up the proxy if:
  #
  #   - The vagrant-proxyconf Vagrant plugin is installed
  #   - The user set the VAGRANT_PROXYCONF_ENDPOINT environmental variable
  #
  if Vagrant.has_plugin?("vagrant-proxyconf") &&
     !VAGRANT_PROXYCONF_ENDPOINT.nil?
    config.proxy.http     = VAGRANT_PROXYCONF_ENDPOINT
    config.proxy.https    = VAGRANT_PROXYCONF_ENDPOINT
    config.proxy.no_proxy = "localhost,127.0.0.1"
  end

  if Vagrant.has_plugin?("vagrant-hostmanager")
    config.hostmanager.enabled = true
    config.hostmanager.manage_host = true
  else
    $stderr.puts "\nERROR: Please install the vagrant-hostmanager plugin."
    exit(1)
  end

  if Vagrant.has_plugin?("vagrant-cachier") &&
    VAGRANT_PROXYCONF_ENDPOINT.nil?
    config.cache.scope = :box
  end

  config.vm.define "leader" do |leader|
    leader.hostmanager.aliases = [
      "zookeeper.service.geotrellis-spark.internal",
      "namenode.service.geotrellis-spark.internal",
      "mesos-leader.service.geotrellis-spark.internal",
      "accumulo-leader.service.geotrellis-spark.internal",
      "monitoring.service.geotrellis-spark.internal"
    ]

    leader.vm.hostname = "leader"
    leader.vm.network "private_network", ip: "33.33.33.10"

    # Spark console
    leader.vm.network "forwarded_port", guest: 4040, host: 4040
    # Mesos console
    leader.vm.network "forwarded_port", guest: 5050, host: 5050
    # Marathon console
    leader.vm.network "forwarded_port", guest: 8080, host: 8080
    # HDFS console
    leader.vm.network "forwarded_port", guest: 50070, host: 50070
    # Accumulo console
    leader.vm.network "forwarded_port", guest: 50095, host: 50095
    # Graphite Web UI
    leader.vm.network "forwarded_port", guest: 8081, host: 8081
    # ElasticSearch HTTP endpoint
    leader.vm.network "forwarded_port", guest: 9200, host: 9200
    # Grafana
    leader.vm.network "forwarded_port", guest: 8090, host: 8090

    leader.vm.provider "virtualbox" do |v|
      v.memory = 3072
    end

    leader.vm.provision "ansible" do |ansible|
      ansible.playbook = "deployment/ansible/leader.yml"
      ansible.inventory_path = ANSIBLE_INVENTORY_PATH
      ansible.raw_arguments = ["--timeout=60"]
    end
  end

  (1..2).each do |follower_index|
    config.vm.define "follower0#{follower_index}" do |follower|
      follower.hostmanager.aliases = [ "datanode0#{follower_index}.service.geotrellis-spark.internal" ]

      follower.vm.hostname = "follower0#{follower_index}"
      follower.vm.network "private_network", ip: "33.33.33.#{follower_index + 1}0"

      follower.vm.synced_folder ".", "/vagrant", disabled: true

      follower.vm.provider "virtualbox" do |v|
        v.memory = 2048
        v.cpus = 2

        v.customize ["createhd", "--filename", ".vagrant/follower0#{follower_index}-disk01.vdi", "--size", 10000]
        v.customize ["storageattach", :id, "--storagectl", "SATAController", "--port", 3 + 1, "--device", 0,
          "--type", "hdd", "--medium", ".vagrant/follower0#{follower_index}-disk01.vdi"]
      end

      follower.vm.provision "ansible" do |ansible|
        ansible.playbook = "deployment/ansible/follower.yml"
        ansible.inventory_path = ANSIBLE_INVENTORY_PATH
        ansible.raw_arguments = ["--timeout=60"]
      end
    end
  end
end
