# Use the official AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# Copy your requirements file into the image
COPY requirements.txt .

# Install required packages to a directory named 'lambda_package' without caching
RUN pip install --target /lambda_package -r requirements.txt --no-cache-dir

# Copy the contents to the output directory for easy access
CMD cp -r /lambda_package/* /out
