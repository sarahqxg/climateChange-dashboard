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
@st.cache_data
def load_data():
    url = "https://ourworldindata.org/grapher/ghg-emissions-by-sector.csv"
    df = pd.read_csv(url)
    return df

gas = load_data()

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