import boto3
import pandas as pd
import io

DATABASE_NAME = "global_air_quality_db_dev"
GOLD_TABLE_NAME = "air_quality_gold"
LOCATION_ID = "2143"

def get_bucket_by_keyword(s3_client, keyword):
    response = s3_client.list_buckets()
    for bucket in response['Buckets']:
        if keyword in bucket['Name']:
            return bucket['Name']
    raise ValueError(f"Could not find bucket matching keyword: {keyword}")

def transform_gold():
    s3_client = boto3.client('s3', region_name='us-east-1')
    curated_bucket = get_bucket_by_keyword(s3_client, "-curated-dev-")
    
    # 1. Read the Silver Parquet data from S3
    prefix = f"silver/openaq/locationid={LOCATION_ID}/"
    print(f"Reading Silver data from s3://{curated_bucket}/{prefix}...")
    
    response = s3_client.list_objects_v2(Bucket=curated_bucket, Prefix=prefix)
    if 'Contents' not in response:
        raise Exception(f"No Silver data found at {prefix}")
        
    # Find the parquet file
    parquet_keys = [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.parquet')]
    if not parquet_keys:
        raise Exception("No Parquet files found in Silver partition.")
        
    # Read all matching Parquet files into a single Pandas DataFrame
    dfs = []
    for key in parquet_keys:
        obj = s3_client.get_object(Bucket=curated_bucket, Key=key)
        df = pd.read_parquet(io.BytesIO(obj['Body'].read()))
        dfs.append(df)
        
    silver_df = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(silver_df)} rows from Silver layer.")

    # 2. Derive date safely (fallback to ingestion_date if utc is missing or null)
    if 'utc' in silver_df.columns and not silver_df['utc'].dropna().empty:
        silver_df['date'] = pd.to_datetime(silver_df['utc'], errors='coerce').dt.date.astype(str)
        
    # If date conversion failed or utc column didn't have valid entries, use ingestion_date
    if 'date' not in silver_df.columns or silver_df['date'].isna().all():
        print("Falling back to 'ingestion_date' for aggregation grouping..")
        silver_df['date'] = silver_df['ingestion_date']

    # 3. Aggregate into Gold Layer: Daily Average Pollutant Levels
    group_cols = [col for col in ['location_id', 'location', 'city', 'country', 'parameter', 'unit', 'date'] if col in silver_df.columns]
    gold_df = silver_df.groupby(group_cols, as_index=False).agg(
        avg_value=('value', 'mean'),
        min_value=('value', 'min'),
        max_value=('value', 'max'),
        sample_count=('value', 'count')
    )

    print("\nCalculated Gold Layer Aggregations:")
    print(gold_df.head())

    # 3. Write Gold Parquet back to S3
    output_prefix = f"gold/openaq/locationid={LOCATION_ID}/"
    output_buffer = io.BytesIO()
    gold_df.to_parquet(output_buffer, index=False, engine='pyarrow', compression='snappy')
    output_buffer.seek(0)
    
    gold_s3_key = f"{output_prefix}daily_aggregates.parquet"
    s3_client.put_object(Bucket=curated_bucket, Key=gold_s3_key, Body=output_buffer.getvalue())
    print(f"\nGold layer data successfully written to s3://{curated_bucket}/{gold_s3_key}")

if __name__ == "__main__":
    transform_gold()