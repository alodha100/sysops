# [AWS Certified SysOps Administrator - Associate](https://aws.amazon.com/certification/certified-sysops-admin-associate/)
These are my notes from the [acloudguru](https://acloud.guru) training on [udemy](https://www.udemy.com/aws-certified-sysops-administrator-associate/)

# Section 2: Monitoring and Reporting

## CloudWatch: monitoring service for all your AWS resources and applications you run.

### EC2
EC2 default monitoring:
1. CPU
2. Network
3. Disk (I/O only; not capacity details)
4. Status Check (health of VM aka host)

Tip: RAM util is custom.  EC2 monitoring is 5min by default.  Can make 1min

Metrics are stored indefinitely by default.  Terminated EC2 or ELB instance metrics can still be retrieved!  You can retrieve your metrics with `GetMetricStatics` API or 3rd party tools from AWS partners

Defaults: depends on service, some are 1, 3 or 5.  Custom metrics minimum is 1 min.

#### CloudWatch Alarms
can monitor any metric.  E.g.: CPU utilization on EC2, billing alert, etc.  They can then trigger an actions to be taken:
1. send SNS
2. run a lambda to smoke your infrastructure
3. whatever!

Tip: CloudWatch can be used to monitor on premise resources by installing the **SSM agent** can CloudWatch agent

#### Monitor EC2 with Custom Metrics
Goal: have an EC2 instance send custom metrics to CloudWatch
1. Create an IAM role for EC2 to write to CW
2. Provision EC2 instance
  * use our role
  * use bootstrap script to install perl and perl scripts
3. Log in to EC2
  * don't forget to `chmod 400` your pem  

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
* IOPS maths for CW: 1000 every 1 minute => 1000/60 IOPS => 16.3 IOPS

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

#### Four Ways to monitor ELB:
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
fully managed service that provides AWS resource inventory, config history, config change notification to enable security and governance

[AWS FAQ](https://aws.amazon.com/config/faq/)

Think auditing to appease **compliance** people.

* configuration snapshots and logs config changes of AWS resources
* automated compliance checking 
* per region only.  So if you want Global compliance, you would have to go into each regions =(
* you can create your own config rules, or use the AWS managed ones
* what triggers AWS Config:
  * periodically: run every 2 weeks
  * configuration changes: somebody opened port 80 on EC2


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

| CloudWatch | CloudTrail | Config     | Access Logs|
|------------|------------|------------|------------|
| monitor performance | monitor API calls | state of AWS env | turn on for EC2 |
| CPU utilization| who provisioned security groups | rules of security groups 3 weeks ago | fleet of EC2 autoscaling, recover 500 errors days after instance termination |


## Dashboards
1. Service: [status of each AWS service by region](https://status.aws.amazon.com/)
2. Personal: alerts to my AWS experience.  If I had an EC2 in US-EAST-1 and that region was down.  I get a personal alert



# Section 3: Deployment & Provisioning
Things I was iffy on for EC2:
* Placement group: put all instances in same AZ for less latency.  
  * Spread: same AZ. same hardware
  * Cluster: same AZ, different hardware
  * Try to make all EC2 istances the same type
* T2/T3 Unlimited: burstable CPU performance.  Have to keep average CPU utilization within bounds  ~~I think you use credits~~

Let's fire up an Apache Website
```
#!/bin/bash
yum update -y
yum install httpd -y
service httpd start
chkconfig httpd on 
echo "<html><body><center><h1>Hello Apache</h1></center></body></html>" > /var/www/html/index.html
```

## Troubleshooting: 
Why didn't my EC2 launch???

1. **InstanceLimitExceed** error: too many instances in that region (20 default).  
Solve: You need to request more.
2. **InsufficientInstanceCapacity** error: AWS is out of that hardware instance type.  
Solve: Wait for more; request less instances; try different instance type; request in different AZ.

## EBS IOPS
* gp2 (general purpose) 3 IOPS/GB; up to 16,000 IOPS
* io1 (provisioned IOPS) 50 IOPS/GB; up to 64,000 IOPS
  * NoSQL or relational DB with latency sensitive workloads

#### What happens if you max your IOPS?
* on gp2
  * I/O requests start queueing
  * your disk will start to thrash
* gp2 fixes
  * increase disk size (size and IOPS are directly proportional), but capped at 5.2TB
  * increase EBS class to io1


## Bastion Host 
Host located in your public subnet with a route to the internet via gateway.  Use this subnet to jump to your private subnet via ssh or rdp.  Make sure to lock down your bastion host (restrict IP and ports)

## ELB - Elastic Load Balancer
Equal distribution of work load across resources

1. Application LB - layer 7; inspect packets of HTTP header
2. Network LB - layer 4; transport layer, TCP, super fast, super $$$; static IP
3. Class LB - layer 4 & 7; but features for layer 7 are weak sauce `X-Forwarded` and `sticky sessions`

You can `pre-warm` your ELBs by contacting AWS if you expect a massive surge in traffic to ensure your ELB can handle the traffic.  You have to contact AWS support to do this.

**IP address**: Application LB have changing IP addresses as they are brought into service.  Network LB get **static IP** address (one per subnet).  This makes firewall rules are a breeze.  You can put a ALB behind a NLB to get the best of both worlds.  
**Exam tip**: if it needs static IP, you should use Network LB.

### ELB Error Messages:
* **4xx** client side error; think 404 for bad URL (client mistake)

  * **400**: bad request (bad header)  
  * **401**: unauthorized - user access denied
  * **403**: forbidden - request block by firewall ACL
  * **460**: client closed connection - LB didn't have time to respond and client timed out the server
  * **463**: LB received an `X-Forward-For` request header that was more than 30 IP addresses

* **5xx** server side error; think 500 the 5 is an "S" for server side

  * **500** internal server error (LB s the bed)
  * **502** bad gateway: app server closed connection or bad response
  * **503** Unavailable - no registered target
  * **504** Gateway timeout - application is not responding
  * **561** Unauthorized - ID provider error when trying to authenticate the user


## CloudWatch for ELB
By default, your ELB will report to CloudWatch

* CW can monitor the ELB and its backend instance
* Default for ELB is 60sec

1. Overall Health:
    * **BackendConnectionErrors**: number of unsuccessful connections to the backend instance
    * **HealthHostCount**: count of healthy instances registered
    * **UnHealthyCount**
    * **HTTPCode_Backend_2XX-5XX**: all of our HTTP return codes
  
2. Performance:
    * **RequestCount**: number of completed requests / connections
    * **SurgeQueueLength**: classic LB; number of pending requests (queue size max 1024)
    * **SpilloverCount**: classic LB; if queue is full, this is count of dropped

## Lab: ELB & CW
1. Provision EC2 with Apache webpage
    * make sure ssh & http are enabled in security group
2. Create Application LB
    * put into same Security Group as EC2 (ssh,http)
    * create new target group
    * point/register targets to point to our newly created target group
3. Use the DNS of the LB and access EC2 (will be an A record)
4. Check the CloudWatch metrics to see the detail

## AWS Systems Manager (SSM)

* Management tool which gives you visibility and control over AWS infrastructure (including on-prem)
* Works with CloudWatch and includes **Run Command**, which automates operational tasks (security, package installs, etc)
* Allows you to organize your inventory by grouping resources (by application, environment, team, etc).  Can also manage on premise.

How to:
1. make IAM role for Run Command with the policy `AmazonEC2RoleforSSM`
2. Assign role to EC2 and maybe add a tag to help us find it
3. Go to AWS System Manager (think of this as a portal to other AWS services)
  * Find resource(s) by running a query (can use tags to search with)
  * Save the query as a group

### Insights
1. Config: audit resource setup
2. CloudTrail
3. Personal Health: operational notices about the regions I have resources
4. Trusted Advisor: makes suggestions for compliance such as S3 permissions, EC2 access, security group open ports, etc
    * cost optimize (not free account)
    * performance (not free account)
    * security
    * fault tolerance (not free account)
    * service limits (too many EC2 instances)
5. Inventory  
6. Compliance

### Actions
1. Automation: use pre-define AWS managed commnands E.g.: Copy Snapshot, Attach EBS, Stop instance
2. Run command: do stuff to EC2 instances E.g.: Ansible playbook, configure Docker, make your own script, `AWS-RunShellScript`
3. Patch Manager
4. Maintenance Windows: run jobs every X minutes, hours, days, etc
5. State Manager: make sure instances are all in same state.  If someone changes instance state, this will change is back.

### Shared Resources
1. List of all instances
2. Activation: manage AWS and on prem systems 
3. Documents: all the commands we can run with Run Command
4. Parameter Store: store secrets, DB strings, etc.  They can be encrypted



# Section 4: High Availability

## Elasticity & Scalability 101

* **Elasticity**: env can stretch back and forth based on need (short term). Pay for what you need.  
* **Scalability**: building out the infrastructure for long term demands.

### EC2
* **Elasticity**: increase the number of instances; use autoscaling
* **Scalability**: increase Instance size, use reserve instances

### DynamoDB
* **Elasticity**: increase IOPS for traffic spikes, decrease after
* **Scalability**: infinite size of storage

### RDS
* **Elasticity**: not very elastic (mySQL, etc)
* **Scalability**: increase size; small => medium (downtime)

### Aurora
* **Elasticity**:  solves RDS non scale limitation!  Use Aurora serverless.
* **Scalability**: increase size; small => medium (no downtime!)


## RDS: Multi-AZ Failover
Keeps a copy of your Prod DB in a different AZ in case of failure or disaster.  Feature must be turned on for your DB.  AWS manages the syncing to the backup DB.  If a failure occurs, AWS will update the DNS records.  Your connection strings do not change.  Endpoint remains the same.  E.g.: 

`[myname].[randomstring].[region].rds.amazonaws.com`
`benwright.lkq09fsm3l12.us-east-1.rds.amazonaws.com`

This is for DR (disaster recovery), not performance.
* Highly available
* backups are taken from secondary, no performance hit to I/O on primary
* restores are taken from secondary, no performance hit to I/O on primary
* can force a failover by rebooting primary

## RDS: Using Read Replicas
Read only copy of your DB for read heavy workloads
* performance
* can have multiple RR; even chain them (expect latency)
* if your primary needs to be taken down (maintenance) send all traffic to RR
* data warehousing against RR so primary doesn't take a read hit

Creating:
* AWS will take a snapshot of primary
  * if not multi-AZ, expect a ~1 min I/O suspension
  * if multi-AZ, snapshot of backup is taken, performance hit
* You get a new endpoint for the RR (can point traffic directly to it)  

Exam tips:
1. You can promote a RR to primary, but this will break the RR 
2. MySQL, PostgreSQL, MariaDB can have up to 5 RR's
3. RR's can be in different regions
4. Replication is always async
5. cannot snapshot or auto backup RR.  Have to do those on primary
6. look out for the `REPLICA LAG` monitorable item
7. __Know the difference between RR & Multi-AZ__

## RDS: Lab

Cools things we can do after spinning up a [mySQL] DB
1. make it multi-az (little performance hit when you change this)
2. change to io1 (high IOPS)
3. change disk size
4. create a read replica (after BACKUPS are turned ON)
    * turning on backups will reboot the primary
    * nice to put a DB instance ID on the RR to reference it later
    * can promote the RR (this breaks the replication chain)
    * can chain another RR to the RR (after turning on backups for RR)
    * force a failover (reboot the primary)
5. find the RDS version `aws rds describe-db-instances --region us-east-1`

## Elasticache
Cache most frequent DB searches or recommend engine.  Good choice if your DB is read heavy of same queries.
#### Memcached
Object caching.  Simple.  __No Multi-AZ__
#### Redis 
Key value pairs that supports data structures like sets and lists.  Supports Master / Slave replication and Multi-AZ

## Aurora
Amazon's RDS.  MySQL & PostgreSQL compatible. Stores 6 copies of data across 3 AZ's! It would take a loss to 2 copies to affect write & 3 concurrent failures to affect read availabilty
* min 10GB up to 64TB autoscaling
* self healing; data blocks are continuously being scanned
* you only write to a single primary instance.  That will replicate for you
* if 100% CPU on Aurora; need to determine if it's read or writes that is maxing you out
  * if __writes__, you need a bigger single instance to write to (scale up)
  * if __reads__, you need more read replicas (scale out).  Can go up to 15
* Aurora servlerless: on demand; autoscaling.  Can migrate between server/serverless as needed.
* encryption by default; this will force all RR to also be encrypted 
* backtrack: easy to restore DB to time point up to 72 hours ago
* you can create a RR if a different region
  * this will create an entire new cluster however

## Auto Scaling Trouble Shooting
Instances are not launching into an autoscaling group
* associated k/p does not exist
* security group does not exist
* instance type may not be available in that region

# Section 5: Storage & Data Management
## S3
secure, durable, and highly scalable storage for __objects__
* size: 0B - 5TB
* unlimited storage capacity

Atonomy:
* key/value, version, metadata, subresources (ACLs), CORS

Data consistency:
  * PUTS: read after write
  * UPDATE & DELETE: eventual

Default
* 99.99% availability (99.9% guaranteed)
* 99.99999 99999 9% (11) durable

S3-IA (infrequent access)
  * retrieval fee

S3-IA One Zone
  * 20% cost savings
  * 99.5% available

Reduced Redundancy
  * 99.99% durable 
  * 99.99% available
  * phasing out

Glacier:
  * 3-5 hours to retrieval

Intelligent Tiering (new) - objects move between frequent & infrequent

## S3 review
* Versioning: when versioning is turned on; you do not delete files.  Instead, a delete marker is applied.  Can always come back to restore the file
* MFA delete: requires MFA to (1) delete an object version (2) turn on/off versioning

## S3: Encryption at rest
Server Side Encryption (SSE)
* S3 managed keys (SSE-S3)
  * AWS manages all (encrypt key and rotate key)
* AWS Key Management Service, managed keys (SSE-KMS)
  * encrypt key's key (envelope key) gets an audit trail
  * either you or aws manages envelope key
* SSE with customer provided keys (SSE-C)
  * you do it all

Client Side Encryption: you do it before you give it to S3

You can create `bucket policy` which states everything stored in bucket must be encrypted.  When adding a file to the bucket, you must include in the request header as a parameter.  All PUT requests must state which encryption is to be used.


#### Volume Types:

|| Instance   | EBS | 
|--|------------|------------|
| persists:| ephemeral, No  |  Yes
| max size:| 10GB  | 1-2TB (pending OS)  |
| EC2 root volume on terminate:| gone | default is delete, can change|
| EC2 additional volumes on terminate | gone | will persist, even if root volume is instance
| Can be stopped? | No; reboot or terminate only | Of course! |
| Can upgrade EC2? | No; cannot stop instance | Of course!| 


Fun facts:
* You do not have to stop EC2 to make changes to the __root__ EBS volume
  * Note: magnetic drive size cannot be changed; old tech
* You can take a snapshot of a volume (best if stop the EC2 first)
  * Now you can __move__ the new volume to diffent AZ and create a new EC2.
  * Or you can __copy__ the snapshot to a __new region__.  
  * Or you can __make an image__ (AMI) from the snapshot, and copy the AMI to a new __region__
* EBS volumes are in the same AZ as the EC2 (kind of a duh moment)
* If volume is encrypted, then all snapshots are encrypted
  * cannot share encrypted snapshots

## Encryption & Downtime
Many resources can only have encrypt turned on at time of creation
* EFS (elastic file system) : used when multiple EC2 share a file system
* RDS: create new DB and migrate data
* EBS volumes
  * can migrate data from unencrypted to encrypted
  * can make snapshot and copy snapshot.  At time of copy you can apply encryption

Resources where encryption is more flexible
* S3
  * buckets
  * objects

## KMS vs. CloudHSM (hardware security modules)
Generate, store, manage own crypto keys

#### CloudHSM
* dedicated hardware; no multi-tenancy
* super security - no free tier
* FIPS (US govt standard)
* offers both asymmetric (can use different encryption algos & keys) & symmetric
  * public/private key are asymmetric
* FIPS compliance

#### KMS
* shared hardware; 
* multi-tenant managed service
* protect confidentiality of your keys
* symmetric (same encryption algos & keys)

## AMI's
Amazon machine image used to launch EC2 instance
* template for the root volume, OS, applications
* launch permissions: which AWS accounts can use the AMI (public, private, shared explicitly)
* additional volumes attached
* Amazon managed: Linux, Windows Server, etc

How to:
1. launch instance from existing AMI
2. connect your instance and customize it (install apps, copy data, etc)
3. create a custom AMI
4. register your AMI before it can be used
    * must register for every region you wish to use this AMI
    * AMI's are per region only, but can be copied btw regions

#### Sharing AMI's
* Options: private (default), public, shared explicity with other AWS accounts, sold on market place
* AMI's are stored in S3; not free
* can copy AMI, but need read permission to owner's S3 or EBS snapshot
* Limitations
  * cannot copy/share encrypted AMI
  * cannot copy Marketplace AMI's
  * cannot copy licensed AMI's 
    * OS: Windows, Red Hat
    * Application: Windows SQL


## Snowball
* transfer 100TB+ data
* Snowball Edge: comes with computing power.  Can use Lambda to do something to the data before it loads on to the Snowball

## Storage Gateway:
On prem software appliance to integrate with AWS services
1. File Gateway - NFS/SMB (linux/windows)
    * store files in S3
2. Volume Gateway - iSCSI
    * stored volumes: store everything local, then backup to AWS as EBS snapshot
    * cached volumes: use S3 as primary storage, cache frequent access
3. Tape Gateway - VTL (virtual tape library)
    * offsite async backups to Glacier using EBS snapshots

## Athena
Query S3 using SQL
* serverless, pay as you go, per TB scanned

# Section 6: Security

## Compliance Frameworks
1. PCI - credit card payments
2. ISO - 
3. HIPAA - health care in US

## DDoS
#### Amplification / Reflection
* attacker sends request from spoofed IP to NTP server.  NTP server sends a super large payload to the victim.  Attacker makes NTP server perform the attack for them.
* attacker floods victim with GET requests
* Slowloris attack: open many requests to victim and keep them open

#### Mitigate
* minimize attack surface area
* be ready to absorb the attack
* safeguard exposed resource
* learn normal behavior of your system
* detect abnormal behavior

#### AWS Shield
* Free service from AWS on all ELB, CloudFront, R53
* Shield Advanced - $3k /mo

## AWS Marketplace - Security Products
* Pentesting: submit a request form to AWS
* get hardened OS
 
## Custom IAM Lab
1. create a `policy` with JSON.  E.g. create policy which S3 can READ & LIST
2. attach the policy to a `role` E.g. create EC2 role and attach our policy
3. create buckets
4. launch EC2
5. ssh into EC2
6. try to `aws s3 ls`  Spoiler: it will fail
7. attach role to EC2 and repeat the command
8. new role __allows the command to be executed almost instantly__
9. try to write a file to S3
```
echo "this is a file" > file.txt
aws s3 cp file.txt s3://bjw-us-east
>> OUTPUT >> operation: Access Denied
```
10. Update the policy to allow WRITE
11. re-run the `s3 copy` and it works

#### Exam tips
* can change EC2 roles on the fly
* create policies with the visual editor or directly with JSON
* changing a policy or role will take affect immeditately

## MFA
* the QR code you use to setup your MFA can be re-used if you lose your phone
* you can force users to have MFA turned on
  * AWS Console (web) => IAM => select user => security creds => Assigned MFA
  * from the command line
    1. ssh into ec2
    2. make sure `aws configure` user has privledges
    3. generate the QR code 
    ```
    aws iam create-virtual-mfa-device --virtual-mfa-device-name ***mfa*** --outfile /home/ec2-user/QRCode.png --bootstrap-method QRCodePNG
    ```
    4. copy that to S3
    5. apply the code to our user
    ```
    aws iam enable-mfa-device --user-name EC2-User --serial-number arn:aws:iam::"***USERIDHERE***":mfa/EC2-User --authentication-code-1 123456 --authentication-code-2 654321
    ```
* you can enable [MFA for command line operations](https://aws.amazon.com/premiumsupport/knowledge-center/authenticate-mfa-cli/), but you have to use STS (security token service)
* you can download all your User details in IAM => `credential report`
  * show all users
  * last login
  * MFA
  * tons more

## STS - Security Token Service
Grant users `limited` & `temp` access to AWS resources.  Achieved using 1 of 3 ways:
1. Federation (commonly by using Active Directory)
    * uses SAML
    * grants users access based on Active Directory creds
    * SSO allows users to log in to AWS without IAM creds!
2. Federation with Mobile Apps
    * Facebook, Google, etc or really any OpenID provider
3. Cross Account Access
    * sharing AWS resources across different AWS accounts

#### Vocab:
* __Federation__: joining a list of users from one domain (IAM) to another domain (Active Directory)
* __Identity Broker__: service that allows you to federate
* __Identity Store__: service like FB or Google
* __Identity__: the user

#### Scenario:
1. Hosting a website on EC2 in your VPC
2. Users log into the website and it authenticates against companies active directory
3. The VPC is connected to the company's AD using IPSEC VPN
4. Once a user is logged in, they can access S3 bucket

Set this up: We want an __Identity Broker__ to join existing user auth from company's Active Directory and an IAM

1. user enters name/password on website
2. Identity Broker verifies against Active Directory
3. Identity Broker requests token from STS
   * good for 1-36 hours
   * returns policy with user permissions
   * `GetFederationToken` is the function call
4. user calls S3 using their STS   
5. S3 verifies the STS has IAM permissions


## Security and Logging
1. CloudTrail - API calls
2. Config - state of AWS configuration
3. CloudWatch Logs - performance metrics
4. VPC Flow Logs - network traffic

* Always limit access to log files
  * IAM users, groups, roles, & policies
  * bucket policies
  * MFA

* Create alerts when logs are created or failed
  * CloudTrail notifications
  * AWS Config Rules
* Alerts are specific, but do not leak too much detail (point to the log file location)
* prevent log manipulation
  * CloudTrail log file verification
  * CloudTrail log file encryption

## Hypervisor
Virual Machine Monitor (VMM) or just a fancy way of saying the thing that manages (runs) your Virtual Machine(s).  The hypervisor is the __host__ and the each VM is called a __guest machine__.

#### Xen Hypervisor
The VMM which EC2 uses.  Xen can have guest OS's running either Paravirtual (PV) or using Hardware Virtual Machine (HVM)
1. HVM: guests are fully virtualized.  The VM is on top the the hypervisor and not aware they are sharing processing time with other VMs
2. PV: lighter form of virtualization and it used to be quicker (cannot do Windows VM).  Let's talk about `rings` for security
    * ring 0: highest privledge, where host (Zen hypervisor) executes
    * ring 1: EC2 instance
    * ring 3: application on the instance (ring 2 is unknown)

## Dedicated Instance vs. Dedicated Host (EC2)
  
| Instance     | Host |
|-------------|----------|
| run in VPC, on hardware dedicated to host | more control of how your physical server is placed on host     |
| may share hardware within same AWS account | consistently deploy instances to the same physical hardware |
| on demand, reserve instance, spot | enables server-bound sofware licenses |
| | great for compliance & regulations |
| | see sockets, cores, ID of server |
| charge by instance | charge by host |


## AWS System Manager EC2 Run Command
Run command is for admin'ing many EC2 at once (on prem & AWS managed).  Automate common tasks and ad hoc config changes.  E.g.: installing apps, patches, join new instance to Windows domain.  Do not even have to RDP (login) to the system!
* Pick the EC2 manually
* Pick the EC2's by tag

1. need IAM role to perform SysMgr tasks on EC2
    * `AmazonEC2RoleforSSM`
2. launch Win Server EC2    
    * do **not** need to open RDP port for remote control of machine
3. go to **Run Command**
    * pick a `command document`. E.g.: AWS-ConfigureCloudWatch
    * set our target (Win EC2)
    * Run

#### Requirements
1. Have to have IAM role for SSM
2. Have to have SSM agent running on instance


## AWS System Manager Parameter Store
Storing secrets (users, passwords, license keys, etc) found in EC2 section
1. string
2. list of string
3. secure string (cannot see value after entered) using KMS

## AWS Config with S3
Compliance by adding rules
#### Good ones for S3
* s3-bucket-public-write-prohibited
* s3-bucket-public-read-prohibited

## Presigned URL
Say you want your SDK (Python) to access secured item in S3.  Authenticate with Presigned URL!
1. create role.  E.g. policy: `AmazonS3FullAccess`
2. create EC2 with role
3. ssh into EC2
    * `aws s3 mb s3://bjw-cli` # make a bucket
    * `echo "this is a file" > file.txt` # make a local file
    * `aws s3 cp file.txt s3://bjw-cli` # copy local file to S3
    * `aws s3 ls s3://bjw-cli` # verify file is in S3
    * try to open file from web S3.  Spoiler: cannot, it is private
    * `aws s3 presign s3://bjw-cli/file.txt --expires-in 300` # presign the file for 300 seconds. This will return a URL
    * follow the URL, can see file.  Did not have to change bucket policy, file permissions, etc

## Trusted Advisor vs. Inspector
Guess which service we're talking about based on the details

#### Amazon Inspector (think **security** and install agent on instance)
Automated security assessment service based on best practices.  Produces a detailed list of security findings based on priority.  
1. create target E.g. ec2 instance
2. install agent on target (creates the role) using Run Command
    * alternatively: ssh into instance and [follow instructions](https://docs.aws.amazon.com/inspector/latest/userguide/inspector_installing-uninstalling-agents.html#install-linux).
3. create an `assessment template`
   * pick pre-defined package like "Best Practices" or "Hardened OS Benchmarks", etc
4. perform the `assessment run`
   * default time is an hour
5. review the findings against the rules
   * create a 600+ page pdf report, SHIZZAM

#### Trusted Advisor (think **performance**)
1. cost optimize
2. performance
3. security (just like Inspector!)
4. fault tolerance

#### Shared Responsibility Model (for security)
[AWS](https://aws.amazon.com/compliance/shared-responsibility-model/) manages security **of** the cloud, whereas you manage security **in** the cloud.  AWS provides the infrastructure security.

Model changes, depending on which service type:

1. __Infrastructure__: ECS, EBS, Auto Scaling, VPC - you own it.
2. __Container__: EC2 - you don't manage the OS, but you own the network access to container
3. __Abstracted__: S3, DynamoDB, SQS, SES - AWS owns it, but you own policies to access the services

* RDS: you don't have to patch.  
* PHP in Elasticbeanstock: don't have to patch


#### Other Stuff
1. AWS Artifact: on demand compliance document downloads (red herring exam question)


# Section 7 Networking & Route 53
#### Review
* SOA records
  1. name of server that supplied the data for zone
  2. admin of the zone (contact details for domain)
  3. TTL - how long the DNS record is cached
* NS records (name server) - used by top level domain to direct traffic to the content DNS server
* A record (address) - translate domain to IP address
Fun fact: ELB only use DNS; never has IP4/6 address because AWS will manage all that behind the scenes.  Moreover, you never use A record.  Instead use AS record 
* CName - make one site point to another (instead of two A records) `mail.google.com => google.com/mail`
* Alias Record - AWS term, much like a CName.  Good for mapping `example.com => elb23523.elb.amazonaws.com`
    * created because you cannot make a CName to a naked domain `example.com`.  CName has to map to IPv4, which your load balancer will never give you.  This is a circular problem =(
    * also great because as AWS changes IP address for your load balance, R53 with auto update too!
    * Alias records are *free*, CName will cost you.  
    * Always use Alias records

#### Lab
Start multiple EC2s across multiple regions and zones

```
#!/bin/bash
yum update -y
yum install httpd -y
cd var/www/html/
echo "web 01 - N. Virg" > index.html
service httpd start
chkconfig httpd on    
```
| Name | IP | Zone |
|------|----|------|
| web01 | 35.175.150.185 | us-east-1 |
| web02 | 3.83.123.160   | us-east-1 |
| web03 | 34.237.245.107 | us-east-1 |
| web04 | 18.130.57.158  | eu-west-2 (london) |

### Routing
1. **Simple**: can only use a single record with multiple IP addresses and returns all values **randomly**
2. **Weighted**: percentage based routing.  20% goes to A, 80% goes to B.  
3. **Latency**: lowest ping wins.  You can put multiple IP in a single region. E.g.: web01, web02, web03 all go into region for US-East.  web04 goes into separate London region.  How does r53 pick for which instance within US-East region?  Probably simple.  Who knows
4. **Failover**: disaster recovery using health checks.  If `primary` site is dead, route to `secondary`
5. **Geolocation**: based on where client DNS query originates.  Best to set a default record
6. **Multi-value**: simple with failover.  If one fails, it is removed from list of valid returned simple options


# Section 8: VPC's
Virtual network/data center in the cloud.

#### (1) Connect to our VPC
1. internet gateway - limit = 1
2. virtual private gateway

#### (2) Router

#### (3) Router table

#### (4) NACL (network access controller)
* more granular control E.g.: block IP, country, etc
* stateless: have to open inbound & outbound ports

#### (5) Subnet (public or private)

#### (6) Security Group
* span multiple AZ
* stateful: symmetrical, if port 80 is open.. it is open for both

#### (7) Instance

#### Multiple VPC's
* can connect with direct network route using private IPs (VPC peering)
* can connect to different AWS accounts
* instances behave like on the same private network
* no transitive peering (chaining), must have direct connect

#### CIDR
* [CIDR range calculator](http://cidr.xyz/)
* AWS will reserve 5 IP address from your range.  First 4 & last 1

|CIDR         | First    | Last         | Count |
|-------------|----------|------------  |-------|
| 10.0.0.0/16 | 10.0.0.1 | 10.0.255.254 | 65,536|
| 10.0.0.0/24 | 10.0.0.1 | 10.0.0.254   | 256 |

#### NAT Instance (old) & NAT Gateway (current)
* NAT Instance: EC2 instance using a NAT Instance AMI
  * make new EC2 in public subnet w/ ssh, http, https
  * disable EC2 "source/dest check"
  * why this way sucks:
    * single instance 
    * single AZ 
    * single throughput
    * single point of failure
* NAT Gateway
  * auto scaling
  * AWS managed; no patch, no secgrp
  * Need to make multiple GWs in multiple AZ

#### Network Access Control List (NACL)
* Get first one by default; which allows everything.  
  * when you create a NACL, it denies everything
* Sits outside of subnet.  
* Each subnet can only have 1 NACL
* Inbound/Outbound rules are asymetric

#### VPC endpoint
Inside of my public VPC, I want to interact with S3.  As it stands, my traffic would leave my internal VPC, go to the outside internet, then re-enter the AWS landscape to talk with S3.  We can create a gateway to talk directly with S3, all while staying inside of AWS land.
1. create a role
    * allow ec2 to do whatever with S3
    * apply role to private ec2
2. test the role
    * `aws s3 ls` works because we have a NAT GW/Instance out to the interwebs
    * make sure the NAT GW/instance is off
      * vpc => mysubnet => route table => delete 0.0.0.0/0 & NAT
    * ssh into private ec2 (from public)
    * `aws s3 ls` won't work (as intended)
3. create the Endpoint
    * VPC => Endpoint    
    * choose between:
      1. interface: elastic network interface (ENI)
      2. gateway: much like NAT gateway, AWS managed
    * search by `Service Name : *.s3`

      | Name | Owner | Type |
      |---|--|--|
      | com.amazonaws.us-east-1.s3 | amazon | Gateway |
    * pick our VPC
    * pick our default/main route table (that one is not public)
    * go back and look at the main route table, it should have updated the routes to point to the endpoint
4. verify endpoint
    * go back to private ec2
    * `aws s3 ls` works because we have internal AWS connection (endpoint), yeet! 


#### VPC Flow Logs
Network traffic (IPs) stored in CloudWatch Logs.  Can be 3 different levels:
1. VPC
2. Subnet
3. Network Interface

Do the thing:
1. select your VPC => Action => Flow Log
2. create a role (can do this here)
3. create a CloudWatch (have to go to CW)
Exam Tips:
* cannot flow log a peered VPC
* cannot change IAM 
* not all IP traffic is monitored
  * Amazon DNS
  * Windows license activation
  * metadata for 169.254.169.254
  * DHCP
  * reserved IP traffic

#### NAT vs Bastion

|NAT instance|Bastion|
|-|-|
| create a special type of EC2 | create 1 hardened public instance, then jump to private instances|
| Expose Internet traffic for EC2 | SSH or RDP into the bastion, then jump |
|almost retired| |


## Make a VPC

1. create new vpc 10.0.0.0/16 (largest range)
    * router
    * default (main) Route Table
    * Network ACL
2. put some subnets into vpc
    * Subnet 1: 10.0.1.0/24
    * Subnet 2: 10.0.2.0/24
3. make an Internet Gateway (can only have 1)
    * attach to vpc
4. make new route table
    * connect to subnet 1 (override default route table)
5. connect IGW to our route table
    * Dest: 0.0.0.0/0     # IP4
    * Dest: ::/0          # IP6
    * Target: our IGW
6. associate subnet 1 with our route table (now has public access)
7. turn on "auto assign IP" for subnet 1
8. create security group for subnet 2 which allows subnet to talk
    * Type: ssh
    * IP: 10.0.1.0/24
9. Test it out: ssh into subnet 1 and jump over to subnet 2 (from 1)    
10. Give subnet 2 a bastion (jump box) host
    * **NAT instance** (old): 
      * create EC2 with NAT AMI in subnet 1
      * from default route table (one subnet 2 is using), we need a route out
        * Dest: 0.0.0.0/0
        * Target: NAT instance
    * **NAT Gateway** (current IP4):
      * create NAT GW from VPC menu
      * put in public subnet
      * create new elastic IP address
      * from default route table (one subnet 2 is using), we need a route out
        * Dest: 0.0.0.0/0
        * Target: NAT gateway
    * **Egress Only Internet GW** (current IP6):
      * dunno, mate
11. Stop using default NACL (it's 100% open)
    * make new NACL
    * create rules (asymetric)
      * lowest rule = highest priority
    
    INBOUND rules (starting at 100)

    |Rule|Type|Source|Which|
    |--|-|-|-|
    |100| HTTP (80) | 0.0.0.0/0 | ALLOW |
    |200|HTTPS (443)|0.0.0.0/0 |ALLOW |
    |300|SSH (22)| 0.0.0.0/0| ALLOW |
  
    OUTBOUND rules (starting at 100)

    |Rule|Type|Source|Which|
    |--|-|-|-|
    |100| HTTP (80) | 0.0.0.0/0 | ALLOW |
    |200|HTTPS (443)|0.0.0.0/0 |ALLOW |
    |300|**Custom TCP (1024-65535)**| 0.0.0.0/0| ALLOW |

    WTF is the custom outbound rule 300?  **[Ephemeral ports](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html#nacl-ephemeral-ports)** is the client port number which is randomized.  Basically, when the client makes HTTP request, our server sends back the response on a random port number which the client tells us.  The range 1024-65535 will support all OS's.

    * now that we have a custom NACL, associate it to our public subnet.
    * if we create a `Rule 99` this would supercede all other rules
      * Rule 99, http (80), ###.###.###.###/32, deny
      


## Section 9: Automation 
### CloudFormation
Service that allows you to manage, configure, and provision your AWS infrastructure as code

* YAML or JSON
* `+ use version control on templates
* `+ manage updates & dependancies
* `+ rollback entire stack

#### Creating a template
1. make your template (JSON or YAML)
2. upload to CF via S3
3. CF reads the template and makes API calls on your behalf
4. the resulting resources are called a `stack`

* __AWSTemplateFormatVersion__: 2010-09-09  # always this
* __Parameters__: # input values to give the template. E.g.: we are creating either ***prod*** or ***dev*** env 
* __Conditions__: # decisions CF would make based on the params you give it
* __Mappings__: # E.g.: set value based on region; think an if this, then that switch.  Use xxx AMI if in US-EAST-1
* __Transform__: # run `snippets` of code outside the main template. E.g.: some Lambda or Snippet sitting in S3 bucket
  * [Cloudformation Template Snippets](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/CHAP_TemplateQuickRef.html)
* __Resources__: # Only required part!  The AWS resource you are deploying. E.g.: an EC2 instance
* __Outputs__: # completely user defined. E.g.: output the instance ID of the EC2 we are creating

#### CloudFormation Lab
See the attached files

#### Elastic Beanstalk
* Used for scaling web apps in Java, .NET, PHP, Node.js, Python, Ruby, Go, Docker
* Simply upload your existing code and AWS will do the rest
* Fast, simple way to deploy
* EBeanstalk will auto: 
  * scale (up/down)
  * update platforms.  E.g.: Java
    * also update your server E.g.: Tomcat, Nginx, IIS
  * monitor via dashboard
    * X-Ray 
    * CloudWatch

You can take over control if you don't want auto mode turned on


#### OpsWorks
* Automate server config with Puppet or Chef
* AWS manages instances; you don't have to configure and operate the environment


## Gaps: Topcis Not Covered
* **Amazon Redshift** is a fully managed, petabyte-scale **data warehouse** service in the cloud. You can start with just a few hundred gigabytes of data and scale to a petabyte or more. This enables you to use your data to acquire new insights for your business and customers.
* **Elastic MapReduce** (EMR) is a managed cluster platform that simplifies running big data frameworks, such as Apache Hadoop and Apache Spark, on AWS to process and analyze vast amounts of data.
* **Elastic IP** When an EC2 is stopped, it will be assigned a new IPv4.  So we use EIP for mapping to R53. Currently do not support Elastic IP addresses for IPv6.
* **DynamoDB**:  When you create a **global table**, you specify the AWS regions where you want the table to be available. DynamoDB performs all of the necessary tasks to create identical tables in these regions, and propagate ongoing data changes to all of them.  **Autoscaling**: Application Auto Scaling issues an `UpdateTable` request to adjust your table's provisioned throughput.
* You can have an IAM user assume a role for X seconds
* **VPC Endpoint** enables you to privately connect your VPC to supported AWS services and VPC endpoint services powered by PrivateLink without requiring an internet gateway, NAT device, VPN connection, or AWS Direct Connect connection. There are two types of VPC endpoints: interface endpoints and gateway endpoints. Create the type of VPC endpoint required by the supported service.
  * Gateway: S3 & DynamoDB
  * Interface: everything else
* Compare AWS [plans](https://aws.amazon.com/premiumsupport/plans/)
  * Business: 24*7 support; 1 hr
  * Enterprise: < 15 minute
* AWS **Cost Explorer** has an easy-to-use interface that lets you visualize, understand, and manage your AWS costs and usage over time. 
* **AWS Artifact** is your go-to, central resource for compliance-related information that matters to you. It provides on-demand access to AWS’ security and compliance reports and select online agreements. Reports available in AWS Artifact include our Service Organization Control (SOC) reports, Payment Card Industr
* **AWS Data Pipeline** is a web service that you can use to automate the movement and transformation of data. With AWS Data Pipeline, you can define data-driven workflows, so that tasks can be dependent on the successful completion of previous tasks. You define the parameters of your data transformations and AWS Data Pipeline enforces the logic that you've set up.

## Exam Practice
1. [WhizLabs](https://www.whizlabs.com/aws-sysops-administrator-associate/free-test/) with 10 free ones (this one is so-so.  I have found multiple wrong answers)
2. [Udemy](https://www.udemy.com/aws-certified-sysops-administrator-associate-practice-exams-soa-c01/) with high reviews
3. [Udemy](https://www.udemy.com/aws-certified-sysops-administrator-2018-practice-questions/) with questionable reviews


### Config vs. Trusted Advisor vs. Inspector
* Config: compliance
* Trusted Advisor: make suggestions
* Inspector: use templates for best practices