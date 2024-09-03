import boto3
from botocore.exceptions import ClientError
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, REGION_NAME

def analyze_document(jpg_file, bucket):
    textract = boto3.client('textract',
                            aws_access_key_id=AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=REGION_NAME)

    try:
        response = textract.analyze_document(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': jpg_file
                }
            },
            FeatureTypes=["TABLES", "FORMS"]
        )
        return response
    except ClientError as e:
        print(f"An error occurred: {e}")
        return None