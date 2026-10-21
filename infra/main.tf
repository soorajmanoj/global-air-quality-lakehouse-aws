resource "random_id" "bucket_suffix" {
    byte_length = 4
}

#1. Raw S3 Bucket
resource "aws_s3_bucket" "raw" {
    bucket = "${var.project_name}-raw-${var.environment}-${random_id.bucket_suffix.hex}"
    force_destroy = true
}

#2. Curated S3 Bucket
resource "aws_s3_bucket" "curated" {
    bucket = "${var.project_name}-curated-${var.environment}-${random_id.bucket_suffix.hex}"
    force_destroy = true
}

#3. Athena Query Results S3 Bucket
resource "aws_s3_bucket" "athena_results" {
    bucket = "${var.project_name}-athena-results-${var.environment}-${random_id.bucket_suffix.hex}"
    force_destroy = true
}

#Glue Catalog Database
resource "aws_glue_catalog_database" "air_quality_db" {
    name = replace("${var.project_name}_db_${var.environment}", "-", "_")
    description = "Glue Catalog Database for Global Air Quality Lakehouse"
}