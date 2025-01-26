import pandas as pd
import folium
from sklearn.cluster import KMeans
from folium.plugins import MarkerCluster
import requests
from io import BytesIO
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px

# Load data from Excel URL with error handling
def load_data(url):
    try:
        st.write(f"Loading data from {url}...")
        response = requests.get(url)
        if response.status_code == 200:
            lat_long_data = pd.read_excel(BytesIO(response.content), sheet_name="lat long", engine='openpyxl')
            measurement_data = pd.read_excel(BytesIO(response.content), sheet_name="measurement data", engine='openpyxl')
            
            # Merge data on school_id_giga
            merged_data = pd.merge(
                lat_long_data,
                measurement_data,
                left_on="school_id_giga",
                right_on="school_id_giga",
                how="inner"
            )
            
            # Strip any extra spaces from column names
            merged_data.columns = merged_data.columns.str.strip()
            st.write("Data loaded successfully")
            return merged_data
        else:
            st.write(f"Failed to load data. Status code: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.write(f"Error loading data: {e}")
        return pd.DataFrame()

# Perform clustering to find data center location
def find_data_center(df, n_clusters=1):
    if df.empty:
        st.write("Dataframe is empty, skipping clustering")
        return None
    kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(df[["latitude", "longitude"]])
    return kmeans.cluster_centers_

# Plot the map with markers and save as HTML
def plot_map(df, center):
    if df.empty:
        st.write("Dataframe is empty, skipping map plotting")
        return None
    
    map = folium.Map(location=[center[0][0], center[0][1]], zoom_start=10)
    marker_cluster = MarkerCluster().add_to(map)
    
    # Add school locations
    for idx, row in df.iterrows():
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=(
                f"School Name: {row.get('school_name', 'N/A')}<br>"
                f"Download Speed: {row['download_speed']} Mbps<br>"
                f"Upload Speed: {row['upload_speed']} Mbps<br>"
                f"Latency: {row['latency']} ms"
            ),
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(marker_cluster)
    
    # Add data center location
    folium.Marker(
        location=[center[0][0], center[0][1]],
        popup="Proposed Data Center",
        icon=folium.Icon(color="red", icon="cloud")
    ).add_to(map)
    
    # Save the map as an HTML file
    map.save("map.html")
    return "map.html"

# Calculate the impact of data center on latency and bandwidth
def calculate_impact(df, center):
    if df.empty:
        st.write("Dataframe is empty, skipping impact calculation")
        return None
    avg_latency_before = df['latency'].mean()
    avg_download_before = df['download_speed'].mean()
    avg_upload_before = df['upload_speed'].mean()
    
    # Assuming the data center reduces latency and increases bandwidth by 20%
    latency_reduction = avg_latency_before * 0.8
    download_increase = avg_download_before * 1.2
    upload_increase = avg_upload_before * 1.2
    
    # Return the new statistics
    return latency_reduction, download_increase, upload_increase, avg_latency_before, avg_download_before, avg_upload_before

# Display the 3D bar chart for impact
def display_3d_bar_chart(latency_reduction, download_increase, upload_increase, avg_latency_before, avg_download_before, avg_upload_before):
    if latency_reduction is None:
        st.write("No data to display in the chart.")
        return
    
    # Create data for plotting
    metrics = ['Latency (ms)', 'Download Speed (Mbps)', 'Upload Speed (Mbps)']
    before = [avg_latency_before, avg_download_before, avg_upload_before]
    after = [latency_reduction, download_increase, upload_increase]

    impact_data = pd.DataFrame({
        'Metric': metrics,
        'Before': before,
        'After': after
    })

    # Create a 3D bar chart using Plotly
    fig = px.bar(
        impact_data,
        x='Metric',
        y=['Before', 'After'],
        barmode='group',
        title="Impact of Data Center on Latency and Bandwidth",
        labels={"value": "Speed / Latency", "Metric": "Metric"},
        height=400
    )

    # Display the chart in the Streamlit app
    st.plotly_chart(fig)

# Main function to run the application
def main():
    url = "https://huggingface.co/spaces/engralimalik/lace/resolve/main/data%20barbados.xlsx"  # URL of your Excel file
    df = load_data(url)
    
    if df.empty:
        st.write("No data to process, exiting application.")
        return
    
    # Find the data center location using clustering
    center = find_data_center(df)
    if center is None:
        st.write("Could not find data center, exiting application.")
        return
    
    # Create the map and save it as an HTML file
    map_file = plot_map(df, center)
    
    # Embed the map in the Streamlit app using st.components.v1.html
    if map_file:
        components.html(open(map_file, 'r').read(), height=600)
    
    # Calculate the impact of adding the data center
    latency_reduction, download_increase, upload_increase, avg_latency_before, avg_download_before, avg_upload_before = calculate_impact(df, center)
    if latency_reduction is not None:
        display_3d_bar_chart(latency_reduction, download_increase, upload_increase, avg_latency_before, avg_download_before, avg_upload_before)

if __name__ == "__main__":
    main()
