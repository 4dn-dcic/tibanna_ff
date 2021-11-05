from tibanna_ffcommon.vars import BUCKET_NAME

def test_bucket_name():
    bucket = BUCKET_NAME('fourfront-green', 'FileProcessed')
    assert bucket == 'elasticbeanstalk-fourfront-webprod-wfoutput'

def test_bucket_name2():
    bucket = BUCKET_NAME('fourfront-blue', 'FileReference')
    assert bucket == 'elasticbeanstalk-fourfront-webprod-files'

def test_bucket_name3():
    bucket = BUCKET_NAME('fourfront-cgap', 'FileFastq')
    assert bucket == 'elasticbeanstalk-fourfront-cgap-files'

def test_bucket_name4():
    bucket = BUCKET_NAME('fourfront-blue', 'FileMicroscopy')
    assert bucket == 'elasticbeanstalk-fourfront-webprod-files'
