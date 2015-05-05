# Amazon Web Services Deployment

Deployment is driven by [Packer](https://www.packer.io), [Troposphere](https://github.com/cloudtools/troposphere), the [AWS Command Line Interface](http://aws.amazon.com/cli/) and [Boto](http://aws.amazon.com/cli/), the AWS SDK for Python.

Deployment requires some set-up in your Amazon account, editing a config file, creating AMIs, and launching a stack. This README describes this process.

## Install Dependencies

There are two options for dealing with dependencies to manage the stack:
  1. Manually install dependencies on your workstation
  2. Use the `mesos-leader` VM to run the stack management commands

To install manually use the following steps:
 - Install Troposphere, Boto, and other Python dependencies:

```bash
$ cd deployment
$ pip install -r requirements.txt
```

 - Install [Packer]()

## Create IAM Roles (optional)

Two IAM roles are required for the stack. These IAM roles are assigned to the `mesos-leader` and `mesos-follower` instances and grant access to S3. Assuming your data to be ingested is on S3, the profiles would include access to S3.

Example `MesosLeaderInstanceProfile` and `MesosFollowerInstanceProfile`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:*",
      "Resource": "*"
    }
  ]
}
```

If your data does not reside on S3 or needs access to other AWS resources your policy may need to be modified. If a profile is not provided in the `geotrellis-cluster.config` then your instances will not be launched with IAM profiles attached to them.


## Create/Download EC2 KeyPair

The EC2 KeyPair is used to authenticate SSH connections to the instances from a local machine. Creating this Key is necessary to launch an instance; however, if you already have a Key you can simply re-use that. Note, keys are tied to regions so if you want to launch a stack in a different region, you need to create a key for that region.

## Configure AWS Profile using the AWS CLI

Using the AWS CLI, create an AWS profile.

```bash
$ aws configure
```

You will be prompted to enter your AWS access keys,  AWS access key IDs, and default region. These credentials will be used to authenticate calls to the API when using Boto, Packer, and the AWS CLI.

## Edit Configuration File

A configuration file is required to launch the stack. An example file is available in this directory at `geotrellis-cluster.cfg.example`.

```
[CONFIG NAME]
IPAccess: '<IP to allow SSH Access> (e.g. 216.158.51.82/32)'
KeyName: '<EC2 Key to authenticate with SSH>'
MesosFollowerAMI: '<AMI ID of Mesos Follower (optional -- will be found automatically if not provided)>'
MesosFollowerInstanceProfile: '<ARN of Mesos Follow Instance Profile (optional -- may not be necessary)>'
MesosFollowerInstanceType: '<Mesos Follow Instance Type>'
MesosFollowerSpotPrice: '<Spot Price to use Mesos Follower Instances> (optional)>'
MesosLeaderAMI: '<AMI ID of Mesos Leader (optional -- will be found automatically if not provided)>'
MesosLeaderInstanceProfile: '<ARN of Mesos Leader Instance Profile (optional -- may not be necessary)>'
MesosLeaderInstanceType: '<Mesos Leader Instance Type>'
Region: '<AWS Region to Launch Stack>'
StackType: '<Type of Stack to launch (e.g. accumulo)>'
NameSpace: '<String that identifies user of stack (used to differentiate multiple stacks within a single account)>'
```

Multiple configs can be present in the same file, but must be delineated by separate sections using different section headers (`[SECTION]`).

## Launching and Managing Stacks

Creating AMIs and launching stacks is managed with  `gt-stack.py` CLI. This command provides an interface for automatically generating AMIs and launching GeoTrellis Cluster stacks.

### Generate AMIs

Before launching your GeoTrellis Cluster stack you will need to generate AMIs. The `create-ami` subcommand in `gt-stack.py` can be used for generating AMIs. To view options at the tommand line you can use `./gt-stack.py create-ami --help`.

If using defaults for generating AMIs (e.g. you haven't moved your `geotrellis-cluster.config` file and want to youse the `default` AWS profile in `~/.aws/credentials`) you only need to provide the `machine_type` positional argument. There are two types of machines -- `mesos-leader` and `mesos-follower`. For instance, to generate a new `mesos-leader` AMI:

```bash
$ ./gt-stack.py create-ami mesos-leader
```

To create a `mesos-follower` AMI:
```bash
$ ./gt-stack.py create-ami mesos-follower
```

This two commands will create AMIs based on parameters set in the configured `geotrellis-cluster.config`.

### Launch Stack

After having successfully created AMIs, you can now launch a GeoTrellis cluster stack with the `launch-stacks` subcommand in `./gt-stack.py`. To view all options and parameters to the `launch-stacks` command you can use the help option at the command line `./gt-stack.py launch-stacks --help`.

Using the parameters set in your `geotrellis-cluster.config` and provided defaults you can launch a full stack with the command:

```bash
$ ./gt-stack.py launch-stacks
```

This command will create a VPC, create a private hosted zone in the VPC, launch a mesos-leader instance, and then finally launch a set of mesos follower instances. The command is idempotent, so running it again after launching a stack will not create any more resources. This also means that if you wish to leave the VPC up, but want to launch a new set of mesos followers and/or mesos leader you can delete the stack via the AWS CloudFormation console and re-run the command which will use the previously created private hosted zone and VPC.
