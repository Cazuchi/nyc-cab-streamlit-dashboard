-- The query used to pull timeseries graphs for the Streamlit dashboard

WITH basic_table AS (
  SELECT
    TIMESTAMP_TRUNC(pickup_datetime, MONTH) AS month,
    SUM(CASE WHEN borough = "Brooklyn" THEN total_amount - tip_amount END) AS borough_a_net_revenue,
    SUM(CASE WHEN borough = "Bronx" THEN total_amount - tip_amount END) AS borough_b_net_revenue,
    SUM(CASE WHEN borough = "Brooklyn" THEN COALESCE(passenger_count, 0) END) AS borough_a_passenger_count,
    SUM(CASE WHEN borough = "Bronx" THEN COALESCE(passenger_count, 0) END) AS borough_b_passenger_count
  FROM cazuchi.nyc_taxi_data.yellow_cab_table
  WHERE pickup_datetime >= "2022-01-01"
    AND pickup_datetime < "2023-01-01"
    AND borough IS NOT NULL
    AND borough != "EWR"
    AND (borough = "Brooklyn" OR borough = "Bronx")
    AND TIMESTAMP_DIFF(dropoff_datetime, pickup_datetime, SECOND) >= 60.0
    AND total_amount > 0
    AND tip_amount >= 0
  GROUP By TIMESTAMP_TRUNC(pickup_datetime, MONTH)
),
aggregated_table AS (
  SELECT
    bt.month AS month,
    ROUND(SUM(bt.borough_a_net_revenue) OVER (ORDER BY bt.month), 2) AS borough_a_aggregated_revenue,
    ROUND(SUM(bt.borough_b_net_revenue) OVER (ORDER BY bt.month), 2) AS borough_b_aggregated_revenue,
    SUM(bt.borough_a_passenger_count) OVER (ORDER BY bt.month) AS borough_a_aggregated_passenger_count,
    SUM(bt.borough_b_passenger_count) OVER (ORDER BY bt.month) AS borough_b_aggregated_passenger_count
  FROM basic_table bt
  ORDER BY bt.month
)

SELECT * FROM aggregated_table