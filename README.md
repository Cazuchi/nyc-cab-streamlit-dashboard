# **Streamlit dashboard made with the NYX taxi dataset**  
I used SQL to extract a subset of the NYC yellow taxi dataset and stored that in a BigQuery table. The Streamlit dashboard compares select KPIs across two boroughs of the user's choosing.  

The data is cached for 3,600 seconds to avoid unnecessary re-pulls and the data pulls are separated so that changing a value in one drop-down only updates the subset of the total dataset for that borough.  

### **Dashboard link**
[You can see and interact with the dashboard here.](https://nyc-cab-streamlit-dashboard-562594843791.europe-west1.run.app/)  

Here is a preview of the dashboard:  
![Alt text](/imgs/preview.png)    

### **Tech stack**
* Streamlit
* Bigquery
* Cloud Run
* Python
* SQL