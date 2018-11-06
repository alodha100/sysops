# [AWS Certified SysOps Administrator - Associate](https://aws.amazon.com/certification/certified-sysops-admin-associate/
)
*These are my notes*

# Cloudwatch
*monitoring service for all your AWS resources and applications you run.*

EC2 defaults:
1. CPU
2. Network
3. Disk (I/O, not capacity details)
4. Status Check (health of VM)
Tip: RAM util is custom.  EC2 monitoring is 5min by default.  Can make 1min

Metrics are stored indefinitely.  Terminated EC2 or ELB can still be retrieved.

Defaults: depends on service, some are 1, 3 or 5.  Custom metrics minimum is 1min.

Cloudwatch Alarms can monitor **any** metric.  They can then trigger an action to be taken:
1. send SNS
2. run a lambda to smoke your infrastructure
3. whatever!

Tip: Cloudwatch can be used to monitor on premise resources by installing the SSM agent can Cloudwatch agent

## Monitor EC2 with Custom Metrics
Goal: have an EC2 instance send custom metrics to Cloudwatch
1. Create an IAM role for EC2 to write to CW
2. Provision EC2 instance


*Scripts for Cloudwatch*
```
# verify this script works
/home/ec2-user/aws-scripts-mon/mon-put-instance-data.pl --mem-util --verify --verbose
# actually send data (one data point for each metric)
/home/ec2-user/aws-scripts-mon/mon-put-instance-data.pl --mem-util --mem-used --mem-avail
# send metrics every minute 
nanao /etc/crontab
*/1 * * * * root /home/ec2-user/aws-scripts-mon/mon-put-instance-data.pl --mem-util --mem-used --mem-avail
```
These metrics are found in:
Cloudwatch => Browser Metrics (button) => All Metrics (tab) => Custom


#>> chmod 400 ~/pems/SysopsKp.pem
#>> ssh ec2-user@54.210.165.248 -i ~/pems/SysopsKp.pem

Tip: from the online CW cosno
