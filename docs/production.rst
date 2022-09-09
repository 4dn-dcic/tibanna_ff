=====================
Production Deployment
=====================


Deploying Tibanna requires a few environment variables, including:

* AWS_ACCESS_KEY_ID and SECRET + SESSION_TOKEN (if using Okta)
* ACCOUNT_NUMBER
* S3_ENCRYPT_KEY
* S3_ENCRYPT_KEY_ID (if deploying to an encrypted environment)
* GLOBAL_ENV_BUCKET
* TIBANNA_VERSION

You must also have an existing network (VPC) with subnets to target and a security group
to associate with Tibanna. Tibanna takes these arguments directly
from the command line. Note that if using a Sentieon license server you may need to
add some rules to the default application security group.

--------
4dn-dcic
--------

Deploy Tibanna to the main account with:

* Your AWS_ACCESS_KEY_ID/SECRET with appropriate permissions
* ACCOUNT_NUMBER=643366669028
* S3_ENCRYPT_KEY=<key from environment GAC you are deploying>
* S3_ENCRYPT_KEY_ID unset since Fourfront is not encrypted
* GLOBAL_ENV_BUCKET=foursight-prod-envs
* TIBANNA_VERSION=<version of Tibanna to use in the lambdas, e.g. 2.1.0>
* -e <env_name>, for valid names see s3://foursight-prod-envs/main.ecosystem, typically "data" or "fourfront-webdev"
* --subnets subnet-006dce98b4b349b90 (C4NetworkMain Public Subnet A)
* -r sg-04b9d1a18fd086f33 (C4NetworkMain Application Security Group)

For example:
``tibanna_4dn deploy_pony -e fourfront-webdev --subnets subnet-006dce98b4b349b90 -r sg-04b9d1a18fd086f33``

----------------------
CGAP Isolated Accounts
----------------------

Deploy Tibanna to isolated accounts with:

* Your Okta credentials for the account, ID/Secret/Session Token
* ACCOUNT_NUMBER=<isolated account number, see envs Confluence page>
* S3_ENCRYPT_KEY=<key from environment GAC you are deploying>
* S3_ENCRYPT_KEY_ID=<key ID from environment GAC you are deploying, if applicable>
* GLOBAL_ENV_BUCKET=<Get this value from the GAC as well>
* TIBANNA_VERSION=<version of Tibanna to use in the lambdas, e.g. 2.1.0>
* -e <env_name>, for valid names see main.ecosystem in $GLOBAL_ENV_BUCKET
* --subnets <subnetA>,<subnetB>
* -r <application security group>

For example:
``tibanna_cgap deploy_zebra --subnets subnet-07bac0312de6cff43 subnet-0d4a7670776d7c823 --env cgap-dbmi -r sg-033046050ef0b02c1``

--------------
Debugging Tips
--------------

Tibanna consists of a step function with 4 lambda functions. Each Lambda function has it's own
associated CloudWatch log which can be directly reached from the Lambda console. Typically when
an issue occurs the step function will fail and one of the steps will show up as red. First, use
``tibanna log --job-id <jid>`` to see if the job failed in execution. If at the end you can see
a successful run, or if no log is generated, you will want to investigate the CW logs. First
check the Lambda that failed, then follow the traceback to see which Lambda was the source.
You may need to navigate timestamps and make use of the search functionality within log groups
to find the correct events. Using the job ID as a search query (can be acquired from the input
JSON) is usually a quick way to locate the relevant events and timestamps.
