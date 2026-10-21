import boto3
import time

DATABASE_NAME = "global_air_quality_db_dev"
TABLE_NAME = "air_quality_silver"
LOCATION_ID = "2143"

def get_bucket_by_keyword(s3_client, keyword):
    response = s3_client.list_buckets()
    for bucket in response['Buckets']:
        if keyword in bucket['Name']:
            return bucket['Name']
    raise ValueError(f"Could not find bucket matching keyword: {keyword}")

def run_athena_statement(athena_client, query, output_location, description):
    print(f"Running: {description}...")
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': DATABASE_NAME},
        ResultConfiguration={'OutputLocation': output_location}
    )
    query_id = response['QueryExecutionId']
    
    while True:
        status_res = athena_client.get_query_execution(QueryExecutionId=query_id)
        state = status_res['QueryExecution']['Status']['State']
        if state == 'SUCCEEDED':
            print(f"Success: {description}")
            break
        elif state in ['FAILED', 'CANCELLED']:
            reason = status_res['QueryExecution']['Status'].get('StateChangeReason', 'Unknown reason')
            raise Exception(f"Query failed ({description}): {reason}")
        time.sleep(2)

def register_table():
    s3_client = boto3.client('s3', region_name='us-east-1')
    athena_client = boto3.client('athena', region_name='us-east-1')
    
    curated_bucket = get_bucket_by_keyword(s3_client, "-curated-dev-")
    athena_results_bucket = get_bucket_by_keyword(s3_client, "-athena-results-dev-")
    
    table_location = f"s3://{curated_bucket}/silver/openaq/locationid={LOCATION_ID}/"
    output_location = f"s3://{athena_results_bucket}/athena-results/"

    try:
        # Step 1: Drop existing table to clear old schema
        drop_query = f"DROP TABLE IF EXISTS {DATABASE_NAME}.{TABLE_NAME};"
        run_athena_statement(athena_client, drop_query, output_location, "Drop existing table")

        # Step 2: Create external table with corrected schema (bigint for location_id)
        create_query = f"""
        CREATE EXTERNAL TABLE {DATABASE_NAME}.{TABLE_NAME} (
            location_id BIGINT,
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
        TBLPROPERTIES ('parquet.compression'='SNAPPY');
        """
        run_athena_statement(athena_client, create_query, output_location, "Create external table")
        
        print("Table successfully re-registered with updated schema!")
        
    except Exception as e:
        print(f"Error registering table: {e}")

if __name__ == "__main__":
    register_table()