-- The query used to pull the calculated metrics for the KPI cards in the Streamlit dashboard

SELECT
  borough,
  COUNT(*) AS total_trips,
  ROUND(AVG(total_amount), 2) AS avg_total_cost_incl_tip,
  ROUND(AVG(total_amount) - AVG(tip_amount), 2) AS avg_total_cost_excl_tip,
  ROUND(AVG(tip_amount), 2) AS avg_tip_amount,
  ROUND(SAFE_DIVIDE(AVG(tip_amount), AVG(total_amount - tip_amount)), 4) AS tip_percentage,
  ROUND(AVG(passenger_count), 1) AS avg_passenger_count,
  ROUND(AVG(TIMESTAMP_DIFF(dropoff_datetime, pickup_datetime, SECOND) / 60.0), 2) AS avg_ride_duration,
  ROUND(AVG(CASE WHEN trip_distance > 0 THEN trip_distance END) * 1.60934, 2) AS avg_trip_distance,
  ROUND(SAFE_DIVIDE(AVG(CASE WHEN trip_distance > 0 THEN total_amount - tip_amount END), AVG(CASE WHEN trip_distance > 0 THEN trip_distance END)  * 1.60934), 2) AS avg_cost_per_km,
  ROUND(SAFE_DIVIDE(AVG(total_amount - tip_amount), (AVG(TIMESTAMP_DIFF(dropoff_datetime, pickup_datetime, SECOND) / 60.0))), 2) AS avg_cost_per_minute,
  ROUND(SAFE_DIVIDE(AVG(CASE WHEN trip_distance > 0 THEN tip_amount END), AVG(CASE WHEN trip_distance > 0 THEN trip_distance END)  * 1.60934), 2) AS avg_tip_per_km,
  ROUND(SAFE_DIVIDE(AVG(tip_amount), (AVG(TIMESTAMP_DIFF(dropoff_datetime, pickup_datetime, SECOND) / 60.0))), 2) AS avg_tip_per_minute
FROM cazuchi.nyc_taxi_data.yellow_cab_table
WHERE pickup_datetime >= "2022-01-01"
  AND pickup_datetime < "2023-01-01"
  AND borough IS NOT NULL
  AND borough != "EWR"
  AND TIMESTAMP_DIFF(dropoff_datetime, pickup_datetime, SECOND) >= 60.0
  AND total_amount > 0
  AND tip_amount >= 0
GROUP By borough