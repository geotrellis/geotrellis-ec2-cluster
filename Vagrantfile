# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.require_version ">= 1.5"

if ["up", "provision", "status"].include?(ARGV.first)
  require_relative "vagrant/ansible_galaxy_helper"

  AnsibleGalaxyHelper.install_dependent_roles("deployment/ansible")
end

GEOTRELLIS_EC2_CLUSTER_TYPE = ENV.fetch("GEOTRELLIS_EC2_CLUSTER_TYPE", "accumulo")
ANSIBLE_GROUPS = {
  "leaders" => ["leader"],
  "followers" => (1..2).collect { |index| "follower0#{index}" },
  "development:children" => ["leaders", "followers"]
}

case GEOTRELLIS_EC2_CLUSTER_TYPE
when "accumulo"
  ANSIBLE_GROUPS_BY_TYPE = {"accumulo:children" => ["development"]}

  LEADER_HOSTMANAGER_ALIASES = [
    "namenode.service.geotrellis-spark.internal",
    "accumulo-leader.service.geotrellis-spark.internal",
  ]
  LEADER_PORT_FORWARDS = [
    # HDFS console
    50070,
    # Accumulo console
    50095
  ]

  FOLLOWER_HOSTMANAGER_ALIASES = [
    "datanode0{{index}}.service.geotrellis-spark.internal"
  ]
  FOLLOWER_PORT_FORWARDS = []
when "cassandra"
  ANSIBLE_GROUPS_BY_TYPE = {"cassandra:children" => ["development"]}
end

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/trusty64"

  if Vagrant.has_plugin?("vagrant-hostmanager")
    config.hostmanager.enabled = true
    config.hostmanager.manage_host = true
  else
    $stderr.puts "\nERROR: Please install the vagrant-hostmanager plugin."
    exit(1)
  end

  if Vagrant.has_plugin?("vagrant-cachier")
    config.cache.scope = :box
  end

  config.vm.define "leader" do |leader|
    leader.hostmanager.aliases = [
      "zookeeper.service.geotrellis-spark.internal",
      "mesos-leader.service.geotrellis-spark.internal",
      "monitoring.service.geotrellis-spark.internal"
    ] + LEADER_HOSTMANAGER_ALIASES

    leader.vm.hostname = "leader"
    leader.vm.network "private_network", ip: "33.33.33.10"

    # Spark console
    leader.vm.network "forwarded_port", guest: 4040, host: 4040
    # Mesos console
    leader.vm.network "forwarded_port", guest: 5050, host: 5050
    # Marathon console
    leader.vm.network "forwarded_port", guest: 8080, host: 8080
    # Graphite Web UI
    leader.vm.network "forwarded_port", guest: 8081, host: 8081
    # ElasticSearch HTTP endpoint
    leader.vm.network "forwarded_port", guest: 9200, host: 9200
    # Grafana
    leader.vm.network "forwarded_port", guest: 8090, host: 8090

    LEADER_PORT_FORWARDS.each do |port|
      leader.vm.network "forwarded_port", guest: port, host: port
    end

    leader.vm.provider "virtualbox" do |v|
      v.memory = 3072
    end

    leader.vm.provision "ansible" do |ansible|
      ansible.playbook = "deployment/ansible/#{GEOTRELLIS_EC2_CLUSTER_TYPE}-leader.yml"
      ansible.groups = ANSIBLE_GROUPS.merge(ANSIBLE_GROUPS_BY_TYPE)
      ansible.raw_arguments = ["--timeout=60"]
    end
  end

  (1..2).each do |follower_index|
    config.vm.define "follower0#{follower_index}" do |follower|
      follower.hostmanager.aliases = FOLLOWER_HOSTMANAGER_ALIASES.collect { |name|
        name.gsub(/\{\{index\}\}/, follower_index.to_s)
      }

      follower.vm.hostname = "follower0#{follower_index}"
      follower.vm.network "private_network", ip: "33.33.33.#{follower_index + 1}0"

      FOLLOWER_PORT_FORWARDS.each do |port|
        follower.vm.network "forwarded_port", guest: port, host: port
      end

      follower.vm.synced_folder ".", "/vagrant", disabled: true

      follower.vm.provider "virtualbox" do |v|
        v.memory = 2048
        v.cpus = 2

        v.customize ["createhd", "--filename", ".vagrant/follower0#{follower_index}-disk01.vdi", "--size", 10000]
        v.customize ["storageattach", :id, "--storagectl", "SATAController", "--port", 3 + 1, "--device", 0,
          "--type", "hdd", "--medium", ".vagrant/follower0#{follower_index}-disk01.vdi"]
      end

      follower.vm.provision "ansible" do |ansible|
        ansible.playbook = "deployment/ansible/#{GEOTRELLIS_EC2_CLUSTER_TYPE}-follower.yml"
        ansible.groups = ANSIBLE_GROUPS.merge(ANSIBLE_GROUPS_BY_TYPE)
        ansible.raw_arguments = ["--timeout=60"]
      end
    end
  end
end
