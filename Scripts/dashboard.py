"""Streamlit dashboard for the CORDIS opportunity and CTIS trial datasets."""

from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Life Science Market Opportunity",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner=False)
def load_source_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    consur = pd.read_csv("../data/data_clean/CordisDatabase_clean.csv")
    trials = pd.read_csv("../data/data_clean/TrialsDatabase_clean.csv")
    trial_countries = pd.read_csv("../data/data_clean/TrialCountry_clean.csv")
    cordis_opportunities = pd.read_csv("../data/data_clean/CordisOpportunities_clean.csv")
    return consur, trials, trial_countries, cordis_opportunities


(
    CONSUR_CANDIDATES,
    TRIALS_CANDIDATES,
    TRIAL_COUNTRIES_CANDIDATES,
    CORDIS_OPPORTUNITIES_CANDIDATES,
) = load_source_data()


ACTIVITY_LABELS = {
    "HES": "Higher / secondary education",
    "PRC": "Private company",
    "REC": "Research organisation",
    "PUB": "Public body",
    "OTH": "Other",
}

# Fixed color assignments so the same category/activity type always renders
# the same color across the pie chart and the per-year stacked bar -- Plotly's
# default sequential assignment depends on each dataframe's own row order, so
# without a fixed map the same label can land on a different color per chart.
CATEGORY_COLORS = {
    "Genomics / Molecular Biology": "#2CA02C",
    "Oncology": "#2878B5",
    "Diagnostics / Biomarkers": "#C77800",
    "Digital Health / Bioinformatics": "#8250A0",
    "Pharma / Biotech": "#D62728",
    "Cell / Advanced Therapies": "#17BECF",
    "Proteomics / Multi-omics": "#BCBD22",
    "MedTech / Medical Device": "#E377C2",
    "Automation": "#9E9E9E",
    "Other": "#CCCCCC",
}
ACTIVITY_TYPE_COLORS = {
    "Higher / secondary education": "#2878B5",
    "Private company": "#136F63",
    "Research organisation": "#C77800",
    "Public body": "#8250A0",
    "Other": "#9E9E9E",
    "Unknown": "#CCCCCC",
}

OPPORTUNITY_TIERS = ["High", "Medium", "Small"]


@st.cache_data(show_spinner=False)
def clean_consur(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.loc[:, ~df.columns.str.startswith("Unnamed:")]
    for column in ("totalCostOrg", "totalCostProj", "ecContribution"):
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)
    for column in ("startDate", "endDate"):
        df[column] = pd.to_datetime(df[column], errors="coerce")
    for column in ("country", "period", "status", "activityType", "name", "title"):
        df[column] = df[column].astype("string").str.strip()
    return df


@st.cache_data(show_spinner=False)
def clean_trials(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.loc[:, ~df.columns.str.startswith("Unnamed:")]
    for column in ("Decision_date", "Start_date", "End_date"):
        df[column] = pd.to_datetime(df[column], errors="coerce")
    df["decision_year"] = pd.to_numeric(df["decision_year"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def clean_cordis_opportunities(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.loc[:, ~df.columns.str.startswith("Unnamed:")]
    df["totalCostProj"] = pd.to_numeric(df["totalCostProj"], errors="coerce").fillna(0)
    for column in ("title", "category", "coordinator_name", "coordinator_country", "status"):
        df[column] = df[column].astype("string").str.strip()
    return df


def european_number(formatted: str) -> str:
    """Swap US-style separators (1,234.5) for European ones (1.234,5)."""
    return formatted.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def euro(value: float) -> str:
    """Format large euro values compactly, European number format."""
    value = float(value or 0)
    if abs(value) >= 1_000_000_000:
        return f"€{european_number(f'{value / 1_000_000_000:,.1f}')}B"
    if abs(value) >= 1_000_000:
        return f"€{european_number(f'{value / 1_000_000:,.1f}')}M"
    if abs(value) >= 1_000:
        return f"€{european_number(f'{value / 1_000:,.1f}')}K"
    return f"€{european_number(f'{value:,.0f}')}"


def integer(value: float) -> str:
    """Format a count with European-style (period) thousands separators."""
    return european_number(f"{int(value):,}")


def multiselect_filter(
    frame: pd.DataFrame, column: str, selected: list[str]
) -> pd.DataFrame:
    """Filter a frame only when values have been selected."""
    if not selected or column not in frame:
        return frame
    return frame[frame[column].isin(selected)]


def horizontal_bar(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    x_label: str,
    color: str = "#136F63",
    text: str | None = None,
):
    """Create a consistently styled horizontal bar chart."""
    chart_data = data.sort_values(x, ascending=True).copy()
    text_col = None
    right_margin = 35
    if text is not None:
        text_col = "_text_label"
        if pd.api.types.is_numeric_dtype(chart_data[text]):
            chart_data[text_col] = chart_data[text].map(integer)
        else:
            chart_data[text_col] = chart_data[text]
        # Widen the right margin for longer labels (e.g. "2.069 (51,4%)")
        # so outside-positioned text isn't clipped by the plot area.
        max_label_len = chart_data[text_col].astype(str).str.len().max()
        right_margin = max(35, int(max_label_len * 7))
    fig = px.bar(
        chart_data,
        x=x,
        y=y,
        orientation="h",
        text=text_col,
        title=title,
        labels={x: x_label, y: ""},
    )
    fig.update_traces(marker_color=color, textposition="outside", cliponaxis=False)
    fig.update_layout(
        height=max(390, len(chart_data) * 27),
        margin=dict(l=5, r=right_margin, t=55, b=5),
        title_x=0,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        separators=",.",
    )
    fig.update_xaxes(
        showgrid=True, gridcolor="rgba(128,128,128,0.15)",
        tickformat=",.0f", hoverformat=",.0f",
    )
    fig.update_yaxes(showgrid=False)
    return fig


def pie_chart(
    data: pd.DataFrame,
    names: str,
    values: str,
    title: str,
    color_sequence=None,
    color_map: dict | None = None,
):
    """Create a consistently styled pie chart with % and value labels."""
    fig = px.pie(
        data,
        names=names,
        values=values,
        title=title,
        color=names if color_map else None,
        color_discrete_sequence=None if color_map else (color_sequence or px.colors.qualitative.Set3),
        color_discrete_map=color_map,
    )
    fig.update_traces(
        texttemplate="%{value:,.0f}<br>%{percent}", textposition="inside"
    )
    fig.update_layout(
        height=420,
        margin=dict(l=5, r=5, t=55, b=5),
        title_x=0,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend_title_text="",
        separators=",.",
    )
    return fig


def choropleth_map(data: pd.DataFrame, locations: str, color: str, title: str):
    """Create a consistently styled thermal-scale choropleth map."""
    fig = px.choropleth(
        data,
        locations=locations,
        color=color,
        scope="world",
        color_continuous_scale="thermal",
        title=title,
    )
    fig.update_geos(
        showcountries=True,
        showcoastlines=False,
        showland=True,
        landcolor="rgba(128,128,128,0.08)",
        bgcolor="rgba(0,0,0,0)",
        projection_type="natural earth",
    )
    fig.update_traces(hovertemplate=fig.data[0].hovertemplate.replace("%{z}", "%{z:,.0f}"))
    fig.update_coloraxes(colorbar_tickformat=",.0f")
    fig.update_layout(
        height=520,
        margin=dict(l=0, r=0, t=55, b=0),
        title_x=0,
        paper_bgcolor="rgba(0,0,0,0)",
        separators=",.",
    )
    return fig


def stacked_year_bar(
    data: pd.DataFrame,
    year_col: str,
    segment_col: str,
    value_col: str,
    y_label: str,
    title: str,
    color_sequence=None,
    color_map: dict | None = None,
    show_pct: bool = False,
):
    """Create a consistently styled year-by-year stacked bar chart."""
    data = data.copy()
    text_col = None
    if show_pct:
        year_totals = data.groupby(year_col)[value_col].transform("sum")
        pct_values = (data[value_col] / year_totals * 100).round(1)
        data["pct_label"] = pct_values.map(lambda v: european_number(f"{v}") + "%")
        text_col = "pct_label"
    fig = px.bar(
        data,
        x=year_col,
        y=value_col,
        color=segment_col,
        text=text_col,
        title=title,
        labels={year_col: "Year", value_col: y_label, segment_col: ""},
        color_discrete_sequence=None if color_map else (color_sequence or px.colors.qualitative.Set3),
        color_discrete_map=color_map,
    )
    if show_pct:
        fig.update_traces(textposition="inside")
    fig.update_layout(
        barmode="stack",
        height=420,
        margin=dict(l=5, r=10, t=55, b=5),
        title_x=0,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend_title_text="",
        separators=",.",
    )
    fig.update_xaxes(dtick=1, showgrid=False)
    fig.update_yaxes(
        gridcolor="rgba(128,128,128,.15)", tickformat=",.0f", hoverformat=",.0f"
    )
    return fig


st.markdown(
    """
    <style>
      .block-container {padding-top: 2rem; padding-bottom: 3rem;}
      [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(19,111,99,.10), rgba(52,152,219,.06));
        border: 1px solid rgba(19,111,99,.18);
        border-radius: 14px;
        padding: 16px 18px;
      }
      [data-testid="stMetricLabel"] {font-weight: 600;}
      div[data-testid="stDataFrame"] {border-radius: 12px; overflow: hidden;}
      .dashboard-note {
        padding: 12px 16px;
        border-left: 4px solid #136F63;
        background: rgba(19,111,99,.07);
        border-radius: 0 10px 10px 0;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Life Science Industry — Europe Market Opportunity")
st.caption(
    "The present project aims to identify opportunities for a MEDTECH company in Europe by analyzing the CORDIS 2014 - 2027 (*Community Research and Development Information Service*, which provide information on EU-funded research and innovation projects)"
    " and CTIS public data ( *Clinical Trials Information System*, which provide information on clinical trials conducted in the EU) datasets."

)

st.caption(
    "**Scope of the analysis**\n\n"
    "• Projects were classified into strategic life science categories relevant to Tecan.\n"
    "• CORDIS: Active Horizon Europe projects with signed grants and currently in progress only.\n"
    "• CTIS: Active or recruiting clinical trials only.\n"
    "• The objective is to identify organizations, technologies, and markets with the highest commercial potential."
)


consur = clean_consur(CONSUR_CANDIDATES)
trials = clean_trials(TRIALS_CANDIDATES)
all_trial_countries = TRIAL_COUNTRIES_CANDIDATES.copy()
cordis_opportunities_all = clean_cordis_opportunities(CORDIS_OPPORTUNITIES_CANDIDATES)

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")
st.sidebar.caption("Filters affect every KPI and chart in the dashboard.")

period_options = sorted(consur["period"].dropna().unique().tolist())
selected_periods = st.sidebar.multiselect(
    "CORDIS funding period", period_options, default=period_options
)

project_status_options = sorted(consur["status"].dropna().unique().tolist())
selected_project_statuses = st.sidebar.multiselect(
    "Project status", project_status_options, default=project_status_options
)

country_options = sorted(consur["country_name"].dropna().unique().tolist())
selected_project_countries = st.sidebar.multiselect(
    "Project participant country", country_options
)

category_options = sorted(consur["category"].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect(
    "Life-science category", category_options, default=category_options
)

trial_status_options = sorted(
    trials["Overall_trial_status"].dropna().astype(str).unique().tolist()
)
selected_trial_statuses = st.sidebar.multiselect(
    "Trial status", trial_status_options, default=trial_status_options
)

trial_phase_options = sorted(
    trials["Trial_phase"].dropna().astype(str).unique().tolist()
)
selected_trial_phases = st.sidebar.multiselect("Trial phase", trial_phase_options)

top_n = st.sidebar.slider("Countries shown in trial country bar", 5, 25, 12)

filtered_consur = consur.copy()
filtered_consur = multiselect_filter(filtered_consur, "period", selected_periods)
filtered_consur = multiselect_filter(
    filtered_consur, "status", selected_project_statuses
)
filtered_consur = multiselect_filter(
    filtered_consur, "country_name", selected_project_countries
)
filtered_consur = multiselect_filter(filtered_consur, "category", selected_categories)

filtered_trials = trials.copy()
filtered_trials = multiselect_filter(
    filtered_trials, "Overall_trial_status", selected_trial_statuses
)
filtered_trials = multiselect_filter(
    filtered_trials, "Trial_phase", selected_trial_phases
)
trial_countries = all_trial_countries[
    all_trial_countries["trial_id"].isin(filtered_trials["trial_id"])
].copy()

st.sidebar.divider()

# ---------------------------------------------------------------------------
# Shared aggregates (used across both tabs)
# ---------------------------------------------------------------------------
cordis_tab, trials_tab = st.tabs(["CORDIS opportunities", "Clinical trials"])

project_level = filtered_consur.sort_values("projectID").drop_duplicates("projectID")
project_country_count = filtered_consur["country_name"].nunique()

unique_trials = filtered_trials["trial_id"].nunique()
trial_country_count = trial_countries["country_name"].nunique()
distinct_sponsors = filtered_trials["Sponsor_Co-Sponsors"].nunique()
active_opportunity_trials = (
    filtered_trials["trial_status_group"] == "Active / recruiting opportunity"
).sum()
high_opportunity_trials = (filtered_trials["opportunity_tier_ctis"] == "High").sum()

# Restrict the project-level opportunity table to whatever the sidebar filters
# currently select (the table itself has no period/status/country columns).
cordis_opportunities = cordis_opportunities_all[
    cordis_opportunities_all["projectID"].isin(filtered_consur["projectID"])
].copy()

# "Open" projects: still running in 2026 or later and not wound down/dropped.
# Drives most of the CORDIS tab (the status chart is the one exception, since
# its whole job is to show the status breakdown itself).
open_projects_mask = (
    (filtered_consur["project_end_year"] >= 2026)
    & (filtered_consur["status"] == "SIGNED")
)
open_projects = filtered_consur[open_projects_mask]
open_project_level = open_projects.drop_duplicates("projectID")
max_open_end_year = (
    int(open_project_level["project_end_year"].max())
    if not open_project_level.empty
    else 2026
)

# ---------------------------------------------------------------------------
# CORDIS opportunities tab
# ---------------------------------------------------------------------------
with cordis_tab:
    cols = st.columns(4)
    cols[0].metric("Countries with projects", integer(project_country_count))
    cols[1].metric(
        f"Projects open: 2026-{max_open_end_year}",
        integer(open_project_level["projectID"].nunique()),
    )
    cols[2].metric(
        "Organisations (open 2026+)", integer(open_projects["organisationID"].nunique())
    )
    cols[3].metric(
        "Investment (open 2026+)", euro(open_project_level["totalCostProj"].sum())
    )

    st.markdown("#### Overview")
    st.info(
            "The CORDIS database (2014–2027) includes life science projects across 146 countries. "
            "As of 2026, there are **4,760 active signed projects** involving **8,428 organizations**, "
            "representing approximately **€12.1B** in total project funding."
        )


    st.markdown("#### Projects by *Activity Type*")
    st.caption(
        "Organizations are grouped by **Activity Type**: Higher / Secondary Education (e.g., University of Zurich, University of Bern), "
        "Research Organization (e.g., Switzerland Innovation Park, PSI, Swiss Cancer Institute), "
        "Private Company (e.g., Siemens, IBM Research, Roche), "
        "Public Body (e.g., Geneva University Hospitals), and Other (e.g., Foundation for Innovative New Diagnostics)."
    )
    activity_all = (
        open_projects.dropna(subset=["activityType"])
        .assign(organisation_type=lambda d: d["activityType"].map(ACTIVITY_LABELS).fillna("Unknown"))
        [["projectID", "organisation_type"]]
        .drop_duplicates()
        .groupby("organisation_type")["projectID"]
        .nunique()
        .reset_index(name="projects")
    )
    activity_year = (
        open_projects.dropna(subset=["activityType", "project_start_year"])
        .assign(organisation_type=lambda d: d["activityType"].map(ACTIVITY_LABELS).fillna("Unknown"))
        [["projectID", "organisation_type", "project_start_year"]]
        .drop_duplicates()
        .groupby(["project_start_year", "organisation_type"])["projectID"]
        .nunique()
        .reset_index(name="projects")
    )
    activity_left, activity_right = st.columns(2)
    with activity_left:
        st.plotly_chart(
            pie_chart(
                activity_all, "organisation_type", "projects",
                "Mix by Activity Type (on going projects)", color_map=ACTIVITY_TYPE_COLORS,
            ),
            width="stretch",
        )
    with activity_right:
        st.plotly_chart(
            stacked_year_bar(
                activity_year, "project_start_year", "organisation_type", "projects",
                "Unique projects", "Ongoing Projects by Activity Type and Start Year",
                color_map=ACTIVITY_TYPE_COLORS, show_pct=True,
            ),
            width="stretch",
        )

    st.info(
        "Approximately **70% of active projects** are led by **Research Organizations** and **Higher / Secondary Education** institutions, making them the primary innovation ecosystem for EU-funded research. "
        "Since 2023, **private companies** have increased their participation.  "
        "**Commercial implication:** prioritize engagement with research institutes and universities while strengthening relationships with emerging private-sector innovators."
    )

    st.markdown("#### Projects by *Life-Science Category*")
    st.caption(
        "Projects were classified into categories aligned with Tecan's core business using keywords extracted from each project's objective and description. "
        "The analysis covers nine strategic domains: Genomics / Molecular Biology, Oncology, Diagnostics / Biomarkers, Digital Health / Bioinformatics, Pharma / Biotech, "
        "Cell / Advanced Therapies, Proteomics / Multi-omics, MedTech / Medical Device, Automation, and Other. This is a proxy approach, not a precise topic label."
    )
    category_all = (
        open_projects.dropna(subset=["category"])
        [["projectID", "category"]]
        .drop_duplicates()
        .groupby("category")["projectID"]
        .nunique()
        .reset_index(name="projects")
    )
    category_year = (
        open_projects.dropna(subset=["category", "project_start_year"])
        [["projectID", "category", "project_start_year"]]
        .drop_duplicates()
        .groupby(["project_start_year", "category"])["projectID"]
        .nunique()
        .reset_index(name="projects")
    )
    category_left, category_right = st.columns(2)
    with category_left:
        st.plotly_chart(
            pie_chart(
                category_all, "category", "projects", "Category mix (all years)",
                color_map=CATEGORY_COLORS,
            ),
            width="stretch",
        )
    with category_right:
        st.plotly_chart(
            stacked_year_bar(
                category_year, "project_start_year", "category", "projects",
                "Unique projects", "Projects by category, per year",
                color_map=CATEGORY_COLORS, show_pct=True,
            ),
            width="stretch",
        )
    st.info(
        "Approximately **56% of active projects** are concentrated in **Genomics / Molecular Biology** and **Oncology**, followed by **Diagnostics / Biomarkers**. "
        "These areas closely align with Tecan's laboratory automation and liquid handling portfolio. "
        "**Commercial implication:** prioritize account mapping and commercial engagement with organizations leading projects in these domains, while increasing visibility in the growing **Diagnostics**, **Digital Health**, and **Pharma / Biotech** segments to capture emerging opportunities."
    )

    st.markdown("#### Projects by *Country*")
    st.caption("Mapping by country of the on-going projects with a status Signed).")
    country_counts = (
        open_projects[["projectID", "country_name", "country_iso3"]]
        .dropna(subset=["country_iso3"])
        .drop_duplicates(subset=["projectID", "country_iso3"])
        .groupby(["country_iso3", "country_name"], as_index=False)["projectID"]
        .nunique()
        .rename(columns={"projectID": "projects"})
    )
    st.plotly_chart(
        choropleth_map(country_counts, "country_iso3", "projects", "Projects by country"),
        width="stretch",
    )

    st.info(
        "Germany remains the largest research market in Europe, with more than 1,600 active projects, followed by Spain, France, the United Kingdom, the Netherlands, and Italy. These countries should remain the primary commercial focus, while the increasing project activity in Sweden, Austria, and Greece highlights emerging markets with growing future potential."
    )

    st.markdown("#### Project *Opportunity Ranking*")
    st.caption(
        "Projects are prioritized according to their commercial relevance for Tecan. "
        "**High**: Active projects (end date ≥ 2026) within Tecan's core business domains. "
        "**Medium**: Projects ending in 2026 within Tecan's core business domains. "
        "**Low**: Projects outside Tecan's strategic business areas."
    )

    st.info(
    "Ranking projects by opportunity highlights organizations with the largest active research funding in areas aligned with Tecan's portfolio. "
    "These organizations represent high-priority accounts for commercial engagement, helping Sales identify where to focus, understand their phase in the ongoing research, and align with the company's solutions with future laboratory needs."
    )
    cordis_opportunities_open = cordis_opportunities[
        (cordis_opportunities["project_end_year"] >= 2026)
        & (cordis_opportunities["status"] == "SIGNED")
    ]
    cordis_opportunities_rankable = cordis_opportunities_open[
        cordis_opportunities_open["opportunity_tier_cordis"] != "Not applicable"
    ]
    cordis_tier_filter = st.multiselect(
        "Opportunity tier", OPPORTUNITY_TIERS, default=OPPORTUNITY_TIERS,
        key="cordis_tier_filter",
    )
    cordis_opportunities_view = multiselect_filter(
        cordis_opportunities_rankable, "opportunity_tier_cordis", cordis_tier_filter
    ).copy()
    cordis_opportunities_view["investment_display"] = cordis_opportunities_view[
        "totalCostProj"
    ].map(lambda v: f"€ {european_number(f'{round(v):,}')}")
    st.dataframe(
        cordis_opportunities_view[[
            "category", "title", "coordinator_name", "coordinator_country",
            "status", "project_start_year", "project_end_year",
            "investment_display", "opportunity_tier_cordis",
        ]].head(500),
        width="stretch",
        hide_index=True,
        column_config={
            "category": "Category",
            "title": st.column_config.TextColumn("Project", width="large"),
            "coordinator_name": st.column_config.TextColumn("Organisation", width="medium"),
            "coordinator_country": "Country",
            "status": "Status",
            "project_start_year": st.column_config.NumberColumn("Start year", format="%d"),
            "project_end_year": st.column_config.NumberColumn("End year", format="%d"),
            "investment_display": "Investment",
            "opportunity_tier_cordis": "Opportunity",
        },
    )
    if len(cordis_opportunities_view) > 500:
        st.caption("Showing the first 500 matching projects.")

# ---------------------------------------------------------------------------
# Clinical trials tab
# ---------------------------------------------------------------------------
with trials_tab:
    trial_cols = st.columns(4)
    trial_cols[0].metric("Trials", integer(unique_trials))
    trial_cols[1].metric("Active Opportunity", integer(active_opportunity_trials))
    trial_cols[2].metric("Countries Reached", integer(trial_country_count))
    trial_cols[3].metric("Trial Sponsors", integer(distinct_sponsors))

    st.info(
    "Based on the CTIS database, the analysis identifies **4,023 clinical trials**, of which **2,069 are active or recruiting opportunities**. "
    "These trials span **28 countries** and involve approximately **1,179 organizations**."
    )

    st.caption(
    "**Clinical trial opportunity definition:** The analysis focuses on **active and recruiting clinical trials**, as they provide an early indicator of future demand for laboratory technologies and help identify organizations, therapeutic areas, and countries where new commercial opportunities are emerging. This includes trials that are authorised and recruiting (51.4% of the database). **Not authorised** trials are reported separately, while completed, Inactive, and Other trials are excluded from the opportunity analysis."
    )

    left, right = st.columns(2)
    with left:
        status_group_summary = (
            filtered_trials["trial_status_group"]
            .fillna("Unknown")
            .value_counts()
            .rename_axis("status_group")
            .reset_index(name="trials")
        )
        status_group_total = status_group_summary["trials"].sum()
        status_group_summary["label"] = status_group_summary["trials"].map(
            lambda v: f"{integer(v)} ({european_number(f'{v / status_group_total * 100:.1f}')}%)"
        )
        st.plotly_chart(
            horizontal_bar(
                status_group_summary, "trials", "status_group", "Trials by Status",
                "Trials", "#2878B5", "label",
            ),
            width="stretch",
        )
    with right:
        active_trials = filtered_trials[
            filtered_trials["trial_status_group"] == "Active / recruiting opportunity"
        ]
        sponsor_active_summary = (
            active_trials["primary_sponsor_type"]
            .fillna("Unknown")
            .value_counts()
            .rename_axis("sponsor_type")
            .reset_index(name="trials")
        )
        sponsor_active_total = sponsor_active_summary["trials"].sum()
        sponsor_active_summary["label"] = sponsor_active_summary["trials"].map(
            lambda v: f"{integer(v)} ({european_number(f'{v / sponsor_active_total * 100:.1f}')}%)"
        )
        st.plotly_chart(
            horizontal_bar(
                sponsor_active_summary, "trials", "sponsor_type",
                "Active-Opportunity Trials by Sponsor Type", "Trials",
                "#C77800", "label",
            ),
            width="stretch",
        )

    st.info(
        "Classifying trial sponsors by organization type shows that **82% of active clinical trials are led by hospitals, healthcare institutions, and pharmaceutical companies**. These organizations represent the largest concentration of potential commercial opportunities for Tecan."
    )

    st.markdown("#### Trials by *Country*")
    country_view = st.radio(
        "France, Spain, and Italy have the highest number of active and recruiting clinical trials, reinforcing their research activity already observed in CORDIS projects. An additional signal is the growing clinical activity in *Poland* and *Czechia*, suggesting emerging markets where Tecan could strengthen its commercial presence and develop relationships with research organizations before demand matures.",
        ["Active / recruiting opportunity", "Recruitment ended / completed"],
        horizontal=True,
        key="trial_country_status_view",
    )
    trials_country_join = trial_countries.merge(
        filtered_trials[["trial_id", "trial_status_group"]], on="trial_id", how="inner"
    )
    country_trial_counts = (
        trials_country_join[trials_country_join["trial_status_group"] == country_view]
        .dropna(subset=["country_iso3"])
        .groupby(["country_iso3", "country_name"], as_index=False)["trial_id"]
        .nunique()
        .rename(columns={"trial_id": "trials"})
    )
    country_bar_left, country_map_right = st.columns(2)
    with country_bar_left:
        top_bar = country_trial_counts.nlargest(top_n, "trials")
        st.plotly_chart(
            horizontal_bar(
                top_bar, "trials", "country_name",
                f"{country_view} — top {top_n} countries", "Trials",
                "#2878B5", "trials",
            ),
            width="stretch",
        )
    with country_map_right:
        st.plotly_chart(
            choropleth_map(country_trial_counts, "country_iso3", "trials",
                            f"{country_view} by country"),
            width="stretch",
        )





    st.markdown("#### Trial *Opportunity* Ranking")

    st.caption(
        "This table includes only **active commercial opportunities** (authorised or recruiting clinical trials). "
        "Completed, suspended, expired, and not authorised trials are excluded. "
        "Each row represents one trial and includes the sponsor, sponsor type, trial status, and an overall opportunity rating (High, Medium, or Low) based on trial stage, sponsor profile, and recency."
        " **Commercial action:** prioritize engagement with both sponsors and co-sponsors, as they are the organizations driving the research and the most likely decision-makers for future laboratory equipment and automation investments."
    )



    active_trials_for_ranking = filtered_trials[
        filtered_trials["trial_status_group"] == "Active / recruiting opportunity"
    ]
    ctis_tier_filter = st.multiselect(
        "Opportunity tier", OPPORTUNITY_TIERS, default=OPPORTUNITY_TIERS,
        key="ctis_tier_filter",
    )
    trial_explorer = multiselect_filter(
        active_trials_for_ranking, "opportunity_tier_ctis", ctis_tier_filter
    )

    search = st.text_input(
        "Search trial title, condition, product, or sponsor",
        placeholder="e.g. oncology, PCR, Roche...",
    )
    if search:
        searchable_columns = [
            column
            for column in (
                "Title_of_the_trial",
                "Medical_conditions",
                "Product",
                "Sponsor_Co-Sponsors",
            )
            if column in trial_explorer
        ]
        safe_search = re.escape(search)
        search_mask = (
            trial_explorer[searchable_columns]
            .fillna("")
            .astype(str)
            .agg(" ".join, axis=1)
            .str.contains(safe_search, case=False, regex=True)
        )
        trial_explorer = trial_explorer[search_mask]

    st.dataframe(
        trial_explorer[[
            "Title_of_the_trial", "primary_sponsor_type", "Sponsor_Co-Sponsors",
            "Overall_trial_status", "opportunity_tier_ctis",
        ]].head(500),
        width="stretch",
        hide_index=True,
        column_config={
            "Title_of_the_trial": st.column_config.TextColumn("Title", width="large"),
            "primary_sponsor_type": "Sponsor type",
            "Sponsor_Co-Sponsors": st.column_config.TextColumn("Sponsor / co-sponsors", width="medium"),
            "Overall_trial_status": "Status",
            "opportunity_tier_ctis": "Opportunity",
        },
    )
    if len(trial_explorer) > 500:
        st.caption("Showing the first 500 matching trials.")

    with st.expander("Methodology & definitions"):
        st.markdown(
        """
        **CORDIS opportunity ranking**  
        Closed and terminated projects are excluded. The analysis focuses on signed projects that are still active in 2026 or later.

        - **High:** active projects in categories closely linked to Tecan’s core business  
        - **Medium:** core-category projects ending sooner, or active projects with a weaker strategic fit  
        - **Low:** all other signed projects  

        **Trial opportunity ranking**  
        Trials are ranked using three factors: trial status, sponsor type, and recency. Active or recruiting trials receive the highest weight, followed by commercially relevant sponsors and more recent activity.

        **Project investment**  
        `totalCostProj` is counted once per project, since the same project value appears across multiple participating organizations.

        **How to read the results**  
        Public funding and clinical-trial activity are market signals, not confirmed sales opportunities. Project categories are based on keyword classification, and CTIS trend analysis is limited to data available from 2022 onward.
        """
        )