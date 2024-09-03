import PyPDF2
import boto3
from botocore.exceptions import ClientError
import json
import os
from dotenv import load_load_dotenv
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, REGION_NAME, BUCKET


# Set up AWS credentials
aws_access_key_id = AWS_ACCESS_KEY_ID
aws_secret_access_key = AWS_SECRET_ACCESS_KEY
region_name = REGION_NAME
bucket_name = BUCKET

def extract_second_page(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        if len(reader.pages) < 2:
            print("The PDF does not have a second page.")
            return None
        
        page = reader.pages[1]
        return page.extract_text()

def upload_to_s3(file_content, object_name):
    s3_client = boto3.client('s3', 
                             aws_access_key_id=aws_access_key_id,
                             aws_secret_access_key=aws_secret_access_key,
                             region_name=region_name)
    try:
        s3_client.put_object(Body=file_content, Bucket=bucket_name, Key=object_name)
        print(f"File uploaded successfully to {bucket_name}/{object_name}")
    except ClientError as e:
        print(f"Error uploading file to S3: {e}")
        return False
    return True

def analyze_document(object_name):
    textract_client = boto3.client('textract', 
                                   aws_access_key_id=aws_access_key_id,
                                   aws_secret_access_key=aws_secret_access_key,
                                   region_name=region_name)
    
    try:
        response = textract_client.analyze_document(
            Document={'S3Object': {'Bucket': bucket_name, 'Name': object_name}},
            FeatureTypes=["FORMS", "TABLES"]
        )
        return response
    except ClientError as e:
        print(f"Error analyzing document: {e}")
        return None

def extract_key_value_pairs(response):
    key_value_pairs = {}
    for block in response['Blocks']:
        if block['BlockType'] == 'KEY_VALUE_SET':
            if 'KEY' in block['EntityTypes']:
                key = block['Text']
                for relationship in block['Relationships']:
                    if relationship['Type'] == 'VALUE':
                        for related_block in response['Blocks']:
                            if related_block['Id'] == relationship['Ids'][0]:
                                value = related_block['Text']
                                key_value_pairs[key] = value
    return key_value_pairs

def main():
    pdf_path = 'sample_gas_statement.pdf'
    second_page_content = extract_second_page(pdf_path)
    
    if second_page_content:
        object_name = 'contract_statement_page2.txt'
        if upload_to_s3(second_page_content, object_name):
            response = analyze_document(object_name)
            if response:
                key_value_pairs = extract_key_value_pairs(response)
                print("Extracted Key-Value Pairs:")
                print(json.dumps(key_value_pairs, indent=2))
            else:
                print("Failed to analyze the document.")
        else:
            print("Failed to upload the file to S3.")
    else:
        print("Failed to extract the second page content.")

if __name__ == "__main__":
    main()