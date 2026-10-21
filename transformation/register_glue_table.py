import os
import boto3
import time

DATABASE_NAME = "global_air_quality_db_dev"
TABLE_NAME = "air_quality_silver"
LOCATION_ID = "2143"

def get_bucket_by_keyword(s3_client, keyword):
    """Dynamically finds a bucket containing a specific keyword."""
    response = s3_client.list_buckets()
    for bucket in response['Buckets']:
        if keyword in bucket['Name']:
            return bucket['Name']
    raise ValueError(f"Bucket containing keyword '{keyword}' not found.")

def register_table():
    s3_client = boto3.client('s3', region_name='us-east-1')
    athena_client = boto3.client('athena', region_name='us-east-1')

    curated_bucket = get_bucket_by_keyword(s3_client, '-curated-dev-')
    athena_results_bucket = get_bucket_by_keyword(s3_client, '-athena-results-dev-')

    # S3 path where Silver Parquet partitions are stored
    table_location = f"s3://{curated_bucket}/silver/openaq/locationid={LOCATION_ID}/"
    output_location = f"s3://{athena_results_bucket}/athena-results/"

    # SQL DDL statement to register the external Parquet table 
    # Adjust column definitions to match extracted OpenAQ CSV columns
    ddl_query = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {DATABASE_NAME}.{TABLE_NAME} (
        location_id STRING,
        location STRING,
        city STRING,
        country STRING,
        utc STRING,
        local STRING,
        parameter STRING,
        value DOUBLE,
        unit STRING,
        latitude DOUBLE,
        longitude DOUBLE,
        ingestion_date STRING
    )
    STORED AS PARQUET
    LOCATION '{table_location}'
    TBLPROPERTIES ('parquet.compress'='SNAPPY');
    """

    print(f"Registering table {DATABASE_NAME}.{TABLE_NAME} pointing to {table_location}...")

    try:
        response = athena_client.start_query_execution(
            QueryString=ddl_query,
            QueryExecutionContext={'Database': DATABASE_NAME},
            ResultConfiguration={'OutputLocation': output_location}
        )

        query_execution_id = response['QueryExecutionId']
        print(f"Query submitted. Execution ID: {query_execution_id}")

        # Poll for query completion
        while True:
            status_response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
            state = status_response['QueryExecution']['Status']['State']
            
            if state == 'SUCCEEDED':
                print("Table registered successfully in the AWS Glue Catalog.")
                break
            elif state in ['FAILED', 'CANCELLED']:
                reason = status_response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown reason')
                raise Exception(f"Athena DDL query failed: {reason}")

            time.sleep(2)  # Wait before polling again

    except Exception as e:
        print(f"Error during table registration: {e}")

if __name__ == "__main__":
    register_table()