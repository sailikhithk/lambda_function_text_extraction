import os
import json
from datetime import datetime
import boto3
import logging
from botocore.exceptions import ClientError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configurations from environment variables
S3_BUCKET = os.getenv('S3_BUCKET')
AWS_REGION = os.getenv('REGION_NAME')
# Template Configuration
TEMPLATE_S3_KEY = os.environ.get('TEMPLATE_S3_KEY', 'templates/template.json')

# Initialize S3 client
s3_client = boto3.client('s3', region_name=AWS_REGION)

def ensure_template_in_s3():
    try:
        logging.info(f"Checking if template exists in S3: {S3_BUCKET}/{TEMPLATE_S3_KEY}")
        # Check if template exists in S3
        s3_client.head_object(Bucket=S3_BUCKET, Key=TEMPLATE_S3_KEY)
        logging.info(f"Template found in S3: {S3_BUCKET}/{TEMPLATE_S3_KEY}")
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            logging.warning(f"Template not found in S3: {S3_BUCKET}/{TEMPLATE_S3_KEY}")
            # Template doesn't exist, upload it
            local_path = os.path.join(os.path.dirname(__file__), TEMPLATE_S3_KEY)
            logging.info(f"Looking for local template at: {local_path}")
            if os.path.exists(local_path):
                with open(local_path, 'rb') as file:
                    s3_client.put_object(Body=file, Bucket=S3_BUCKET, Key=TEMPLATE_S3_KEY)
                logging.info(f"Template uploaded to S3: {S3_BUCKET}/{TEMPLATE_S3_KEY}")
            else:
                logging.error(f"Local template file not found: {local_path}")
        else:
            logging.error(f"Error checking template in S3: {e}")

def save_intermediate_result(data, filename):
    """Save intermediate results directly to S3."""
    s3_object_name = f"intermediate_results/{filename}"
    try:
        logging.info(f"Saving intermediate result to S3: {S3_BUCKET}/{s3_object_name}")
        s3_client.put_object(Body=json.dumps(data, indent=2), Bucket=S3_BUCKET, Key=s3_object_name)
        logging.info(f"Intermediate result saved to S3 as {S3_BUCKET}/{s3_object_name}")
    except ClientError as e:
        logging.error(f"Error saving intermediate result to S3: {e}")

def process_single_file(s3_file, file_index):
    """Process a single file using Textract and save results to S3."""
    try:
        logging.info(f"Processing file: {s3_file}")
        response = analyze_document(s3_file, S3_BUCKET)
        logging.info(f"Textract response: {response}")
        if not response:
            logging.error(f"Failed to analyze document: {s3_file}")
            return None

        parsed_kv, parsed_tables = parse_response(response)
        logging.info(f"Parsed key-value pairs: {parsed_kv}")
        logging.info(f"Parsed tables: {parsed_tables}")

        extracted_data = {
            "key_value_pairs": parsed_kv,
            "tables": parsed_tables
        }
        save_intermediate_result(extracted_data, f"extracted_data_{file_index}.json")

        processed_kv = process_checkboxes(parsed_kv, response)
        logging.info(f"Processed checkboxes in document: {processed_kv}")

        matched_data = match_template(processed_kv, parsed_tables)
        logging.info(f"Matched template data: {matched_data}")

        save_intermediate_result(matched_data, f"matched_data_{file_index}.json")

        log_matching_results(matched_data)

        final_result = post_process(matched_data)
        logging.info(f"Completed post-processing for file: {s3_file}, result: {final_result}")

        return final_result
    except Exception as e:
        logging.error(f"Error processing file {s3_file}: {e}", exc_info=True)
        return None

def save_result_to_s3(result, object_name):
    """Save the final result to S3."""
    try:
        logging.info(f"Saving final result to S3: {S3_BUCKET}/{object_name}")
        s3_client.put_object(Body=json.dumps(result, indent=2), Bucket=S3_BUCKET, Key=object_name)
        logging.info(f"Result saved to S3 as {S3_BUCKET}/{object_name}")
        return True
    except ClientError as e:
        logging.error(f"Error saving result to S3: {e}", exc_info=True)
        return False

def lambda_handler(event, context):
    """AWS Lambda handler function."""
    try:
        logging.info(f"Received event: {json.dumps(event)}")
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        logging.info(f"Processing file: {bucket}/{key}")
        # Ensure template is in S3
        ensure_template_in_s3()
    except KeyError as e:
        logging.error(f"Error parsing event data: {e}", exc_info=True)
        return {'statusCode': 400, 'body': json.dumps('Invalid event data')}

    try:
        logging.info(f"Attempting to download file from S3: {bucket}/{key}")
        response = s3_client.get_object(Bucket=bucket, Key=key)
        pdf_content = response['Body'].read()
        logging.info(f"Downloaded file from S3: {bucket}/{key}, Content size: {len(pdf_content)} bytes")
    except ClientError as e:
        logging.error(f"Error downloading file from S3: {e}", exc_info=True)
        return {'statusCode': 500, 'body': json.dumps('Error downloading file from S3')}

    try:
        logging.info("Starting document preparation")
        jpg_files = prepare_document(pdf_content, S3_BUCKET)
        logging.info(f"Prepared {len(jpg_files)} JPG files: {jpg_files}")

        if not jpg_files:
            logging.error("No JPG files were prepared. Exiting.")
            return {'statusCode': 500, 'body': json.dumps('Error processing document: No JPG files prepared.')}

        results = []
        for index, s3_file in enumerate(jpg_files):
            logging.info(f"Processing file {index + 1} of {len(jpg_files)}: {s3_file}")
            result = process_single_file(s3_file, index)
            if result:
                results.append(result)
            else:
                logging.warning(f"No result for file: {s3_file}")

        if not results:
            logging.error("No results were processed. Exiting.")
            return {'statusCode': 500, 'body': json.dumps('Error processing document: No results processed.')}

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
                    if value:
                        combined_result[key] = value

        logging.info("Processing completed. Final result:")
        logging.info(json.dumps(combined_result, indent=2))

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"extraction_result_{timestamp}.json"
        s3_result_object_name = f"extraction_results/{result_filename}"
        save_result_to_s3(combined_result, s3_result_object_name)

        return {'statusCode': 200, 'body': json.dumps('Document processed successfully.')}
    except Exception as e:
        logging.error(f"Error processing document: {e}", exc_info=True)
        return {'statusCode': 500, 'body': json.dumps(f'Error processing document: {str(e)}')}

# Import these at the end to avoid circular imports
from src.document_preparation import prepare_document
from src.textract_api import analyze_document
from src.response_parser import parse_response
from src.document_specific_processing import process_checkboxes
from src.template_matching import match_template, log_matching_results
from src.post_processing import post_process
