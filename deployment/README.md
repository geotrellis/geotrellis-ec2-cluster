# Amazon Web Services Deployment

Deployment is driven by [Packer](https://www.packer.io), [Troposphere](https://github.com/cloudtools/troposphere), and the [Amazon Web Services CLI](http://aws.amazon.com/cli/).

## Dependencies

The deployment process expects the following environment variables to be overridden:

```bash
$ export AWS_DEFAULT_PROFILE=geotrellis-spark-test
$ export AWS_DEFAULT_OUTPUT=text
$ export AWS_DEFAULT_REGION=us-east-1
$ export AWS_KEY_NAME=geotrellis-spark-test
$ export AWS_SNS_TOPIC=arn:aws:sns:us-east-1...
$ export GEOTRELLIS_SPARK_CLUSTER_NAME=Joker
```

Lastly, install the AWS CLI and Troposphere:

```bash
$ cd deployment
$ pip install -r requirements.txt
```

### Amazon Machine Images (AMIs)

In order to generate AMIs for the leader and followers, use the following `make` targets:

```bash
$ make leader-ami
$ make follower-ami
```

### CloudFormation (via Troposphere)

After at least one AMI of each type exists, use the following command to generate all of the CloudFormation templates:

```bash
$ make build
```

#### Launch the AWS Virtual Private Cloud (VPC)

Use the following command to create the VPC stack:

```
$ make vpc-stack
```

#### Create Route 53 Private Hosted Zones

Next, create the internal to the VPC private hosted zones:

```bash
$ make private-hosted-zones
```

### Launch the Mesos leader stack

After both AMIs are created, create the Mesos leader stack:

```
$ make leader-stack
```

### Launch the Mesos follower stack

After the leader stack is complete, create the Mesos follower stack:

```
$ make follower-stack
```
