import os
import boto3
from botocore import UNSIGNED
from botocore.config import Config

# Configuration parameters
PUBLIC_BUCKET = "openaq-data-archive"
LOCATION_ID = "2143"
YEAR = "2026"
MONTH = "07"
DAY = "20260715"

def get_bronze_bucket_name(s3_client):
    """Helper to dynamically find the provisioned raw bucket name from AWS S3."""
    response = s3_client.list_buckets()
    for bucket in response['Buckets']:
        if "-raw-dev-" in bucket['Name']:
            return bucket['Name']
    raise ValueError("Provisioned raw bucket not found")

def ingest_file():
    # Unauthenticated S3 client for public OpenAQ bucket
    public_s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED), region_name='us-east-1')

    # Authenticated S3 client for the private lakehouse
    private_s3 = boto3.client('s3', region_name='us-east-1')

    bronze_bucket = get_bronze_bucket_name(private_s3)

    source_key = f"records/csv.gz/locationid={LOCATION_ID}/year={YEAR}/month={MONTH}/location-{LOCATION_ID}-{DAY}.csv.gz"
    dest_key = f"bronze/openaq/locationid={LOCATION_ID}/year={YEAR}/month={MONTH}/location-{LOCATION_ID}-{DAY}.csv.gz"

    print(f"Copying s3://{PUBLIC_BUCKET}/{source_key} to s3://{bronze_bucket}/{dest_key}...")

    # Copy object server-side using streaming/download-upload pattern to avoid downloading the entire file to local storage
    try:
        obj = public_s3.get_object(Bucket=PUBLIC_BUCKET, Key=source_key)
        private_s3.put_object(
            Bucket=bronze_bucket,
            Key=dest_key,
            Body=obj['Body'].read()
        )
        print("Successfully ingested sample file to the bronze bucket.")
    except Exception as e:
        print(f"Error during ingestion: {e}")

if __name__ == "__main__":
    ingest_file()