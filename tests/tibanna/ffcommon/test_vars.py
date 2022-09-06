from tibanna_ffcommon.vars import BUCKET_NAME


def test_bucket_name_prod_buckets():
    bucket = BUCKET_NAME('fourfront-production-green', 'FileProcessed')
    assert bucket == 'elasticbeanstalk-fourfront-webprod-wfoutput'
    bucket = BUCKET_NAME('fourfront-production-green', 'FileReference')
    assert bucket == 'elasticbeanstalk-fourfront-webprod-files'
    bucket = BUCKET_NAME('data', 'FileProcessed')
    assert bucket == 'elasticbeanstalk-fourfront-webprod-wfoutput'
    bucket = BUCKET_NAME('data', 'FileReference')
    assert bucket == 'elasticbeanstalk-fourfront-webprod-files'


def test_bucket_name_staging_buckets():
    bucket = BUCKET_NAME('fourfront-production-blue', 'FileProcessed')
    assert bucket == 'elasticbeanstalk-fourfront-webprod-wfoutput'
    bucket = BUCKET_NAME('fourfront-production-blue', 'FileReference')
    assert bucket == 'elasticbeanstalk-fourfront-webprod-files'
    bucket = BUCKET_NAME('staging', 'FileProcessed')
    assert bucket == 'elasticbeanstalk-fourfront-webprod-wfoutput'
    bucket = BUCKET_NAME('staging', 'FileReference')
    assert bucket == 'elasticbeanstalk-fourfront-webprod-files'


def test_bucket_name_webdev_buckets():
    bucket = BUCKET_NAME('fourfront-webdev', 'FileProcessed')
    assert bucket == 'elasticbeanstalk-fourfront-webdev-wfoutput'
    bucket = BUCKET_NAME('fourfront-webdev', 'FileReference')
    assert bucket == 'elasticbeanstalk-fourfront-webdev-files'
    bucket = BUCKET_NAME('webdev', 'FileProcessed')
    assert bucket == 'elasticbeanstalk-fourfront-webdev-wfoutput'
    bucket = BUCKET_NAME('webdev', 'FileReference')
    assert bucket == 'elasticbeanstalk-fourfront-webdev-files'
