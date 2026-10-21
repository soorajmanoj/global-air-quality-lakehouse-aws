# OpenAQ Dataset Profile

## Source Architecture
- **Source Bucket:** `s3://openaq-data-archive/`
- **Format:** Gzipped CSV (`.csv.gz`)
- **Partitioning Strategy:** Hive-partitioned by `locationid=ID/year=YYYY/month=MM/`
- **Granularity:** Hourly sensor readings (Narrow format: one row per sensor reading)

## Sample Schema Fields
| Column Name | Inferred Data Type | Description |
| :--- | :--- | :--- |
| `location_id` | Integer | Unique identifier for the monitoring station |
| `sensors_id` | Integer | Unique identifier for the specific sensor instrument |
| `location` | String | Human-readable station name |
| `datetime` | Timestamp (with TZ) | ISO-8601 formatted timestamp of the reading |
| `lat` | Float / String | Latitude coordinate |
| `lon` | Float / String | Longitude coordinate |
| `parameter` | String | Pollutant measured (e.g., pm10, pm25, no2) |
| `units` | String | Measurement unit (e.g., µg/m³) |
| `value` | Float | Recorded measurement value |
