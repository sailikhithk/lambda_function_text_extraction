import os
import json
from datetime import datetime
from src.document_preparation import prepare_document
from src.textract_api import analyze_document
from src.response_parser import parse_response
from src.document_specific_processing import process_checkboxes
from src.template_matching import match_template, log_matching_results
from src.post_processing import post_process
from botocore.exceptions import ClientError
import boto3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configurations from environment variables
BUCKET = os.getenv('BUCKET')
AWS_ACCESS_KEY_ID = os.getenv('KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('VALUE')
REGION_NAME = os.getenv('REGION_NAME')

print(f"Received environment variables are BUCKET: {BUCKET}, AWS_ACCESS_KEY_ID: {AWS_ACCESS_KEY_ID}, AWS_SECRET_ACCESS_KEY: {AWS_SECRET_ACCESS_KEY}, REGION_NAME: {REGION_NAME}")

# Initialize S3 client
s3_client = boto3.client('s3',
                         aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                         region_name=REGION_NAME)

def save_intermediate_result(data, filename):
    """Save intermediate results directly to S3."""
    s3_object_name = f"intermediate_results/{filename}"
    try:
        s3_client.put_object(Body=json.dumps(data, indent=2), Bucket=BUCKET, Key=s3_object_name)
        logging.info(f"Intermediate result saved to S3 as {BUCKET}/{s3_object_name}")
    except ClientError as e:
        logging.error(f"Error saving intermediate result to S3: {e}")

def upload_to_s3(file_path, bucket, object_name=None):
    """Upload a file to S3."""
    if object_name is None:
        object_name = os.path.basename(file_path)

    try:
        logging.info(f"Uploading {file_path} to S3 bucket {bucket} as {object_name}")
        s3_client.upload_file(file_path, bucket, object_name)
        logging.info(f"File uploaded successfully to {bucket}/{object_name}")
        return True
    except ClientError as e:
        logging.error(f"Error uploading file to S3: {e}")
        return False

def upload_jpg_to_s3(jpg_content, bucket, object_name):
    """Upload JPG file content directly to S3."""
    try:
        logging.info(f"Uploading JPG content to S3 bucket {bucket} as {object_name}")
        s3_client.put_object(Body=jpg_content, Bucket=bucket, Key=object_name)
        logging.info(f"JPG content uploaded successfully to {bucket}/{object_name}")
        return True
    except ClientError as e:
        logging.error(f"Error uploading JPG content to S3: {e}")
        return False

def process_single_file(s3_file, file_index):
    """Process a single file using Textract and save results to S3."""
    try:
        logging.info(f"Processing file: {s3_file}")
        response = analyze_document(s3_file, BUCKET)
        if not response:
            logging.error(f"Failed to analyze document: {s3_file}")
            return None

        parsed_kv, parsed_tables = parse_response(response)
        logging.info(f"Parsed key-value pairs and tables from document.")

        # Save extracted data
        extracted_data = {
            "key_value_pairs": parsed_kv,
            "tables": parsed_tables
        }
        save_intermediate_result(extracted_data, f"extracted_data_{file_index}.json")

        processed_kv = process_checkboxes(parsed_kv, response)
        logging.info(f"Processed checkboxes in document.")

        matched_data = match_template(processed_kv, parsed_tables)
        logging.info(f"Matched template data.")

        # Save matched data
        save_intermediate_result(matched_data, f"matched_data_{file_index}.json")

        log_matching_results(matched_data)

        final_result = post_process(matched_data)
        logging.info(f"Completed post-processing for file: {s3_file}")

        return final_result
    except Exception as e:
        logging.error(f"Error processing file {s3_file}: {e}")
        return None

def save_result_to_s3(result, bucket, object_name):
    """Save the final result to S3."""
    try:
        logging.info(f"Saving final result to S3: {bucket}/{object_name}")
        s3_client.put_object(Body=json.dumps(result, indent=2), Bucket=bucket, Key=object_name)
        logging.info(f"Result saved to S3 as {bucket}/{object_name}")
        return True
    except ClientError as e:
        logging.error(f"Error saving result to S3: {e}")
        return False

def lambda_handler(event, context):
    """AWS Lambda handler function."""
    try:
        # Retrieve the S3 bucket and key from the Lambda event
        logging.info(f"Received event: {json.dumps(event)}")
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        logging.info(f"Extracted bucket: {bucket}, key: {key}")
    except KeyError as e:
        logging.error(f"Error parsing event data: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid event data')
        }

    try:
        # Download the file from S3 directly into memory
        logging.info(f"Attempting to download file from S3: {bucket}/{key}")
        response = s3_client.get_object(Bucket=bucket, Key=key)
        pdf_content = response['Body'].read()
        logging.info(f"Downloaded file from S3: {bucket}/{key}")
    except ClientError as e:
        logging.error(f"Error downloading file from S3: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error downloading file from S3')
        }

    try:
        # Process the document directly from the S3 object content
        logging.info(f"Preparing document from S3 content.")
        jpg_files = prepare_document(pdf_content)  # Assuming prepare_document can handle raw bytes
        logging.info(f"Prepared {len(jpg_files)} JPG files")

        s3_files = []
        for index, jpg_file in enumerate(jpg_files):
            s3_object_name = f"textract_input/page_{index}.jpg"
            if upload_jpg_to_s3(jpg_file, BUCKET, s3_object_name):
                s3_files.append(s3_object_name)

        if not s3_files:
            logging.error("No files were uploaded to S3. Exiting.")
            return {
                'statusCode': 500,
                'body': json.dumps('No files were uploaded to S3.')
            }
    except Exception as e:
        logging.error(f"Error during document preparation and S3 upload: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error during document preparation and S3 upload.')
        }

    try:
        results = []
        for index, s3_file in enumerate(s3_files):
            result = process_single_file(s3_file, index)
            if result:
                results.append(result)

        # Combine results from all pages
        combined_result = {}
        for result in results:
            for key, value in result.items():
                if key not in combined_result:
                    combined_result[key] = value
                elif isinstance(value, dict):
                    combined_result[key].update(value)
                elif isinstance(value, list):
                    combined_result[key].extend(value)
                else:
                    # For scalar values, keep the last non-empty value
                    if value:
                        combined_result[key] = value

        logging.info("Processing completed. Final result:")
        print(json.dumps(combined_result, indent=2))

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"extraction_result_{timestamp}.json"
        s3_result_object_name = f"extraction_results/{result_filename}"
        save_result_to_s3(combined_result, BUCKET, s3_result_object_name)

        return {
            'statusCode': 200,
            'body': json.dumps('Document processed successfully.')
        }
    except Exception as e:
        logging.error(f"Error combining and saving results: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error combining and saving results.')
        }
