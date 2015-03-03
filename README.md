# vagrant-geotrellis-mesos-spark

This is a Vagrant project that attempts to produce a local development environment for [GeoTrellis](http://geotrellis.io), on top of [Apache Spark](https://spark.apache.org), on top of [Apache Mesos](http://mesos.apache.org).

## Local Development

A combination of Vagrant 1.5+, Ansible 1.6+, and the `vagrant-hostmanager` Vagrant plug-in is used to setup the development environment for this project. It consists of the following virtual machines:

- `leader`
- `follower01`
- `follower02`

The `leader` virtual machine is overloaded with a Mesos leader, Marathon, Zookeeper, and an HDFS NameNode. The `follower*` virtual machines are Mesos followers, as well as HDFS DataNodes.

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

In order to speed up things up, you may want to consider using a local caching proxy. The `VAGRANT_PROXYCONF_ENDPOINT` environmental variable provides a way to supply a caching proxy endpoint for the virtual machines to use:

```bash
$ VAGRANT_PROXYCONF_ENDPOINT="http://192.168.96.10:8123/" vagrant up
```

Alternatively, you can also install the [`vagrant-cachier`](https://github.com/fgrehm/vagrant-cachier) plugin.

### Testing

Testing the Mesos/Spark integration consists of running a few tasks in the `spark-shell` from the Mesos leader.

First, login to the Mesos leader:

```bash
$ vagrant ssh leader
```

From there, set the following environmental variables:

```bash
vagrant@leader:~$ export MESOS_NATIVE_LIBRARY=/usr/local/lib/libmesos.so
vagrant@leader:~$ export MASTER=mesos://zk://zookeeper.service.geotrellis-spark.internal:2181/mesos
vagrant@leader:~$ export SPARK_EXECUTOR_URI="http://d3kbcqa49mib13.cloudfront.net/spark-1.2.1-bin-cdh4.tgz"
```

Next, download and extract the Spark 1.2.1 distribution for CDH4 locally:

```bash
vagrant@leader:~$ wget $SPARK_EXECUTOR_URI
vagrant@leader:~$ tar xzf spark-1.2.1-bin-cdh4.tgz
```

From here we can launch the `spark-shell` and run the test program:

```bash
vagrant@leader:~$ ./spark-1.2.1-bin-cdh4/bin/spark-shell
scala> val data = 1 to 10000
scala> val distData = sc.parallelize(data)
scala> distData.filter(_< 10).collect()
```

If all goes well, you should be able to see Spark distributing bits of the filter across the `follower*` virtual machines.
