<<<<<<< HEAD
# [AWS Certified SysOps Administrator - Associate](https://aws.amazon.com/certification/certified-sysops-admin-associate/)
=======
# [AWS Certified SysOps Administrator - Associate](https://aws.amazon.com/certification/certified-sysops-admin-associate)
>>>>>>> 1caa3b4824ea4b772e93e642a16a835d745a61d9
*These are my notes*

# CloudWatch
*monitoring service for all your AWS resources and applications you run.*

## EC2

EC2 default monitoring:
1. CPU
2. Network
3. Disk (I/O, not capacity details)
4. Status Check (health of VM)
Tip: RAM util is custom.  EC2 monitoring is 5min by default.  Can make 1min

Metrics are stored indefinitely.  Terminated EC2 or ELB can still be retrieved.

Defaults: depends on service, some are 1, 3 or 5.  Custom metrics minimum is 1min.

CloudWatch Alarms can monitor **any** metric.  They can then trigger an action to be taken:
1. send SNS
2. run a lambda to smoke your infrastructure
3. whatever!

Tip: CloudWatch can be used to monitor on premise resources by installing the SSM agent can CloudWatch agent

## Monitor EC2 with Custom Metrics
Goal: have an EC2 instance send custom metrics to CloudWatch
1. Create an IAM role for EC2 to write to CW
2. Provision EC2 instance
  * use our role
  * use bootstrap script to install perl and perl scripts
3. Log in to EC2
  * don't forget to chmod 400 your pem  


*Scripts for CloudWatch*
```
# verify this script works
/home/ec2-user/aws-scripts-mon/mon-put-instance-data.pl --mem-util --verify --verbose
# actually send data (one data point for each metric)
/home/ec2-user/aws-scripts-mon/mon-put-instance-data.pl --mem-util --mem-used --mem-avail
# send metrics every minute 
nano /etc/crontab
*/1 * * * * root /home/ec2-user/aws-scripts-mon/mon-put-instance-data.pl --mem-util --mem-used --mem-avail
```
These metrics are found in:
CloudWatch => Browser Metrics (button) => All Metrics (tab) => Custom


Copy/Paste helper:
```
#>> chmod 400 ~/pems/SysopsKp.pem
#>> ssh ec2-user@54.210.165.248 -i ~/pems/SysopsKp.pem
```

## Monitoring EBS
EBS types:
1. General Purpose (SSD) - **gp2**
  * most workloads
  * system boot volumes
  * dev and test env
  * virtual desktops
2. Provisioned IOPS (SSD) - **io1**
  * critical business apps the require over 10k IOPS
  * large DBs: MongoDB, Cassandra, Microsoft SQL, etc
3. Throughput Optimized (HDD non-bootable) - **st1**
  * streaming workloads for cheap
  * Big Data warehouse
4. Cold (HDD non-bootable) - **sc1**
  * infrequent access, large volume data
  * balling on a budget


GP2 (general purpose) Maths:
* IOPS proportionally scales up with volume size
* have a base 3 IOPS per GB
* max volume 16.3 GB size
* 10k max IOPS
* can burst up to 3,000 IOPS - *Can use credits*

Have 1 GB drive, we get 3 IOPS - *Could burst to 3000 IOPS by using 2997 credits*
Have 100 GB drive, we get 300 IOPS - *Could burst to 3000 IOPS by using 2700 credits*
Have 500 GB drive, we get 1,500 IOPS - *Could burst to 3000 IOPS by using 1500 credits*

Credits:
* Each volume gets 5.4M
* This will sustain 30min of max (3k IOPS)
* Credits are earned when not going over provisioned level


[Prewarming (old) vs. Initializing EBS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-initialize.html)
* Kind of an old approach, because all EBS volumes operate at max the moment they are available.
* If we take a snapshot from S3, expect a performance hit, because blocks are not read.
* In production, we can read all the blocks on our volume before using it.  This is called **initialization**, and will prevent the performance hit.

### EBS CloudWatch Metrics
* **VolumeReadOps** - total number of reads for a period
* **VolumeWriteOps** - total number of writes for a period
* **VolumeQueueLength** - number of read and write operations waiting
* [Monitoring the Status of Your Volumes](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/monitoring-volume-status.html)
* volume status checks: 
  * OK - normal
  * Warning - degraded, severely degraded
  * Impaired - stalled, not available

You can now modify EBS volumes on the fly (no longer have to stop)  











