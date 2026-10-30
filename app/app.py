import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Kepler Candidate Triage", layout="centered")

st.markdown("""
<style>
.stApp { background: #000000; }
[data-testid="stHeader"] { display: none; }
.block-container { max-width: 860px; padding-top: 1rem; }

.stApp, .stApp p, .stApp label, .stApp li, .stApp h2,
.stApp [data-testid="stMarkdownContainer"] {
    font-family: Verdana, Arial, Helvetica, sans-serif;
}
.stApp p, .stApp label, .stApp li { color: #FFFFFF; font-size: 14px; }

.banner { background: #000080; border: 3px solid #FFFF00; padding: 14px 16px; margin-bottom: 14px; }
.banner-title { color: #FFFFFF !important; font-size: 26px; font-weight: bold; }
.banner-sub { color: #FFFF00 !important; font-size: 13px; margin-top: 4px; }

.note { background: #FFFF99; border: 2px solid #FFFFFF; padding: 8px 12px;
        font-size: 13px; color: #000000 !important; }

.stApp h2 { font-size: 18px; font-weight: bold; color: #FFFF00;
            border-bottom: 2px solid #FFFF00; padding: 0 0 2px 0; margin-top: 24px; }

.tbl { border-collapse: collapse; width: 100%; font-size: 12px; }
.tbl th { background: #0000CC; color: #FFFFFF; border: 1px solid #FFFFFF;
          padding: 3px 6px; text-align: left; }
.tbl td { background: #000000; color: #FFFFFF; border: 1px solid #999999; padding: 3px 6px; }
.tbl tr:nth-child(even) td { background: #161616; }
.tbl td.high { background: #FFFF00 !important; color: #000000 !important; font-weight: bold; }
.tbl td.medium { background: #FFCC66 !important; color: #000000 !important; }

[data-testid="stDownloadButton"] button {
    border-radius: 0; border: 2px outset #C0C0C0; background: #C0C0C0;
    color: #000000; font-family: Verdana, Arial, sans-serif;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="banner">
<div class="banner-title">Kepler Candidate Triage</div>
<div class="banner-sub">Unresolved Kepler candidates, ranked by estimated chance of being a real planet</div>
</div>
<div class="note">
<b>Please note:</b> probabilities come from a model trained on resolved objects.
Candidates have weaker signals on average, so use the scores as a ranking guide, not confirmed odds.
</div>
""", unsafe_allow_html=True)


def band(p):
    if p > 0.9:
        return "High"
    if p > 0.5:
        return "Medium"
    return "Low"


def make_table(df):
    html = '<table class="tbl"><tr><th>' + str(df.index.name or "") + "</th>"
    for col in df.columns:
        html += "<th>" + str(col) + "</th>"
    html += "</tr>"
    for index_value, row in df.iterrows():
        html += "<tr><td>" + str(index_value) + "</td>"
        for col, value in row.items():
            css_class = ""
            if col == "Band":
                css_class = ' class="' + str(value).lower() + '"'
            html += "<td" + css_class + ">" + str(value) + "</td>"
        html += "</tr>"
    html += "</table>"
    return html


@st.cache_data
def load_ranking():
    path = Path(__file__).parent / "candidate_ranking.csv"
    df = pd.read_csv(path)
    df["Band"] = df["planet_probability"].apply(band)
    df["planet_probability"] = df["planet_probability"].round(3)
    df = df.rename(columns={
        "kepoi_name": "KOI name",
        "kepid": "Star ID",
        "koi_model_snr": "Signal-to-noise",
        "koi_period": "Period (days)",
        "koi_prad": "Radius (Earth radii)",
        "planet_probability": "Probability",
        "rank": "Rank",
    })
    return df.set_index("Rank")


ranking = load_ranking()

st.header("How the candidates are spread")
counts = ranking["Band"].value_counts().rename("Objects").to_frame()
counts.index.name = "Band"
st.markdown(make_table(counts), unsafe_allow_html=True)

st.header("Your shortlist")
chosen = st.multiselect("Bands to show", ["High", "Medium", "Low"], default=["High", "Medium"])
k = st.slider("How many candidates can your team follow up?", 10, 500, 100)

shortlist = ranking[ranking["Band"].isin(chosen)].head(k)

st.write("Showing", len(shortlist), "candidates")
st.markdown(make_table(shortlist), unsafe_allow_html=True)

st.download_button(
    "Download this list as CSV",
    shortlist.to_csv(),
    file_name="top_candidates.csv",
)

st.header("How to read the bands")
st.write(
    "High: on resolved objects, about 99% of objects scored above 0.9 were real planets. "
    "Medium: the model was overconfident here, so these need the most human judgment. "
    "Low: unlikely to be planets."
)