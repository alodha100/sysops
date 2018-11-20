# [AWS Certified SysOps Administrator - Associate](https://aws.amazon.com/certification/certified-sysops-admin-associate/)
These are my notes

# Monitoring and Reporting

**CloudWatch**:
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

You can now modify (capacity, type) EBS volumes on the fly (no longer have to stop)  

## Monitoring ELB

Types: 
1. Application: layer 7
2. Network: layer 4 transport (high throughput, TCP)
3. Classic (elastic)

Ways to monitor:
1. CloudWatch (monitor performance)
  * when you spin up ELB, you default get CloudWatch.  No IAM required
2. Access logs
  * disabled by default, dumps to S3. 
  * think auditing like who, when, what (400, 500 errors) accessed ELB 
  * 5 or 60min intervals
  * even if EC2 is deleted (auto scaling), S3 data logs persist
  * Athena is good for parsing these massive logs
3. Request tracing
  * track HTTP requests from clients to target resources
  * updates the X-Amzn-Trace-Id header
  * Application LB only
4. CloudTrail (audit API calls)
  * any change to the LB environment (provision an LB, delete LB, update health checks, etc)
  * auditing (not metrics)

## Monitoring ElastiCache
*caching popular DB queries via Memcached or Redis*

[Monitoring Use with CloudWatch Metrics](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/CacheMetrics.html)

Types:
1. CPU utilization
  * Memcached: multi-threaded; if load exceeds 90% add more nodes to cluster
  * Redis: single-threaded; take 90 divided by number of cores
2. Swap usage 
  * disk space reserved for when out of RAM
  * Memcached: 
    * should be 0, no more than 50MB
    * if over 50MB, increase ['memcached_connections_overhead'](https://docs.aws.amazon.com/AmazonElastiCache/latest/mem-ug/ParameterGroups.ListingGroups.html)
    * Redis: has no SwapUsage metric, use 'reserved-memory'
3. Evictions
  * Let's you know when new is added, and old is booted
  * Memcached: scale up by increasing memory size or scale out by adding nodes
  * Redis: can only scale out by adding read replicas
4. Concurrent connections
  * set alarm based on number of connections.  This would suggest a spike in traffic or application is not releasing connections like it should be.

## CloudWatch Custom Dashboards
*Create custom line, bar graphs on all metrics*
* Don't forget to hit **save** after your done creating... Ouch
* Creating a dashboard will show in all regions

## Creating a Billing Alarm
*go to 'My Billing Dashboard' as root to turn on feature for AWS account*
* send to you as email
* save to S3
* CloudWatch => Alarms => Billing

## AWS Organizations
*manage multiple AWS account by creating groups and applying policies to the groups*

1. centrally manage policies about multiple accounts
2. control access to AWS services (E.g.: deny/allow access to Kinesis to HR)
3. Automate account creation and management
4. consolidate billing across multiple accounts (helps for volume discounting)

## AWS Resource Groups & Tagging

***Tags***: key value pairs attached to AWS resources
Tags can be inherited.  E.g.: Autoscaling, CloudFormation, EBS

***Resource Groups***: collection of tags
* region
* name
* health check
1. Classic Resource Groups
  * Global; I want to see all 'dev' tags
2. AWS System Manager
  * Execute automation commands based on match tag query



## EC2 Pricing Models

1. On demand: pay as you use, no commitment
2. Reserved: pay upfront to save long term
  - Standard
  - Convertible: change attributes; same or better
  - Scheduled: at end of month get more instances
3. Spot: auction house
4. Dedicated host: no multi-tenant
  - can be on demand or reserved
  - good for server-bound software licenses

## AWS Config  
*fully managed service that provides AWS resource inventory,config history, config change notification to enable security and governance*

[AWS FAQ](https://aws.amazon.com/config/faq/)

Think auditing to appease compliance people 

#### Vocab:
* Config **item**: point-in-time attribute of a resource
* Config **snapshot**: collection of config items
* Config **stream**: stream of changed config items
* Config **history**: collection of config items for a resource over time
* Config **recorder**: records and stores config items

#### Setup:
* logs config for account by individual *region*
* stored in S3
* notify via SNS

**Stuff we see**: resource type, resource id, compliance, timeline (config details, relationships, changes, CloudTrail events)

#### Compliance checks:
* Triggered by: periodic or a configuration change
* Managed rules: about 40 rules to pick from 

### Lab: (management tools)

1. turn it on for region
2. determine which resources to monitor
3. choose bucket to dump to
4. opt: create SNS
5. assign IAM role (needs read only to the resource, write to S3, public to SNS)
6. pick rules (out of 30ish)
  * 'restricted-ssh' for example

It shows a __timeline__ for when things are changed.  In our example, Config reported I have security groups that are not compliant with the 'restricted-ssh' rule.  I change the security groups to be compliant.  The history of the security group is tracked.


## Comparing Resources

| CloudWatch | CloudTrail | Config     |
|------------|------------|------------|
| monitor performance | monitor API calls | state of AWS env |
| CPU utilization| who provisioned security groups | rules of security groups 3 weeks ago |


## Dashboards
1. Service: status of each AWS service by region
2. Personal: alerts to my AWS experience.  If I had an EC2 in US-EAST-1 and that region was down.  I get a personal alert




# Deployment & Provisioning
Things I was iffy on for EC2:
* Placement group: spread or cluster, put instances in same AZ for less latency.  
* T2/T3 Unlimited: burst CPU (I think you use credits)

Let's fire up an Apache Website
```
yum update -y
yum install httpd -y
service httpd start
chkconfig httpd on 
echo "<html><body><center><h1>Hello Apache</h1></center></body></html>" > /var/www/html/index.html
```

### Troubleshooting: 
**InstanceLimitExceed** error: too many instances in that region (20 default).  
Solve: You need to request more.

**InsufficientInstanceCapacity** error: AWS is out of that hardware instance type.  
Solve: Wait for more; request less instances; try different instance type; request in different AZ.

## EBS IOPS
* io1 goes 10k up to 32k IOPS
* NoSQL or relational DB with latency sensitive workloads

what happens if you max your IOPS on a gp2?
* I/O requests start queueing
* you get thrashed

solutions:
* increase your volume size, because volume size and IOPS are directly proportional up to 3,333GB.  3 IOPS per GB
* upgrade storage class from gp2 to io1

## Bastion Host 
Host located in your public subnet with a route to the internet via gateway.  Use this subnet to jump to your private subnet via ssh or rdp.  Make sure to lock down your bastion host (restrict IP and ports)

## ELB
You can pre-warm your ELBs by contacting AWS if you expect a massive surge in traffic to ensure your ELB can handle the traffic.

IP address: Application LB have changing IP addresses as they are brought into service.  Network LB get **static IP** address (one per subnet).  This makes firewall rules are a breeze.  You can put a ALB behind a NLB to get the best of both worlds.  Exam tip: if it needs static, you need need Network LB.

### ELB Error Messages:
* **4xx** client side error; think 404 for bad URL (client mistake)

  * **400**: bad request (bad header)  
  * **401**: unauthorized - user access denied
  * **403**: forbidden - request block by firewall ACL
  * **460**: client closed connection - LB didn't have time to respond and client timed out the server
  * **463**: LB received an X-Forward-For request header that was rubbish

* **5xx** server side error; think 500 the 5 is an "S" for server side

  * **500** internal server error (LB s the bed)
  * **502** bad gateway: app server closed connection or bad response
  * **503** Unavailable - no registered target
  * **504** Gateway timeout - application is not responding
  * **561** Unauthorized - check IAM


### CloudWatch for ELB

* CW can monitor the ELB and its backend instance
* Default for ELB is 60sec

1. Overall Health:
  * **BackendConnectionErrors**: number of unsuccessful connections to the backend instance
  * **HealthHostCount**: count of healthy instances registered
  * **UnHealthyCount**
  * **HTTPCode_Backend_2XX-5XX**: all of our HTTP return codes
  
  2. Performance
  * **Latency**
  * **RequestCount**: number of completed requests / connections
  * **SurgeQueueLength**: classic LB; number of pending requests (size 1024)
  * **SpilloverCount**: classic LB; if queue is full, this is count of dropped

## Lab: ELB & CW
1. Provision EC2 with Apache webpage
2. Create Application LB
  * put into same Security Group as EC2 (ssh,http)
  * create new target group
  * point/register targets to point to our newly created target group
3. Use the DNS of the LB and access EC2
4. Check the CloudWatch metrics to see the detail

# Systems Manager (SSM)
*management tool which gives you visibility and control over AWS infrastructure.*

Works with CloudWatch and includes **Run Command**, which automates operational tasks (security, package installs, etc)

Allows you to organize your inventory by grouping resources (by application, environment, team, etc).  Can also manage on premise.

### Run Command

1. make IAM for Run Command: "AmazonEC2RoleforSSM"
2. Assign role to EC2 and maybe add a tag to help us find it
3. Go to AWS System Manager
  * Find resource(s)
  * Save the query as a group

Think of Run Command as a portal to show info about your groups.  The portal leads to:
* Config: audit resource setup
* CloudTrail
* Personal Health: operational notices about the regions I have resources
* Trusted Advisor: requires non-free account =(


stopped at 8:15











