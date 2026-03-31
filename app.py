import streamlit as st
import pandas as pd
import plotly.express as px
import pycountry
import pycountry_convert as pc
import ssl

# 🔥 FIX SSL ISSUE
ssl._create_default_https_context = ssl._create_unverified_context

# =========================
# LOAD DATA (cache for speed)
# =========================
gaspath = "/Users/qianxiaogou/Desktop/uni/Y3/datavis/cw/data/ghg-emissions-by-sector.csv"
gas = pd.read_csv(gaspath)
gas = gas[gas["Year"] >= 2000]

# =========================
# CLEAN DATA
# =========================
exclude_cols = ["Entity", "Code", "Year"]
emission_cols = [col for col in gas.columns if col not in exclude_cols]

gas[emission_cols] = gas[emission_cols].apply(pd.to_numeric, errors='coerce')
gas[emission_cols] = gas[emission_cols].fillna(0)

# =========================
# COUNTRY → CONTINENT
# =========================
@st.cache_data
def map_continent(df):
    def country_to_continent(country_name):
        try:
            country_code = pycountry.countries.lookup(country_name).alpha_2
            continent_code = pc.country_alpha2_to_continent_code(country_code)

            continent_map = {
                "AF": "Africa",
                "AS": "Asia",
                "EU": "Europe",
                "NA": "North America",
                "SA": "South America",
                "OC": "Oceania",
                "AQ": "Antarctica"
            }
            return continent_map.get(continent_code)
        except:
            return None

    df["Continent"] = df["Entity"].apply(country_to_continent)
    return df

gas = map_continent(gas)

# remove regions
regions = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania", "World"]
gas = gas[~gas["Entity"].isin(regions)]
gas = gas.dropna(subset=["Continent"])

# =========================
# GROUP BY CONTINENT
# =========================
continent_df = gas.groupby(
    ["Continent", "Year"], as_index=False
)[emission_cols].sum()

# =========================
# 🎛️ UI
# =========================
st.title("🌍 Emission Source Breakdown Dashboard")

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

# =========================
# FILTER
# =========================
subset = continent_df[
    (continent_df["Continent"] == continent) &
    (continent_df["Year"] == year)
]

if subset.empty:
    st.warning("No data available")
else:
    source_data = subset[emission_cols].iloc[0]

    total = source_data.sum()

    small = source_data[source_data / total < threshold]
    large = source_data[source_data / total >= threshold]

    final_data = large.copy()

    if len(small) > 0:
        final_data["Others"] = small.sum()

    # nicer labels
    final_data.index = [i.replace("-", " ").title() for i in final_data.index]

    # =========================
    # 📊 PIE CHART
    # =========================
    fig = px.pie(
        names=final_data.index,
        values=final_data.values,
        title=f"{continent} Emissions by Source ({year})",
        hole=0.4
    )

    st.plotly_chart(fig, width="stretch")

co2 = "/Users/qianxiaogou/Desktop/uni/Y3/datavis/cw/data/co2.csv"
co = pd.read_csv(co2)
co = co.rename(columns={"CO₂ emissions per capita": "co2"})
co = co[co["Year"]>= 2000]

countries = st.multiselect(
    "Select countries",
    sorted(co["Entity"].unique()),
    default=["Indonesia", "Malaysia"]  # optional
)

filtered = co[co["Entity"].isin(countries)]

fig = px.line(
    filtered,
    x="Year",
    y="co2",
    color="Entity",  # 🔥 key
    title="CO₂ Emissions Per Capita Comparison"
)

st.plotly_chart(fig)



# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Climate Dashboard", layout="wide")

st.title("🌍 Global Temperature Anomaly Over Time")

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    anomalyTemp = "/Users/qianxiaogou/Desktop/uni/Y3/datavis/cw/data/annual-temperature-anomalies.csv"
    df = pd.read_csv(anomalyTemp)

    # preprocess
    df = df.dropna(subset=["Temperature anomaly"])
    df = df[df["Code"].notna()]
    df = df[df["Year"] >= 2000]

    return df

df = load_data()

# =========================
# SIDEBAR FILTER
# =========================
years = sorted(df["Year"].unique())

selected_year = st.slider(
    "Select Year",
    min_value=min(years),
    max_value=max(years),
    value=min(years)
)


# =========================
# FILTER DATA
# =========================
#df = df[df["Year"] == selected_year]

# =========================
# CREATE MAP
# =========================
fig = px.choropleth(
    df,
    locations="Code",
    color="Temperature anomaly",
    hover_name="Entity",
    color_continuous_scale="RdBu_r",
    range_color=(-1, 2),
    title=f"🌡️ Temperature Anomaly in {selected_year}",
    animation_frame="Year"
)

fig.update_layout(
    title={"x": 0.5},
    coloraxis_colorbar=dict(title="Temp Anomaly (°C)")
)

# =========================
# DISPLAY
# =========================
st.plotly_chart(fig, use_container_width=True)




import pandas as pd
import numpy as np
import plotly.express as px
import random

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random

st.set_page_config(layout="wide")

st.title("🌍 Global Natural Disaster Dashboard (2000–2025)")

# =========================
# 1. LOAD DATA (CACHE)
# =========================
@st.cache_data
def load_data():
    disasterP = "/Users/qianxiaogou/Desktop/uni/Y3/datavis/cw/data/disaster.xlsx"
    df = pd.read_excel(disasterP)

    # filter year

    return df

df = load_data()

# =========================
# 2. CLEAN COLUMNS
# =========================
df.columns = df.columns.str.strip()

df = df[[
    "Country",
    "ISO",
    "Disaster Type",
    "Latitude",
    "Longitude",
    "Start Year",
    "Total Affected",
    "Total Deaths"
]]

df = df.rename(columns={"Start Year": "Year"})

# =========================
# 3. CLEAN DATA
# =========================
df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
df = df.dropna(subset=["Year"])
df["Year"] = df["Year"].astype(int)

df = df.sort_values("Year")
df["Year"] = pd.Categorical(
    df["Year"],
    categories=sorted(df["Year"].unique()),
    ordered=True
)

df["Total Affected"] = df["Total Affected"].fillna(0)
df["Total Deaths"] = df["Total Deaths"].fillna(0)
df["Disaster Type"] = df["Disaster Type"].astype(str)

df["Affected_scaled"] = np.log1p(df["Total Affected"])
df = df[(df["Year"] >= 2000) & (df["Year"] <= 2025)]

# =========================
# 4. AGG DATA
# =========================
df_count = (
    df.groupby(["Year", "Disaster Type"])
    .size()
    .reset_index(name="Count")
)

df_total = df_count.groupby("Year")["Count"].sum().reset_index()

# =========================
# 5. COUNTRY CENTROIDS
# =========================
country_centroids = {
    "USA": (39, -98), "CHN": (35, 103), "IND": (21, 78),
    "BRA": (-10, -55), "RUS": (60, 90), "AUS": (-25, 133),
    "IDN": (-5, 120), "CAN": (56, -106), "ARG": (-34, -64),
    "ZAF": (-30, 25), "MEX": (23, -102), "JPN": (36, 138),
    "DEU": (51, 10), "FRA": (46, 2), "GBR": (55, -3)
}

def jitter_coords(lat, lon, scale=2):
    return (
        lat + random.uniform(-scale, scale),
        lon + random.uniform(-scale, scale)
    )

# =========================
# 6. FIX COORDINATES
# =========================
lat_fixed = []
lon_fixed = []

for _, row in df.iterrows():
    if pd.notna(row["Latitude"]) and pd.notna(row["Longitude"]):
        lat_fixed.append(row["Latitude"])
        lon_fixed.append(row["Longitude"])
    else:
        iso = row["ISO"]
        if iso in country_centroids:
            base_lat, base_lon = country_centroids[iso]
            lat, lon = jitter_coords(base_lat, base_lon)
        else:
            lat, lon = None, None

        lat_fixed.append(lat)
        lon_fixed.append(lon)

df["Latitude_fixed"] = lat_fixed
df["Longitude_fixed"] = lon_fixed
df = df.dropna(subset=["Latitude_fixed", "Longitude_fixed"])

# =========================
# 🎛️ SIDEBAR FILTER
# =========================
st.sidebar.header("Filters")

selected_types = st.sidebar.multiselect(
    "Disaster Type",
    options=sorted(df["Disaster Type"].unique()),
    default=df["Disaster Type"].unique()
)

df = df[df["Disaster Type"].isin(selected_types)]

# =========================
# 7. MAP
# =========================
st.subheader("🌍 Disaster Events Map")

fig = px.scatter_geo(
    df,
    lat="Latitude_fixed",
    lon="Longitude_fixed",
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
    projection="natural earth",
    color_discrete_sequence=px.colors.qualitative.Set1
)

fig.update_geos(showcountries=True, showcoastlines=True)

# smoother animation
fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 300

st.plotly_chart(fig, use_container_width=True)

# =========================
# 8. BAR CHART
# =========================
st.subheader("📊 Disaster Count by Type")

fig_bar = px.bar(
    df_count,
    x="Disaster Type",
    y="Count",
    color="Disaster Type",
    animation_frame="Year",
    color_discrete_sequence=px.colors.qualitative.Set1
)

# add total annotation
for frame in fig_bar.frames:
    year = int(frame.name)
    total = df_total[df_total["Year"] == year]["Count"].values[0]

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

st.plotly_chart(fig_bar, use_container_width=True)