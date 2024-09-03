import json
import os
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import logging

from src.document_preparation import prepare_document
from src.textract_api import analyze_document
from src.response_parser import parse_response
from src.document_specific_processing import process_checkboxes
from src.template_matching import match_template, log_matching_results
from src.post_processing import post_process

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize S3 client
s3_client = boto3.client('s3')

def process_single_file(s3_file, bucket):
    logging.info(f"Processing file: {s3_file}")
    response = analyze_document(s3_file, bucket)
    if not response:
        logging.error(f"Failed to analyze document: {s3_file}")
        return None

    parsed_kv, parsed_tables = parse_response(response)
    processed_kv = process_checkboxes(parsed_kv, response)
    matched_data = match_template(processed_kv, parsed_tables)
    log_matching_results(matched_data)
    final_result = post_process(matched_data)

    logging.info(f"Processed file: {s3_file}")
    return final_result

def lambda_handler(event, context):
    # Get the S3 bucket and key from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    logging.info(f"Processing file {key} from bucket {bucket}")

    # Download the PDF from S3
    local_pdf_path = '/tmp/document.pdf'
    s3_client.download_file(bucket, key, local_pdf_path)
    
    # Process the document
    jpg_files = prepare_document(local_pdf_path)
    logging.info(f"Prepared {len(jpg_files)} JPG files")

    results = []
    for jpg_file in jpg_files:
        s3_object_name = f"textract_input/{os.path.basename(jpg_file)}"
        s3_client.upload_file(jpg_file, bucket, s3_object_name)
        result = process_single_file(s3_object_name, bucket)
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
    
    # Save to S3
    s3_result_object_name = f"extraction_results/{result_filename}"
    try:
        s3_client.put_object(Body=json.dumps(combined_result, indent=2), Bucket=bucket, Key=s3_result_object_name)
        logging.info(f"Result saved to S3 as {bucket}/{s3_result_object_name}")
    except ClientError as e:
        logging.error(f"Error saving result to S3: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error processing document')
        }

    return {
        'statusCode': 200,
        'body': json.dumps('Document processed successfully')
    }