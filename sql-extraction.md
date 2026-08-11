This is the SQL statement I used to extract the data for the dashboard from the publicly available NYC Taxi dataset:

```sql
CREATE OR REPLACE TABLE `cazuchi.nyc_taxi_data.yellow_cab_table` --OR REPLACE added because I've used it both to generate a small test dataset and a larger production dataset
PARTITION BY DATE(pickup_datetime) --Partition by pickup_datetime to cut down on how many rows have to be scanned for a given query
CLUSTER BY borough --Cluster by borough to cut down on how many rows have to be scanned for a given query
OPTIONS (
    require_partition_filter = true
) AS
SELECT
  yel.pickup_datetime,
  yel.dropoff_datetime,
  yel.passenger_count,
  yel.trip_distance,
  yel.total_amount,
  yel.tip_amount,
  geo.borough
FROM `bigquery-public-data.new_york_taxi_trips.tlc_yellow_trips_*` yel
LEFT JOIN `bigquery-public-data.new_york_taxi_trips.taxi_zone_geom` geo ON yel.pickup_location_id = geo.zone_id --Borough names are kept in a separate table and have to be merged in
WHERE yel._TABLE_SUFFIX BETWEEN '2022' AND '2022';
```