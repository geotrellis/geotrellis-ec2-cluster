# geotrellis-ec2-cluster

This project attempts to aid in the process of setting up (locally, and on Amazon EC2) a GeoTrellis environment for leveraging its integration with Spark. 

The entire process will install and configure the following dependencies:

- Accumulo
- HDFS
- Marathon
- Mesos
- Spark
- Zookeeper

## Local Development

Vagrant 1.6+, Ansible 1.8+, and the `vagrant-hostmanager` Vagrant plug-in are used to setup the development environment for this project. It consists of the following virtual machines:

- `leader`
- `follower01`
- `follower02`

The `leader` virtual machine is overloaded with a Mesos and Accumulo leader, Marathon, Zookeeper, and an HDFS NameNode. The `follower*` virtual machines are Mesos followers, Accumulo tablet servers, as well as HDFS DataNodes.

Use the following command to bring up a local development environment:

```bash
$ vagrant up
```

**Note**: This step may prompt you for a password so that the `vagrant-hostmanager` plugin can add records to the virtual machine host's `/etc/hosts` file.

After provisioning is complete, you can view the Mesos web console by navigating to:

### Service UIs

Service                | Port  | URL
---------------------- | ----- | ------------------------------------------------
Mesos                  | 5050  | [http://localhost:5050](http://localhost:5050)
Marathon               | 8080  | [http://localhost:8080](http://localhost:8080)
HDFS                   | 50070 | [http://localhost:50070](http://localhost:50070)
Accumulo               | 50095 | [http://localhost:50095](http://localhost:50095)
Graphite               | 8081  | [http://localhost:8081](http://localhost:8081)
ElasticSearch          | 9200  | [http://localhost:9200](http://localhost:9200)
Grafana                | 8090  | [http://localhost:8090](http://localhost:8090)

### Caching

In order to speed up things up, you may want to consider using installing the [`vagrant-cachier`](https://github.com/fgrehm/vagrant-cachier) plugin:

```bash
$ vagrant plugin install vagrant-cachier
```

### Testing

Testing the Mesos/Spark integration consists of running a few tasks in the `spark-shell` from the Mesos leader.

First, login to the Mesos leader:

```bash
$ vagrant ssh leader
```

From there, launch the `spark-shell` and run the test program:

```bash
vagrant@leader:~$ spark-shell --master mesos://zk://zookeeper.service.geotrellis-spark.internal:2181/mesos
scala> val data = 1 to 10000
scala> val distData = sc.parallelize(data)
scala> distData.filter(_< 10).collect()
```

If all goes well, you should be able to see Spark distributing bits of the filter across the `follower*` virtual machines.

## Deployment

For more details around the Amazon Web Services deployment process, please see the deployment [README](deployment/README.md).
