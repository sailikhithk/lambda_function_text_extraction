import os
import json
from datetime import datetime
from src.document_preparation import prepare_document
from src.textract_api import analyze_document
from src.response_parser import parse_response
from src.document_specific_processing import process_checkboxes
from src.template_matching import match_template, log_matching_results
from src.post_processing import post_process
from config import BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, REGION_NAME
import boto3
from botocore.exceptions import ClientError
import logging
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def save_intermediate_result(data, filename):
    temp_dir = os.path.join(os.getcwd(), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, filename)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    logging.info(f"Intermediate result saved: {file_path}")

def clean_temp_directory():
    temp_dir = os.path.join(os.getcwd(), 'temp')
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        logging.info(f"Cleaned temporary directory: {temp_dir}")
    os.makedirs(temp_dir)
    logging.info(f"Created new temporary directory: {temp_dir}")

def upload_to_s3(file_path, bucket, object_name=None):
    if object_name is None:
        object_name = os.path.basename(file_path)

    s3_client = boto3.client('s3',
                             aws_access_key_id=AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                             region_name=REGION_NAME)

    try:
        s3_client.upload_file(file_path, bucket, object_name)
        logging.info(f"File uploaded successfully to {bucket}/{object_name}")
        return True
    except ClientError as e:
        logging.error(f"Error uploading file to S3: {e}")
        return False

def process_single_file(s3_file, file_index):
    logging.info(f"Processing file: {s3_file}")
    response = analyze_document(s3_file, BUCKET)
    if not response:
        logging.error(f"Failed to analyze document: {s3_file}")
        return None

    parsed_kv, parsed_tables = parse_response(response)
    
    # Save extracted data
    extracted_data = {
        "key_value_pairs": parsed_kv,
        "tables": parsed_tables
    }
    save_intermediate_result(extracted_data, f"extracted_data_{file_index}.json")

    processed_kv = process_checkboxes(parsed_kv, response)
    matched_data = match_template(processed_kv, parsed_tables)

    # Save matched data
    save_intermediate_result(matched_data, f"matched_data_{file_index}.json")

    log_matching_results(matched_data)

    final_result = post_process(matched_data)

    logging.info(f"Processed file: {s3_file}")
    return final_result

def save_result_locally(result, filename):
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)
    logging.info(f"Result saved locally as {filename}")

def save_result_to_s3(result, bucket, object_name):
    s3_client = boto3.client('s3',
                             aws_access_key_id=AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                             region_name=REGION_NAME)
    try:
        s3_client.put_object(Body=json.dumps(result, indent=2), Bucket=bucket, Key=object_name)
        logging.info(f"Result saved to S3 as {bucket}/{object_name}")
        return True
    except ClientError as e:
        logging.error(f"Error saving result to S3: {e}")
        return False

def main():
    clean_temp_directory()

    pdf_file = "sample_gas_statement.pdf"
    jpg_files = prepare_document(pdf_file)
    logging.info(f"Prepared {len(jpg_files)} JPG files")

    s3_files = []
    for jpg_file in jpg_files:
        s3_object_name = f"textract_input/{os.path.basename(jpg_file)}"
        if upload_to_s3(jpg_file, BUCKET, s3_object_name):
            s3_files.append(s3_object_name)

    if not s3_files:
        logging.error("No files were uploaded to S3. Exiting.")
        return

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
    
    # Save locally
    save_result_locally(combined_result, result_filename)
    
    # Save to S3
    s3_result_object_name = f"extraction_results/{result_filename}"
    save_result_to_s3(combined_result, BUCKET, s3_result_object_name)

if __name__ == "__main__":
    main()