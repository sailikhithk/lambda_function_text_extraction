import os
import boto3
from pdf2image import convert_from_bytes
from io import BytesIO
from config import BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

def prepare_document(s3_pdf_key):
    # Initialize S3 client
    s3 = boto3.client('s3', 
                      aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                      region_name=AWS_REGION)

    # Download PDF from S3
    response = s3.get_object(Bucket=BUCKET, Key=s3_pdf_key)
    pdf_content = response['Body'].read()

    filename = os.path.splitext(os.path.basename(s3_pdf_key))[0]

    # Convert PDF to images
    images = convert_from_bytes(pdf_content)

    s3_files = []
    for i, image in enumerate(images):
        # Save image to memory buffer
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        # Upload directly to S3
        s3_key = f'textract_input/{filename}_page_{i+1}.jpg'
        s3.put_object(Bucket=BUCKET, Key=s3_key, Body=img_byte_arr)
        s3_files.append(s3_key)
    
    print(f"Uploaded {len(s3_files)} files to S3")
    return s3_files