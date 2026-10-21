import boto3
import time

DATABASE_NAME = "global_air_quality_db_dev"
TABLE_NAME = "air_quality_silver"

def run_query():
    s3_client = boto3.client('s3', region_name='us-east-1')
    athena_client = boto3.client('athena', region_name='us-east-1')
    
    # Dynamically find the athena results bucket
    response = s3_client.list_buckets()
    athena_results_bucket = next(b['Name'] for b in response['Buckets'] if '-athena-results-dev-' in b['Name'])
    output_location = f"s3://{athena_results_bucket}/athena-results/"

    query = f"SELECT * FROM {TABLE_NAME} LIMIT 5;"
    print(f"Running query: {query}")

    # Start the query execution
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': DATABASE_NAME},
        ResultConfiguration={'OutputLocation': output_location}
    )
    
    query_execution_id = response['QueryExecutionId']
    print(f"Query submitted. Execution ID: {query_execution_id}")
    
    # Poll for completion
    while True:
        status_response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        state = status_response['QueryExecution']['Status']['State']
        
        if state == 'SUCCEEDED':
            print("Query succeeded! Fetching results...\n")
            break
        elif state in ['FAILED', 'CANCELLED']:
            reason = status_response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown reason')
            raise Exception(f"Query failed: {reason}")
        
        time.sleep(2)
        
    # Get the results
    results_response = athena_client.get_query_results(QueryExecutionId=query_execution_id)
    
    # Print column headers
    cols = [col['Name'] for col in results_response['ResultSet']['ResultSetMetadata']['ColumnInfo']]
    print(" | ".join(cols))
    print("-" * 80)
    
    # Print rows
    rows = results_response['ResultSet']['Rows'][1:] # Skip header row in results
    for row in rows:
        vals = [field.get('VarCharValue', '') for field in row['Data']]
        print(" | ".join(vals))

if __name__ == "__main__":
    run_query()