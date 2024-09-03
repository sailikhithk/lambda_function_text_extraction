import boto3
from PyPDF2 import PdfReader
from PIL import Image
import io
import os
import tempfile
import logging

# Initialize S3 client
s3_client = boto3.client('s3', region_name=os.getenv('REGION_NAME'))

def prepare_document(pdf_content, s3_bucket):
    """
    Prepares the document by converting PDF pages to JPGs and uploading them to S3.
    :param pdf_content: Raw bytes of the PDF file
    :param s3_bucket: S3 bucket name to upload the JPG files
    :return: List of S3 paths to the uploaded JPG files
    """
    try:
        logging.info(f"Starting document preparation for S3 bucket: {s3_bucket}")
        
        # Initialize PdfReader
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        total_pages = len(pdf_reader.pages)
        logging.info(f"Total pages found in PDF: {total_pages}")

        jpg_files = []

        # Create a temporary directory for storing JPG files
        with tempfile.TemporaryDirectory() as temp_dir:
            logging.info(f"Temporary directory created at: {temp_dir}")

            for page_num in range(total_pages):
                logging.info(f"Processing page {page_num + 1}/{total_pages}")

                # Extract page
                page = pdf_reader.pages[page_num]
                
                # Convert PDF page to image
                images = page.images
                if images:
                    logging.info(f"Images found on page {page_num + 1}, processing first image")
                    # If the page contains images, use the first one
                    image = images[0]
                    img = Image.open(io.BytesIO(image.data))
                else:
                    logging.warning(f"No images found on page {page_num + 1}, creating a blank image")
                    # If no image is found, create a blank white image
                    img = Image.new('RGB', (612, 792), color='white')
                
                # Convert image to RGB if it's in RGBA mode
                if img.mode == 'RGBA':
                    logging.info(f"Converting RGBA image to RGB for page {page_num + 1}")
                    img = img.convert('RGB')
                
                # Save the image as JPG
                jpg_path = os.path.join(temp_dir, f"page_{page_num}.jpg")
                img.save(jpg_path, 'JPEG')
                logging.info(f"Saved JPG for page {page_num + 1} at {jpg_path}")

                # Upload the JPG file to S3
                jpg_s3_key = f"textract_input/page_{page_num}.jpg"
                with open(jpg_path, 'rb') as jpg_file:
                    s3_client.put_object(Body=jpg_file, Bucket=s3_bucket, Key=jpg_s3_key)
                logging.info(f"Uploaded JPG to S3: {s3_bucket}/{jpg_s3_key}")
                jpg_files.append(jpg_s3_key)

        logging.info(f"Document preparation completed. {len(jpg_files)} pages processed and uploaded.")
        return jpg_files

    except Exception as e:
        logging.error(f"Error processing document: {e}", exc_info=True)
        return []
