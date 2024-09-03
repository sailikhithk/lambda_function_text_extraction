import os
import boto3
from PyPDF2 import PdfReader
from pdf2jpg import pdf2jpg
from config import BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

def prepare_document(pdf_file):
    # Use /tmp for temporary storage in Lambda
    outputfolder = os.path.join("/tmp", "pdf_pages")
    os.makedirs(outputfolder, exist_ok=True)

    filename = os.path.splitext(os.path.basename(pdf_file))[0]

    # Convert PDF to JPG
    result = pdf2jpg.convert_pdf2jpg(pdf_file, outputfolder, pages="ALL")

    # Get JPG files
    jpgfolder = [x[0] for x in os.walk(outputfolder)][1]
    jpgfiles = [os.path.join(jpgfolder, entry) for entry in os.listdir(jpgfolder)]
    jpgfiles.sort()

    # Upload to S3
    s3 = boto3.client('s3', 
                      aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                      region_name=REGION_NAME)

    for jpgfile in jpgfiles:
        jpgfilename = os.path.basename(jpgfile)
        s3.upload_file(jpgfile, BUCKET, f'{filename}/{jpgfilename}')
    
    print(f"jpg files", jpgfiles)
    return jpgfiles
