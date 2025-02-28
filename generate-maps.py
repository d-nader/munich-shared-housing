# Install needed libraries using:
# pip install -r requirements.txt

import plotly.express as px
import pandas as pd
import geopandas as gpd
import requests

# Load rental and population data
df_wg = pd.read_csv("data/df_wg_data.csv", encoding="utf-8-sig")  
df_pop = pd.read_csv("data/df_population.csv", encoding="utf-8-sig")

# Define university locations in Munich
universities = [
    {"name": "LMU Main Campus", "lat": 48.150288, "lon": 11.580735},  
    {"name": "TUM Main Campus", "lat": 48.147484, "lon": 11.567949},  
    {"name": "HM Main Campus", "lat": 48.152348, "lon": 11.550285},  
    {"name": "HM Pasing Campus", "lat": 48.137222, "lon": 11.450383},  
    {"name": "TUM University Hospital", "lat": 48.143593, "lon": 11.60133},  
    {"name": "LMU University Hospital", "lat": 48.112854, "lon": 11.472254},  
]
markers = pd.DataFrame(universities)

# Fetch GeoJSON data for Munich districts
geojson_url = "https://geoportal.muenchen.de/geoserver/gsm_wfs/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=gsm_wfs:vablock_stadtbezirke_opendata&outputFormat=application/json"  
response = requests.get(geojson_url)  
geojson_data = response.json()  

# Convert GeoJSON to a GeoDataFrame
gdf = gpd.GeoDataFrame.from_features(geojson_data["features"], crs="EPSG:25832").to_crs(epsg=4326)

# Standardize district naming so we can merge with other data
gdf["name"] = gdf["sb_nummer"] + " " + gdf["name"]  
gdf["name"] = gdf["name"].str.replace("-", " - ")  

# Function to create and save an interactive choropleth map
def choropleth(df, color_var, range_color, title, colorbar_title, filename):
    fig = px.choropleth(
        df,
        geojson=gdf,
        locations="district",
        featureidkey="properties.name",
        color=color_var,
        animation_frame="year",
        projection="mercator",
        range_color=range_color,
        color_continuous_scale="RdYlBu_r"
    )

    # Add university locations
    fig.add_scattergeo(
        lat=markers["lat"],
        lon=markers["lon"],
        text=markers["name"],
        mode="markers",
        marker=dict(size=7, color="black", symbol="triangle-down", opacity=1)  # No legend, just hover text
    )

    # Keep the slider but stop it from looping
    fig.update_layout(
        frames=[{"name": str(year), "data": []} for year in df["year"].unique()],  # Stops repeat animation
        title=title,
        title_x=0.5,
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        coloraxis_colorbar=dict(title=colorbar_title),
        height=500,
        width=700
    )

    # Save the interactive map as an HTML file
    fig.write_html(filename)

# Set output directory for maps
output_dir = "docs/maps/"

# Generate maps (saved as HTML in the output folder)
choropleth(df_wg, "median_sqm_rent", [30, 50], "Median Rent per Square Meter", "Euro/m²", f"{output_dir}munich_sqm-rent_map.html")
choropleth(df_wg, "median_rent", [500, 800], "Median Rent", "Euro", f"{output_dir}munich_rent_map.html")

# Exclude 2015 from the dataset before mapping
df_pop_mig = df_pop[df_pop["year"] != 2015]

choropleth(df_pop_mig, "migration_background", [15, 40], "Population with Migration Background", "Percent", f"{output_dir}munich_migration_map.html")
choropleth(df_pop, "benefit_recipients", [1, 6], "Social Benefit Recipients", "Percent", f"{output_dir}munich_benefit_map.html")
choropleth(df_pop, "households_children", [10, 25], "Households with Children", "Percent", f"{output_dir}munich_hh-children_map.html")
choropleth(df_pop, "residence_duration", [10, 16], "Average Residence Duration", "Years", f"{output_dir}munich_residence_map.html")
choropleth(df_pop, "average_age", [40, 45], "Average Age in the District", "Years", f"{output_dir}munich_age_map.html")

print("check your maps in 'docs/maps/' ;-)")
