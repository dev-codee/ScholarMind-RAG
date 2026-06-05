import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

def upload_to_s3(file_path: str, object_name: str) -> bool:
    """
    Uploads a file to an AWS S3 bucket.
    """
    bucket_name = os.environ.get("AWS_S3_BUCKET")
    if not bucket_name:
        print("AWS_S3_BUCKET environment variable not set. Skipping S3 upload.")
        return False

    # Initialize S3 client based on environment variables
    # Requires AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION
    s3_client = boto3.client('s3')

    try:
        print(f"Uploading {object_name} to S3 bucket {bucket_name}...")
        s3_client.upload_file(file_path, bucket_name, object_name)
        print(f"Successfully uploaded {object_name} to S3.")
        return True
    except FileNotFoundError:
        print("The file was not found.")
        return False
    except NoCredentialsError:
        print("AWS credentials not available.")
        return False
    except ClientError as e:
        print(f"Failed to upload to S3: {e}")
        return False
