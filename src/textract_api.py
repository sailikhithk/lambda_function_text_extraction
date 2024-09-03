import boto3
from botocore.exceptions import ClientError
import os
import logging
import watchtower

# Set up CloudWatch logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler())

# Initialize Textract client
textract = boto3.client('textract', region_name=os.getenv('REGION_NAME'))

def analyze_document(jpg_file, bucket):
    """
    Analyze a document using Amazon Textract.
    
    :param jpg_file: S3 key of the JPG file to analyze
    :param bucket: S3 bucket name
    :return: Textract response or None if an error occurs
    """
    try:
        logger.info(f"Analyzing document: s3://{bucket}/{jpg_file}")
        response = textract.analyze_document(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': jpg_file
                }
            },
            FeatureTypes=["TABLES", "FORMS"]
        )
        logger.info(f"Document analysis completed for: s3://{bucket}/{jpg_file}")
        return response
    except ClientError as e:
        logger.error(f"An error occurred while analyzing document s3://{bucket}/{jpg_file}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while analyzing document s3://{bucket}/{jpg_file}: {e}")
        return None