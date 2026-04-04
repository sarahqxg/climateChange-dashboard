import streamlit as st
import pandas as pd
import plotly.express as px
import pycountry
import pycountry_convert as pc
import numpy as np
import random
import geopandas as gpd



# =========================
# LOAD DATA (Gas Emissions by Sector)
# =========================
@st.cache_data
def load_gas():
    path = "/Users/qianxiaogou/Desktop/uni/Y3/datavis/cw/data/ghg-emissions-by-sector.csv"
    df = pd.read_csv(path)
    df = df[df["Year"] >= 2000]

    return df

@st.cache_data
def load_co():
    path = "/Users/qianxiaogou/Desktop/uni/Y3/datavis/cw/data/co2.csv"
    df = pd.read_csv(path)
    df = df.rename(columns={"CO₂ emissions per capita": "co2"})
    df = df[df["Year"]>= 2000]
    return df

@st.cache_data
def load_dis():
    path = "/Users/qianxiaogou/Desktop/uni/Y3/datavis/cw/data/disaster.xlsx"
    df = pd.read_excel(path)

    # filter year

    return df

@st.cache_data
def load_temp():
    path = "/Users/qianxiaogou/Desktop/uni/Y3/datavis/cw/data/annual-temperature-anomalies.csv"
    df = pd.read_csv(path)

    # preprocess
    df = df.dropna(subset=["Temperature anomaly"])
    df = df[df["Code"].notna()]
    df = df[df["Year"] >= 2000]

    return df




# =========================
# GAS EMISSIONS
# COUNTRY → CONTINENT
# =========================
@st.cache_data
def prepare_emission_data(gas):
    exclude_cols = ["Entity", "Code", "Year"]
    emission_cols = [col for col in gas.columns if col not in exclude_cols]

    gas[emission_cols] = gas[emission_cols].apply(pd.to_numeric, errors='coerce')
    gas[emission_cols] = gas[emission_cols].fillna(0)

    # map continent
    def country_to_continent(country_name):
        try:
            country_code = pycountry.countries.lookup(country_name).alpha_2
            continent_code = pc.country_alpha2_to_continent_code(country_code)

            return {
                "AF": "Africa",
                "AS": "Asia",
                "EU": "Europe",
                "NA": "North America",
                "SA": "South America",
                "OC": "Oceania",
                "AQ": "Antarctica"
            }.get(continent_code)
        except:
            return None

    gas["Continent"] = gas["Entity"].apply(country_to_continent)

    regions = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania", "World"]
    gas = gas[~gas["Entity"].isin(regions)]
    gas = gas.dropna(subset=["Continent"])

    continent_df = gas.groupby(
        ["Continent", "Year"], as_index=False
    )[emission_cols].sum()

    return continent_df, emission_cols

# =========================
# PLOT
# =========================
def emission_pie_chart(continent_df, emission_cols, continent, year, threshold):
    subset = continent_df[
        (continent_df["Continent"] == continent) &
        (continent_df["Year"] == year)
    ]

    if subset.empty:
        return None

    source_data = subset[emission_cols].iloc[0]
    total = source_data.sum()

    small = source_data[source_data / total < threshold]
    large = source_data[source_data / total >= threshold]

    final_data = large.copy()

    if len(small) > 0:
        final_data["Others"] = small.sum()

    final_data.index = [i.replace("-", " ").title() for i in final_data.index]

    fig = px.pie(
        names=final_data.index,
        values=final_data.values,
        title=f"{continent} Emissions by Source ({year})",
        hole=0.4
    )

    return fig


# =========================
# UI
# =========================
def section_emission_pie(gas):
    st.subheader("Emission Source Breakdown")

    # prepare data
    continent_df, emission_cols = prepare_emission_data(gas)

    # 🎛️ UI CONTROLS (only here!)
    continent = st.selectbox(
        "Select Continent",
        sorted(continent_df["Continent"].unique())
    )

    year = st.slider(
        "Select Year",
        int(continent_df["Year"].min()),
        int(continent_df["Year"].max()),
        int(continent_df["Year"].max())
    )

    threshold = st.slider(
        "Group small values into 'Others' (%)",
        0.0, 0.1, 0.02
    )

    # pie chart
    fig = emission_pie_chart(
        continent_df,
        emission_cols,
        continent,
        year,
        threshold
    )

    if fig is None:
        st.warning("No data available")
    else:
        st.plotly_chart(fig, use_container_width=True)



# =========================
# CO2
# =========================

def co2_line_chart(co, countries):
    filtered = co[co["Entity"].isin(countries)]

    fig = px.line(
        filtered,
        x="Year",
        y="co2",
        color="Entity",
        title="CO₂ Emissions Per Capita Comparison"
    )

    return fig
# =========================
# UI
# =========================
def section_co2(co):
    st.subheader("CO₂ Emissions Trend")

    st.markdown("""
    Carbon dioxide (CO₂) is the most significant greenhouse gas emitted by human activities.
    This chart shows how CO₂ emissions per capita have evolved over time across countries.
    """)

    countries = st.multiselect(
        "Select countries",
        sorted(co["Entity"].unique()),
        default=["Indonesia", "Malaysia"]
    )

    fig = co2_line_chart(co, countries)
    st.plotly_chart(fig, use_container_width=True)




# =========================
# LOAD DATA
# =========================


# =========================
# FILTER DATA
# =========================
#temp = temp[temp["Year"] == selected_year]

# =========================
# ANOMALY MAP
# =========================
def temperature_map_chart(temp):
    fig = px.choropleth(
        temp,
        locations="Code",
        color="Temperature anomaly",
        hover_name="Entity",
        color_continuous_scale="RdBu_r",
        range_color=(-1, 2),
        animation_frame="Year"
    )
    fig.update_layout(
        coloraxis_colorbar=dict(title="Temp Anomaly (°C)")
    )

    return fig

# =========================
# UI
# =========================
def section_temperature(temp):
    st.subheader(" Global Temperature Anomaly")

    st.markdown("""
    Global temperatures have increased over time, reflecting the impact of climate change.
    
    This map shows how temperature anomalies vary across years.
    """)

    fig = temperature_map_chart(temp)
    st.plotly_chart(fig, use_container_width=True)




#st.set_page_config(layout="wide")

#st.title("🌍 Global Natural Disaster Dashboard (2000–2025)")

# =========================
# DATA PREPROCESSING
# =========================
@st.cache_data
def prepare_disaster_data(disaster):
    import random

    # -------------------------
    # CLEAN BASIC STRUCTURE
    # -------------------------
    disaster.columns = disaster.columns.str.strip()

    disaster = disaster[[
        "Country","ISO","Disaster Type",
        "Latitude","Longitude","Start Year",
        "Total Affected","Total Deaths"
    ]]

    disaster = disaster.rename(columns={"Start Year": "Year"})

    # -------------------------
    # TYPE CLEANING
    # -------------------------
    disaster["Year"] = pd.to_numeric(disaster["Year"], errors="coerce")
    disaster = disaster.dropna(subset=["Year"])
    disaster["Year"] = disaster["Year"].astype(int)

    disaster["Total Affected"] = disaster["Total Affected"].fillna(0)
    disaster["Total Deaths"] = disaster["Total Deaths"].fillna(0)
    disaster["Disaster Type"] = disaster["Disaster Type"].astype(str)

    # -------------------------
    # FIX MISSING COORDINATES
    # -------------------------
    url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
    world = gpd.read_file(url)
    # compute centroids
    world["centroid"] = world.geometry.centroid
    world["centroid_lat"] = world.centroid.y
    world["centroid_lon"] = world.centroid.x

    # keep only needed columns
    centroids = world[["ISO_A3", "centroid_lat", "centroid_lon"]]    
    centroids = centroids.rename(columns={"ISO_A3": "ISO"})
    disaster = disaster.merge(centroids, on="ISO", how="left")
    def jitter_coords(lat, lon, scale=2):
        return (
            lat + random.uniform(-scale, scale),
            lon + random.uniform(-scale, scale)
        )

    random.seed(42)

    lat_fixed = []
    lon_fixed = []

    for _, row in disaster.iterrows():
        # use real coordinates if available
        if pd.notna(row["Latitude"]) and pd.notna(row["Longitude"]):
            lat_fixed.append(row["Latitude"])
            lon_fixed.append(row["Longitude"])
        else:
            # fallback to centroid + jitter
            if pd.notna(row["centroid_lat"]) and pd.notna(row["centroid_lon"]):
                lat, lon = jitter_coords(row["centroid_lat"], row["centroid_lon"])
            else:
                lat = random.uniform(-60, 80)
                lon = random.uniform(-180, 180)

            lat_fixed.append(lat)
            lon_fixed.append(lon)

    # overwrite columns
    disaster["Latitude"] = lat_fixed
    disaster["Longitude"] = lon_fixed
    disaster = disaster.drop(columns=["centroid_lat", "centroid_lon"])
    # -------------------------
    # FEATURE ENGINEERING
    # -------------------------
    disaster["Affected_scaled"] = np.log1p(disaster["Total Affected"]) + 1

    # filter years
    disaster = disaster[(disaster["Year"] >= 2000) & (disaster["Year"] <= 2025)]

    # -------------------------
    # AGGREGATION
    # -------------------------
    dia_count = (
        disaster.groupby(["Year", "Disaster Type"])
        .size()
        .reset_index(name="Count")
    )

    disaster_total = (
        dia_count.groupby("Year")["Count"]
        .sum()
        .reset_index()
    )

    return disaster, dia_count, disaster_total


# =========================
# CHART
# =========================
def disaster_map_chart(df):
    df = df.sort_values("Year")

    fig = px.scatter_geo(
        df,
        lat="Latitude",
        lon="Longitude",
        color="Disaster Type",
        size="Affected_scaled",
        size_max=40,
        hover_name="Country",
        hover_data={
            "Year": True,
            "Total Deaths": True,
            "Total Affected": True
        },
        animation_frame="Year",
        category_orders={"Year": sorted(df["Year"].unique())},
        projection="natural earth",
        color_discrete_sequence=px.colors.qualitative.Set1
    )

    fig.update_geos(showcountries=True, showcoastlines=True)

    # smoother animation
    if fig.layout.updatemenus:
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 300

    return fig


def disaster_bar_chart(dia_count, disaster_total):
    fig = px.bar(
        dia_count,
        x="Disaster Type",
        y="Count",
        color="Disaster Type",
        animation_frame="Year",
        color_discrete_sequence=px.colors.qualitative.Set1
    )

    # -------------------------
    # ADD TOTAL ANNOTATION (SAFE)
    # -------------------------
    for frame in fig.frames:
        year = int(frame.name)

        total_row = disaster_total[disaster_total["Year"] == year]

        if not total_row.empty:
            total = total_row["Count"].values[0]
        else:
            total = 0

        frame.layout = dict(
            annotations=[
                dict(
                    text=f"Total: {total}",
                    x=0.95,
                    y=0.95,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    bgcolor="white"
                )
            ]
        )

    return fig

# =========================
# UI
# =========================
def section_disaster(disaster):
    st.subheader("Climate Disasters")

    st.markdown("""
    Rising global temperatures contribute to more frequent and severe 
    natural disasters such as floods, storms, and droughts.

    This section shows both the geographic distribution and trends of disasters.
    """)

    # prepare data
    disaster, dia_count, disaster_total = prepare_disaster_data(disaster)

    # 🎛️ sidebar filter
    st.sidebar.header("Disaster Filters")

    selected_types = st.sidebar.multiselect(
        "Disaster Type",
        options=sorted(disaster["Disaster Type"].unique()),
        default=disaster["Disaster Type"].unique(),
        key="disaster_filter"
    )

    disaster_filtered = disaster[
        disaster["Disaster Type"].isin(selected_types)
    ]
    
    dia_count_filtered = dia_count[
    dia_count["Disaster Type"].isin(selected_types)
    ]

    disaster_total_filtered = (
    dia_count_filtered
    .groupby("Year")["Count"]
    .sum()
    .reset_index()
    )
    st.plotly_chart(
        disaster_map_chart(disaster_filtered),
        use_container_width=True
    )
    st.markdown(
        "Total amount of disasters and detailed breakdown by each type are shown in the bar chart below."
    )
    st.plotly_chart(
        disaster_bar_chart(dia_count_filtered, disaster_total_filtered),
        use_container_width=True
    )


# =========================
# DASHBOARD
# =========================

# =========================
# PAGE CONFIG 
# =========================
st.set_page_config(
    page_title="Climate Change Dashboard - Qian Ying 20593898",
    layout="wide"
)
# =========================
# TITLE
# =========================
st.title(" The Modern Climate Crisis: 2000–Present")
st.markdown("""
An interactive dashboard exploring climate change through temperature trends,
greenhouse gas emissions, and natural disasters.

Use the tabs to navigate different aspects of climate analysis.
""")
st.divider()

# =========================
# LOAD DATA
# =========================
gas = load_gas()
co = load_co()
disaster = load_dis()
temp = load_temp()

# =========================
# TABS (MAIN STRUCTURE)
# =========================
tab1, tab2, tab3 = st.tabs([
    "Temperature",
    "Emissions",
    "Disasters"
])

with tab1:
    section_temperature(temp)
with tab2:
    section_emission_pie(gas)
    section_co2(co)
with tab3:
    section_disaster(disaster)
