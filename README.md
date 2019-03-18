# [AWS Certified SysOps Administrator - Associate](https://aws.amazon.com/certification/certified-sysops-admin-associate/)
These are my notes from the [acloudguru](https://acloud.guru) training on [udemy](https://www.udemy.com/aws-certified-sysops-administrator-associate/)

# Section 2: Monitoring and Reporting

**CloudWatch**: monitoring service for all your AWS resources and applications you run.

## EC2

EC2 default monitoring:
1. CPU
2. Network
3. Disk (I/O only; not capacity details)
4. Status Check (health of VM aka host)

Tip: RAM util is custom.  EC2 monitoring is 5min by default.  Can make 1min

Metrics are stored indefinitely by default.  Terminated EC2 or ELB instance metrics can still be retrieved!  You can retrieve your metrics with `GetMetricStatics` API or 3rd party tools from AWS partners

Defaults: depends on service, some are 1, 3 or 5.  Custom metrics minimum is 1 min.

**CloudWatch Alarms** can monitor any metric.  E.g.: CPU utilization on EC2, billing alert, etc.  They can then trigger an actions to be taken:
1. send SNS
2. run a lambda to smoke your infrastructure
3. whatever!

Tip: CloudWatch can be used to monitor on premise resources by installing the **SSM agent** can CloudWatch agent

## Monitor EC2 with Custom Metrics
Goal: have an EC2 instance send custom metrics to CloudWatch
1. Create an IAM role for EC2 to write to CW
2. Provision EC2 instance
  * use our role
  * use bootstrap script to install perl and perl scripts
3. Log in to EC2
  * don't forget to chmod 400 your pem  

These metrics are found in: `CloudWatch => Browser Metrics (button) => All Metrics (tab) => Custom`

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
  * infrequent access, large volume data; File Servers
  * balling on a budget


### GP2 (general purpose) - IOPS proportionally scales up with volume size.  IOPS range 3,000 - 9,999

#### Maths:
* have a base 3 IOPS per GB
* max volume 16.3 GB size
* 10k max IOPS, then you move into io1 tier
* can burst up to 3,000 IOPS by using *credits*

  * Have 1 GB drive, we get 3 IOPS - *Could burst to 3000 IOPS by using 2997 credits*
  * Have 100 GB drive, we get 300 IOPS - *Could burst to 3000 IOPS by using 2700 credits*
  * Have 500 GB drive, we get 1,500 IOPS - *Could burst to 3000 IOPS by using 1500 credits*

#### Credits:
* Each volume gets 5.4M
* This will sustain 30min of max (3k IOPS)
* Credits are earned when not going over provisioned level


[Prewarming (old) vs. Initializing EBS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-initialize.html)
* Kind of an old approach, because all EBS volumes operate at max the moment they are available.
* If we take a snapshot from S3, expect a performance hit, because blocks are not read.
* In production, we can read all the blocks on our volume before using it.  This is called **initialization**, and will prevent the performance hit.

## EBS CloudWatch Metrics
* **VolumeReadOps** - total number of reads for a period (good for calculating IOPS)
* **VolumeWriteOps** - total number of writes for a period (good for calculating IOPS)
* **VolumeQueueLength** - number of read and write operations waiting. (are the IOPS being maxed out?  Want value of zero)
* [Monitoring the Status of Your Volumes](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/monitoring-volume-status.html)
* volume status checks: 
  * OK - normal
  * Warning - degraded, severely degraded
  * Impaired - stalled, not available
* IOPS maths for CW: 1000 every 1 minute => 1000/60 IOPS

You can now modify (capacity, type, IOPS performance, etc) EBS volumes **on the fly**!!! No longer have to stop EC2 to make changes.  How do we do this:
1. issue modification command (console or command line)
2. Monitor the progress of request; wait for it to complete
3. If you increased the size, you have to tell the OS to extend the volume's file system


## Monitoring ELB
CloudWatch is auto turned on when you create an ELB.  No need to set IAM permissions or the like, it just happens

Types: 
1. Application: layer 7
2. Network: layer 4 transport (high throughput, TCP)
3. Classic (elastic)

#### Access logs:
* turned off by default
* stored in s3 bucket (compressed)
* details
  * timestamp
  * client IP
  * latencies
  * request path
  * server response
* Use Athena or 3rd party
* **Access logs store data where EC2 instances have been deleted**
  * E.g.: you have a fleet of auto scaling EC2 instances.  Days after the event, you want to go back and trouble shoot 500 errors.  The Access Logs should have a record of this in S3.

#### Request Tracing
* trace the request from client to it's target.
* load balancer adds or updates the `X-Amzn-Trace-Id` header before forwarding
* **Application** load balancer only

#### Four Ways to monitor:
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

#### CloudWatch vs. CloudTrail
* CW: performance
* CT: api calls within aws platform (Auditing E.g.: make new EC2, new user, etc)

## Monitoring ElastiCache
Caching popular DB queries via Memcached or Redis

[Monitoring Use with CloudWatch Metrics](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/CacheMetrics.html)

Types:
1. CPU utilization
  * Memcached: multi-threaded; if load exceeds 90% you have to add more nodes to your cluster
  * Redis: single-threaded; take 90 divided by number of cores
    * E.g.: `cache.m1.xlarge.node` has four cores.  The CPU utilization threshold would be 22.5% (90% / 4 cores)
2. Swap usage: the amount of the swap file used, duh
  * disk space reserved for when out of RAM
    * size of disk space should be the same as RAM size
  * Memcached: 
    * should be 0, no more than 50Mb
    * if over 50Mb, increase ['memcached_connections_overhead'](https://docs.aws.amazon.com/AmazonElastiCache/latest/mem-ug/ParameterGroups.ListingGroups.html)
    * Redis: has no SwapUsage metric, use `reserved-memory`
3. Evictions
  * Let's you know when new cache item is added and old one is booted
  * Memcached: 
    * scale up by increasing memory size 
    * scale out by adding nodes
  * Redis: can only scale **out** by adding read replicas
4. Concurrent connections
  * set alarm based on number of connections.  This would suggest a spike in traffic or application is not releasing connections like it should be.
  * **Exam Tip**: remember to set an alarm on the number of concurrent connections for elasticache.

[Monitoring Elasticache](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/CacheMetrics.html) by AWS

## CloudWatch Custom Dashboards
Create custom line, bar graphs, numbers, query, etc on all metrics

* Don't forget to hit **save** after your done creating... Ouch
* Dashboards show across **all** regions.
  * you will only see items (EC2, DynamoDB, etc) for the region you are in

## Creating a Billing Alarm
Go to `My Billing Dashboard` as root to turn on feature for AWS account

* send to you as email
* save to S3
* CloudWatch => Alarms => Billing

## AWS Organizations
Manage multiple AWS accounts by creating groups and applying policies to the groups

1. Centrally manage multiple AWS accounts.  Create groups of accounts, then attach policies to them.  E.g.: create a Developers group, and then individual teams with Dev group.
2. Control access to AWS services (E.g.: deny/allow access to Kinesis to HR)
    * these **Service Control Policies (SCP)** will trump IAM policies
3. Automate account creation and management.  Great for when adding new staff.  New hire gets all the permissions/policies of their group.
4. Consolidate billing across multiple accounts (helps for volume discounting)

* add other AWS accounts to the root organization AWS account
* create policy across all accounts
  * create a deny/allow Kenesis policy
  * enable the policy on the root account
  * apply the new policy to the organizations you want


## AWS Resource Groups & Tagging

#### Tags: 
* key value pairs attached to AWS resources
  * Name
  * Value
* Tags can be inherited.  E.g.: Autoscaling, CloudFormation, EBS

#### Resource Groups: collection of tags
* region
* name
* health check

#### Types of Resource groups:
1. Classic Resource Groups
    * Global; I want to see all `dev` tags
    * Appears to no longer be available
2. AWS System Manager
    * Execute automation commands based on match tag 
    * per region
    * think `running queries` for tags
    * once group is created, can use `Insights`
      * compliance
      * inventory
    * can run automation on the group
      * create an image
      * create snapshot


## EC2 Pricing Models
1. On demand: pay as you use, no commitment
2. Reserved: pay upfront to save long term (1 or 3 year)
    - Standard
    - Convertible: change attributes; same or better
    - Scheduled: at end of month get more instances
3. Spot: auction house
4. Dedicated host: not multi-tenant
    - can be on demand or reserved
    - good for server-bound software licenses

## AWS Config  
fully managed service that provides AWS resource inventory,config history, config change notification to enable security and governance

[AWS FAQ](https://aws.amazon.com/config/faq/)

Think auditing to appease **compliance** people.

* configuration snapshots and logs config changes of AWS resources
* automated compliance checking 
* per region only.  So if you want Global compliance, you would have to go into each regions =(
* you can create your own config rules, or use the AWS managed ones


#### Vocab:
* Config **item**: point-in-time attribute of a resource
  * My WebDmzSecGrp has port 22 open to the world
* Config **snapshot**: collection of config items
  * Every 1, 3, etc hours what are the states of my items
* Config **stream**: stream of changed config items
  * All of the changed items are reported to the stream
* Config **history**: collection of config items for a resource over time
  * I want to go back 2 weeks ago and see how a resource was configured
* Config **recorder**: records and stores config items

#### Setup:
* logs config for account by **individual region** (not global)
* stored in S3
* notify via SNS

**Stuff we see**: resource type, resource id, compliance, timeline (config details, relationships, changes, CloudTrail events)

#### Compliance checks:
* Triggered by: periodic or a configuration change
* Managed rules: about 40 rules to pick from 

#### Lab: (management tools)

For example, let's say we do not want resources which allow ssh.  There is an AWS managed Config Rule for this.  Create the rule and it will show you any resources (E.g.: EC2) which are non-compliant.  Config might state something like `you have a security group with ssh port 22 turned on and 4 EC2 instances with this security group`.  You can go in and change the security group.  The output from the Config audit is shown in a pretty timeline.  That way we can say `on Sept 22, 2018 all of our ssh was disabled`

How do we do this:
1. turn it on for region
2. determine which resources to monitor
3. choose bucket to dump to
4. opt: create SNS
5. assign IAM role (needs read only to the resource, write to S3, public to SNS)
6. pick rules (out of 30ish)
  * `restricted-ssh` for example

It shows a __timeline__ for when things are changed.  In our example, Config reported I have security groups that are not compliant with the 'restricted-ssh' rule.  I change the security groups to be compliant.  The history of the security group is tracked.


## Comparing Resources

| CloudWatch | CloudTrail | Config     |
|------------|------------|------------|
| monitor performance | monitor API calls | state of AWS env |
| CPU utilization| who provisioned security groups | rules of security groups 3 weeks ago |


## Dashboards
1. Service: [status of each AWS service by region](https://status.aws.amazon.com/)
2. Personal: alerts to my AWS experience.  If I had an EC2 in US-EAST-1 and that region was down.  I get a personal alert








# Section 3: Deployment & Provisioning
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











