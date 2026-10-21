import os
import boto3
import pandas as pd
import io

# Configuration parameters matching Bronze test file
LOCATION_ID = "2143"
YEAR = "2026"
MONTH = "07"
DAY = "20260715"

def get_bucket_by_keyword(s3_client, keyword):
    """Dynamically finds a bucket containing a specific keyword."""
    response = s3_client.list_buckets()
    for bucket in response['Buckets']:
        if keyword in bucket['Name']:
            return bucket['Name']
    raise ValueError(f"Bucket containing keyword '{keyword}' not found.")

def transform_bronze_to_silver():
    s3_client = boto3.client('s3', region_name='us-east-1')

    raw_bucket = get_bucket_by_keyword(s3_client, '-raw-dev-')
    curated_bucket = get_bucket_by_keyword(s3_client, '-curated-dev-')

    source_key = f"bronze/openaq/locationid={LOCATION_ID}/year={YEAR}/month={MONTH}/location-{LOCATION_ID}-{DAY}.csv.gz"

    print(f"Reading from s3://{raw_bucket}/{source_key}...")

    try:
        # 1. Download and read gzipped CSV into Pandas DataFrame
        obj = s3_client.get_object(Bucket=raw_bucket, Key=source_key)
        df = pd.read_csv(io.BytesIO(obj['Body'].read()), compression='gzip')

        print(f"Data read successfully. Number of rows: {len(df)}")

        # 2. Basic Data Cleaning & Standardization
        # Standardize column names (lowercase and replace spaces with underscores)
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]

        # Drop completely empty rows or handle basic nulls if needed
        df.dropna(how='all')

        # Ensure timestamp fields are parsed
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')

        # Add metadat/partition tracking columns
        df['ingestion_date'] = f"{YEAR}-{MONTH}-{DAY}"

        # 3. Convert DataFrame to Parquet format in memory
        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, engine='pyarrow', index=False)
        parquet_buffer.seek(0)

        # 4. Write Parquet file to the curated S3 bucket with partitioning structure
        dest_key = f"silver/openaq/locationid={LOCATION_ID}/year={YEAR}/month={MONTH}/data.parquet"

        print(f"Writing Parquet to s3://{curated_bucket}/{dest_key}...")
        s3_client.put_object(
            Bucket=curated_bucket,
            Key=dest_key,
            Body=parquet_buffer.getvalue()
        )

        print("Successfully transformed and saved data to Silver layer.")

    except Exception as e:
        print(f"Error during transformation: {e}")
        
if __name__ == "__main__":
    transform_bronze_to_silver()