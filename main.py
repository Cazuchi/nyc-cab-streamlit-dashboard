import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import google.cloud.bigquery as bigquery

st.set_page_config(layout="wide", page_title="NYC Taxi Borough Comparison")

#Function definitions to pull data from the BigQuery table
@st.cache_data(ttl=3600)
def get_borough_kpis(borough: str) -> dict:
    client = bigquery.Client(project="cazuchi")

    query = f"""
    SELECT
        borough,
        COUNT(*) AS total_trips,
        ROUND(AVG(total_amount), 2) AS avg_total_cost_incl_tip,
        ROUND(AVG(total_amount) - AVG(tip_amount), 2) AS avg_total_cost_excl_tip,
        ROUND(AVG(tip_amount), 2) AS avg_tip_amount,
        ROUND(SAFE_DIVIDE(AVG(tip_amount), AVG(total_amount - tip_amount)), 4) AS tip_percentage,
        ROUND(AVG(passenger_count), 1) AS avg_passenger_count,
        ROUND(AVG(TIMESTAMP_DIFF(dropoff_datetime, pickup_datetime, SECOND) / 60.0), 2) AS avg_ride_duration,
        ROUND(AVG(CASE WHEN trip_distance > 0 AND trip_distance < 100 THEN trip_distance END) * 1.60934, 2) AS avg_trip_distance,
        ROUND(SAFE_DIVIDE(AVG(CASE WHEN trip_distance > 0 AND trip_distance < 100 THEN total_amount - tip_amount END), AVG(CASE WHEN trip_distance > 0 AND trip_distance < 100 THEN trip_distance END)  * 1.60934), 2) AS avg_cost_per_km,
        ROUND(SAFE_DIVIDE(AVG(total_amount - tip_amount), (AVG(TIMESTAMP_DIFF(dropoff_datetime, pickup_datetime, SECOND) / 60.0))), 2) AS avg_cost_per_minute,
        ROUND(SAFE_DIVIDE(AVG(CASE WHEN trip_distance > 0 AND trip_distance < 100 THEN tip_amount END), AVG(CASE WHEN trip_distance > 0 AND trip_distance < 100 THEN trip_distance END)  * 1.60934), 2) AS avg_tip_per_km,
        ROUND(SAFE_DIVIDE(AVG(tip_amount), (AVG(TIMESTAMP_DIFF(dropoff_datetime, pickup_datetime, SECOND) / 60.0))), 2) AS avg_tip_per_minute
    FROM cazuchi.nyc_taxi_data.yellow_cab_table
    WHERE pickup_datetime >= "2022-01-01"
        AND pickup_datetime < "2023-01-01"
        AND borough IS NOT NULL
        AND borough != "EWR"
        AND borough = "{borough}"
        AND TIMESTAMP_DIFF(dropoff_datetime, pickup_datetime, SECOND) >= 60.0
        AND total_amount > 0
        AND tip_amount >= 0
    GROUP By borough
    """

    return client.query(query).to_dataframe()

@st.cache_data(ttl=3600)
def get_borough_timeline_data(borough: str) -> dict:
    client = bigquery.Client(project="cazuchi")

    query = f"""
    WITH basic_table AS (
    SELECT
        TIMESTAMP_TRUNC(pickup_datetime, MONTH) AS month,
        SUM(CASE WHEN borough = "{borough}" THEN total_amount - tip_amount END) AS borough_net_revenue,
        SUM(CASE WHEN borough = "{borough}" THEN COALESCE(passenger_count, 0) END) AS borough_passenger_count
    FROM cazuchi.nyc_taxi_data.yellow_cab_table
    WHERE pickup_datetime >= "2022-01-01"
        AND pickup_datetime < "2023-01-01"
        AND borough IS NOT NULL
        AND borough != "EWR"
        AND borough = "{borough}"
        AND TIMESTAMP_DIFF(dropoff_datetime, pickup_datetime, SECOND) >= 60.0
        AND total_amount > 0
        AND tip_amount >= 0
    GROUP By TIMESTAMP_TRUNC(pickup_datetime, MONTH)
    ),
    aggregated_table AS (
    SELECT
        bt.month AS month,
        ROUND(SUM(bt.borough_net_revenue) OVER (ORDER BY bt.month), 2) AS borough_aggregated_revenue,
        SUM(bt.borough_passenger_count) OVER (ORDER BY bt.month) AS borough_aggregated_passenger_count,
    FROM basic_table bt
    ORDER BY bt.month
    )

    SELECT * FROM aggregated_table
    """

    return client.query(query).to_dataframe()

#Dashboard title and borough selection drop-downs
st.title("Comparing key metrics for the yellow NYC taxis across two select NYC boroughs:")
BOROUGHS = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    main_borough = st.selectbox("Select Main Borough", options=BOROUGHS, index=2) #Queens is set as the default for the main borough
with filter_col2:
    comp_borough = st.selectbox("Select Comparison Borough", options=BOROUGHS, index=3) #Bronx is set as the default for the comparison borough

#Pull data
main_data = get_borough_kpis(main_borough)
comp_data = get_borough_kpis(comp_borough)

main_data_timeline = get_borough_timeline_data(main_borough)
comp_data_timeline = get_borough_timeline_data(comp_borough)

#Build the KPI card sections of the dashboard
st.subheader("Financial metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    diff = main_data['avg_total_cost_incl_tip'].iloc[0] - comp_data['avg_total_cost_incl_tip'].iloc[0]
    st.metric(
        label="Avg total cost (incl. tip)", 
        value=f"{main_data['avg_total_cost_incl_tip'].iloc[0]:,.2f}", 
        delta=f"{'+$' if diff >= 0 else '-$'}{abs(diff):,.2f}",
        help="Compared to the comparison borough."
        )

with col2:
    diff = main_data['avg_total_cost_excl_tip'].iloc[0] - comp_data['avg_total_cost_excl_tip'].iloc[0]
    st.metric(
        label="Avg total cost (excl. tip)", 
        value=f"{main_data['avg_total_cost_excl_tip'].iloc[0]:,.2f}", 
        delta=f"{'+$' if diff >= 0 else '-$'}{abs(diff):,.2f}",
        help="Compared to the comparison borough."
        )

with col3:
    diff = main_data['avg_tip_amount'].iloc[0] - comp_data['avg_tip_amount'].iloc[0]
    st.metric(
        label="Avg tip amount", 
        value=f"{main_data['avg_tip_amount'].iloc[0]:,.2f}", 
        delta=f"{'+$' if diff >= 0 else '-$'}{abs(diff):,.2f}",
        help="Compared to the comparison borough."
        )

with col4:
    diff = main_data['tip_percentage'].iloc[0] - comp_data['tip_percentage'].iloc[0]
    st.metric(
        label="Avg tip percentage", 
        value=f"{main_data['tip_percentage'].iloc[0]:.1%}", 
        delta=f"{diff:+.1%}",
        help="Compared to the comparison borough."
        )

st.divider()
st.subheader("Trip metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    diff = main_data['total_trips'].iloc[0] - comp_data['total_trips'].iloc[0]
    st.metric(
        label="Total trips", 
        value=f"{main_data['total_trips'].iloc[0]:,}", 
        delta=f"{'+' if diff >= 0 else '-'}{abs(diff):,}",
        help="Compared to the comparison borough."
        )

with col2:
    diff = main_data['avg_passenger_count'].iloc[0] - comp_data['avg_passenger_count'].iloc[0]
    st.metric(
        label="Avg # of passengers", 
        value=f"{main_data['avg_passenger_count'].iloc[0]:,.1f}", 
        delta=f"{'+' if diff >= 0 else '-'}{abs(diff):,.1f}",
        help="Compared to the comparison borough."
        )

with col3:
    diff = main_data['avg_ride_duration'].iloc[0] - comp_data['avg_ride_duration'].iloc[0]
    st.metric(
        label="Avg ride duration", 
        value=f"{main_data['avg_ride_duration'].iloc[0]:,.2f} min.", 
        delta=f"{'+' if diff >= 0 else '-'}{abs(diff):,.2f} min.",
        help="Compared to the comparison borough."
        )

with col4:
    diff = main_data['avg_trip_distance'].iloc[0] - comp_data['avg_trip_distance'].iloc[0]
    st.metric(
        label="Avg trip distance", 
        value=f"{main_data['avg_trip_distance'].iloc[0]:,.2f} km.", 
        delta=f"{'+' if diff >= 0 else '-'}{abs(diff):,.2f} km.",
        help="Compared to the comparison borough."
        )

st.divider()

#Build the timeline section of the dashboard
col1, col2 = st.columns(2)

colors = {
    main_borough : "#636EFA",
    comp_borough : "#EF553B"
}

with col1:
    fig_rev = go.Figure()

    fig_rev.add_trace(go.Scatter(
        x=main_data_timeline['month'],
        y=main_data_timeline['borough_aggregated_revenue'],
        mode="lines+markers",
        name=main_borough,
        line=dict(color=colors[main_borough], width=3)
    ))

    fig_rev.add_trace(go.Scatter(
        x=comp_data_timeline['month'],
        y=comp_data_timeline['borough_aggregated_revenue'],
        mode="lines+markers",
        name=comp_borough,
        line=dict(color=colors[comp_borough], width=3)
    ))

    fig_rev.update_layout(
        title="Aggregated Monthly Net Revenue Excl. Tips",
        template="plotly_dark",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig_rev.update_yaxes(tickprefix="$", tickformat=",d")
    st.plotly_chart(fig_rev, use_container_width=True)

with col2:
    fig_pax = go.Figure()

    fig_pax.add_trace(go.Scatter(
        x=main_data_timeline['month'],
        y=main_data_timeline['borough_aggregated_passenger_count'],
        mode="lines+markers",
        name=main_borough,
        line=dict(color=colors[main_borough], width=3)
    ))

    fig_pax.add_trace(go.Scatter(
        x=comp_data_timeline['month'],
        y=comp_data_timeline['borough_aggregated_passenger_count'],
        mode="lines+markers",
        name=comp_borough,
        line=dict(color=colors[comp_borough], width=3)
    ))

    fig_pax.update_layout(
        title="Aggregated Monthly Passenger Counts",
        template="plotly_dark",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig_pax.update_yaxes(tickformat=",d")
    st.plotly_chart(fig_pax, use_container_width=True)