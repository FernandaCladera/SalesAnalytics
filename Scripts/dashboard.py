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


CONSUR_CANDIDATES = pd.read_csv("../../_local_data_backup/ConsurDatabase_clean.csv")
TRIALS_CANDIDATES = pd.read_csv("../Scripts/data/data_final/TrialsDatabase_clean.csv")
TRIAL_COUNTRIES_CANDIDATES = pd.read_csv(
    "../Scripts/data/data_final/TrialCountry_clean.csv"
)

ACTIVITY_LABELS = {
    "HES": "Higher / secondary education",
    "PRC": "Private company",
    "REC": "Research organisation",
    "PUB": "Public body",
    "OTH": "Other",
}


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
    for column in (
        "Decision_date",
        "Start_date",
        "End_date",
        "Global_end_of_the_trial",
        "Last_updated",
    ):
        df[column] = pd.to_datetime(df[column], errors="coerce")
    df["Number_of_participants_enrolled"] = pd.to_numeric(
        df["Number_of_participants_enrolled"], errors="coerce"
    )
    return df


def euro(value: float) -> str:
    """Format large euro values compactly."""
    value = float(value or 0)
    if abs(value) >= 1_000_000_000:
        return f"€{value / 1_000_000_000:,.1f}B"
    if abs(value) >= 1_000_000:
        return f"€{value / 1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"€{value / 1_000:,.1f}K"
    return f"€{value:,.0f}"


def integer(value: float) -> str:
    """Format a count with thousands separators."""
    return f"{int(value):,}"


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
    chart_data = data.sort_values(x, ascending=True)
    fig = px.bar(
        chart_data,
        x=x,
        y=y,
        orientation="h",
        text=text,
        title=title,
        labels={x: x_label, y: ""},
    )
    fig.update_traces(marker_color=color, textposition="outside", cliponaxis=False)
    fig.update_layout(
        height=max(390, len(chart_data) * 27),
        margin=dict(l=5, r=35, t=55, b=5),
        title_x=0,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
    fig.update_yaxes(showgrid=False)
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
    "European research projects and clinical-trial activity derived from "
    "CORDIS 2014 - 2027 and CTIS public data."
)


consur = clean_consur(CONSUR_CANDIDATES)
trials = clean_trials(TRIALS_CANDIDATES)
all_trial_countries = TRIAL_COUNTRIES_CANDIDATES.copy()

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

top_n = st.sidebar.slider("Countries / organisations shown", 5, 25, 12)

filtered_consur = consur.copy()
filtered_consur = multiselect_filter(filtered_consur, "period", selected_periods)
filtered_consur = multiselect_filter(
    filtered_consur, "status", selected_project_statuses
)
filtered_consur = multiselect_filter(
    filtered_consur, "country_name", selected_project_countries
)

filtered_trials = trials.copy()
filtered_trials = multiselect_filter(
    filtered_trials, "Overall_trial_status", selected_trial_statuses
)
filtered_trials = multiselect_filter(
    filtered_trials, "Trial_phase", selected_trial_phases
)
trial_countries = all_trial_countries[
    all_trial_countries["Trial_number"].isin(filtered_trials["Trial_number"])
].copy()

st.sidebar.divider()


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------
overview_tab, projects_tab, trials_tab, methodology_tab = st.tabs(
    ["Executive overview", "CORDIS projects", "Clinical trials", "Methodology"]
)

unique_projects = filtered_consur[filtered_consur["period"] == "2021-2027"][
    "projectID"
].nunique()
unique_organisations = filtered_consur["organisationID"].nunique()
project_country_count = filtered_consur["country_name"].nunique()
unique_trials = filtered_trials["Trial_number"].nunique()
trial_country_count = trial_countries["country_name"].nunique()

# One project budget per project; the same value repeats for each organisation.
project_level = filtered_consur.sort_values("projectID").drop_duplicates("projectID")[
    ["projectID", "totalCostProj"]
]
total_project_budget = project_level["totalCostProj"].sum() / 1000
allocated_org_cost = filtered_consur["totalCostOrg"].sum()

with overview_tab:
    cols = st.columns(5)
    cols[0].metric("Countries with projects", integer(project_country_count))
    cols[1].metric("# Projects 2021-2027", integer(unique_projects))
    cols[2].metric("Organisations", integer(unique_organisations))
    cols[3].metric("Clinical trials", integer(unique_trials))
    cols[4].metric("Project investment", euro(total_project_budget))

    st.markdown(
        '<div class="dashboard-note"><b>How percentages are calculated:</b> '
        "country percentages represent each country's share of unique "
        "project–country or trial–country relationships. A project or trial active "
        "in several countries contributes once to each of those countries.</div>",
        unsafe_allow_html=True,
    )

    project_country_pairs = (
        filtered_consur[["projectID", "country_name"]].dropna().drop_duplicates()
    )
    project_country_summary = (
        project_country_pairs.groupby("country_name")["projectID"]
        .nunique()
        .rename("projects")
        .reset_index()
    )
    project_pair_total = project_country_summary["projects"].sum()
    project_country_summary["share"] = (
        project_country_summary["projects"] / project_pair_total * 100
        if project_pair_total
        else 0
    )
    project_country_summary["share_label"] = project_country_summary["share"].map(
        lambda value: f"{value:.1f}%"
    )

    trial_country_summary = (
        trial_countries.groupby("country_name")["Trial_number"]
        .nunique()
        .rename("trials")
        .reset_index()
    )
    trial_pair_total = trial_country_summary["trials"].sum()
    trial_country_summary["share"] = (
        trial_country_summary["trials"] / trial_pair_total * 100
        if trial_pair_total
        else 0
    )
    trial_country_summary["share_label"] = trial_country_summary["share"].map(
        lambda value: f"{value:.1f}%"
    )

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            horizontal_bar(
                project_country_summary.nlargest(top_n, "projects"),
                "projects",
                "country_name",
                "Projects by participant country",
                "Unique projects",
                "#136F63",
                "share_label",
            ),
            use_container_width=True,
        )
    with right:
        st.plotly_chart(
            horizontal_bar(
                trial_country_summary.nlargest(top_n, "trials"),
                "trials",
                "country_name",
                "Clinical trials by country",
                "Unique trials",
                "#2878B5",
                "share_label",
            ),
            use_container_width=True,
        )

    year_summary = (
        filtered_consur.dropna(subset=["startDate"])
        .assign(year=lambda data: data["startDate"].dt.year)
        .groupby("year")["projectID"]
        .nunique()
        .reset_index(name="projects")
    )
    if not year_summary.empty:
        year_fig = px.area(
            year_summary,
            x="year",
            y="projects",
            markers=True,
            title="New relevant projects by start year",
            labels={"year": "Start year", "projects": "Unique projects"},
        )
        year_fig.update_traces(line_color="#136F63", fillcolor="rgba(19,111,99,.18)")
        year_fig.update_layout(
            title_x=0,
            height=380,
            margin=dict(l=5, r=10, t=55, b=5),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        year_fig.update_xaxes(dtick=1, showgrid=False)
        year_fig.update_yaxes(gridcolor="rgba(128,128,128,.15)")
        st.plotly_chart(year_fig, use_container_width=True)

# ---------------------------------------------------------------------------
# CORDIS tab
# ---------------------------------------------------------------------------
with projects_tab:
    st.subheader("CORDIS project and organisation opportunity")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Countries represented", integer(project_country_count))
    metric_cols[1].metric("Project budget", euro(total_project_budget))
    metric_cols[2].metric("Organisation allocations", euro(allocated_org_cost))
    metric_cols[3].metric(
        "EC contribution", euro(filtered_consur["ecContribution"].sum())
    )
    st.caption(
        "Project budget is summed once per project. Organisation allocations and "
        "EC contribution are summed at the participant-organisation level."
    )

    country_project_counts = (
        filtered_consur[["projectID", "country_name"]]
        .dropna()
        .drop_duplicates()
        .groupby("country_name")["projectID"]
        .nunique()
        .reset_index(name="projects")
    )
    country_allocations = (
        filtered_consur.dropna(subset=["country_name"])
        .groupby("country_name", as_index=False)["totalCostOrg"]
        .sum()
        .rename(columns={"totalCostOrg": "investment"})
    )
    country_detail = country_project_counts.merge(
        country_allocations, on="country_name", how="outer"
    ).fillna(0)

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            horizontal_bar(
                country_detail.nlargest(top_n, "investment").assign(
                    investment_label=lambda data: data["investment"].map(euro)
                ),
                "investment",
                "country_name",
                "Allocated organisation cost by country",
                "Allocated cost (€)",
                "#C77800",
                "investment_label",
            ),
            use_container_width=True,
        )
    with right:
        activity = (
            filtered_consur.assign(
                organisation_type=filtered_consur["activityType"]
                .map(ACTIVITY_LABELS)
                .fillna("Unknown")
            )
            .groupby("organisation_type")["organisationID"]
            .nunique()
            .reset_index(name="organisations")
            .sort_values("organisations", ascending=False)
        )
        activity_fig = px.pie(
            activity,
            names="organisation_type",
            values="organisations",
            hole=0.58,
            title="Organisation mix",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        activity_fig.update_traces(textposition="inside", textinfo="percent")
        activity_fig.update_layout(
            title_x=0,
            height=430,
            margin=dict(l=5, r=5, t=55, b=5),
            legend_title_text="",
        )
        st.plotly_chart(activity_fig, use_container_width=True)

    organisation_summary = (
        filtered_consur.dropna(subset=["name"])
        .groupby(["organisationID", "name", "country_name"], dropna=False)
        .agg(
            projects=("projectID", "nunique"),
            allocated_cost=("totalCostOrg", "sum"),
            ec_contribution=("ecContribution", "sum"),
        )
        .reset_index()
        .sort_values(["allocated_cost", "projects"], ascending=False)
        .head(top_n)
    )
    organisation_summary["allocated_cost"] = organisation_summary[
        "allocated_cost"
    ].round(0)
    organisation_summary["ec_contribution"] = organisation_summary[
        "ec_contribution"
    ].round(0)

    st.markdown("#### Leading organisations")
    st.dataframe(
        organisation_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "organisationID": st.column_config.TextColumn("Organisation ID"),
            "name": "Organisation",
            "country_name": "Country",
            "projects": st.column_config.NumberColumn("Projects", format="%d"),
            "allocated_cost": st.column_config.NumberColumn(
                "Allocated cost", format="€ %.0f"
            ),
            "ec_contribution": st.column_config.NumberColumn(
                "EC contribution", format="€ %.0f"
            ),
        },
    )

# ---------------------------------------------------------------------------
# Trials tab
# ---------------------------------------------------------------------------
with trials_tab:
    st.subheader("CTIS clinical-trial landscape")
    participant_total = filtered_trials["Number_of_participants_enrolled"].sum(
        min_count=1
    )
    active_mask = (
        filtered_trials["Overall_trial_status"]
        .fillna("")
        .str.contains(r"ongoing|recruit", case=False, regex=True)
    )
    trial_metrics = st.columns(4)
    trial_metrics[0].metric("Trials", integer(unique_trials))
    trial_metrics[1].metric("Countries", integer(trial_country_count))
    trial_metrics[2].metric(
        "Enrolled participants",
        integer(participant_total) if pd.notna(participant_total) else "N/A",
    )
    trial_metrics[3].metric("Ongoing / recruiting", integer(active_mask.sum()))

    status_summary = (
        filtered_trials["Overall_trial_status"]
        .fillna("Unknown")
        .value_counts()
        .rename_axis("status")
        .reset_index(name="trials")
        .head(top_n)
    )
    phase_summary = (
        filtered_trials["Trial_phase"]
        .fillna("Unknown")
        .value_counts()
        .rename_axis("phase")
        .reset_index(name="trials")
        .head(top_n)
    )

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            horizontal_bar(
                status_summary,
                "trials",
                "status",
                "Trials by overall status",
                "Trials",
                "#2878B5",
                "trials",
            ),
            use_container_width=True,
        )
    with right:
        st.plotly_chart(
            horizontal_bar(
                phase_summary,
                "trials",
                "phase",
                "Trials by phase",
                "Trials",
                "#8250A0",
                "trials",
            ),
            use_container_width=True,
        )

    sponsor_summary = (
        filtered_trials["Sponsor_type"]
        .fillna("Unknown")
        .value_counts()
        .rename_axis("sponsor_type")
        .reset_index(name="trials")
        .head(top_n)
    )
    st.plotly_chart(
        horizontal_bar(
            sponsor_summary,
            "trials",
            "sponsor_type",
            "Trials by sponsor type",
            "Trials",
            "#C77800",
            "trials",
        ),
        use_container_width=True,
    )

    trial_table_columns = [
        "Trial_number",
        "Title_of_the_trial",
        "Overall_trial_status",
        "Trial_phase",
        "Therapeutic_area",
        "Sponsor/Co-Sponsors",
        "Number_of_participants_enrolled",
    ]
    available_trial_columns = [
        column for column in trial_table_columns if column in filtered_trials
    ]
    st.markdown("#### Trial explorer")
    search = st.text_input(
        "Search trial title, condition, product, or sponsor",
        placeholder="e.g. oncology, PCR, Roche...",
    )
    trial_explorer = filtered_trials.copy()
    if search:
        searchable_columns = [
            column
            for column in (
                "Title_of_the_trial",
                "Medical_conditions",
                "Product",
                "Sponsor/Co-Sponsors",
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
        trial_explorer[available_trial_columns].head(500),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Trial_number": "Trial number",
            "Title_of_the_trial": st.column_config.TextColumn("Title", width="large"),
            "Overall_trial_status": "Status",
            "Trial_phase": "Phase",
            "Therapeutic_area": "Therapeutic area",
            "Sponsor/Co-Sponsors": st.column_config.TextColumn(
                "Sponsor", width="medium"
            ),
            "Number_of_participants_enrolled": st.column_config.NumberColumn(
                "Participants", format="%d"
            ),
        },
    )
    if len(trial_explorer) > 500:
        st.caption("Showing the first 500 matching records.")

# ---------------------------------------------------------------------------
# Methodology tab
# ---------------------------------------------------------------------------
with methodology_tab:
    st.subheader("Metric definitions and interpretation")
    st.markdown(
        """
        **Countries with projects**  
        Distinct participant-country codes in the filtered CORDIS data. CORDIS can
        include partners outside Europe, so this is a count of represented countries,
        not a percentage of EU member states.

        **Project share by country (%)**  
        Unique project–country relationships for a country divided by all unique
        project–country relationships. One multinational project contributes once to
        every participating country.

        **Trials by country**  
        CTIS location strings are split into individual countries. Counts use unique
        trial–country pairs, preventing duplicate locations from inflating the result.

        **Project investment**  
        Sum of `totalCostProj` after deduplicating on `projectID`. The project budget
        is repeated on every participating-organisation row in the source and must
        therefore not be summed directly.

        **Organisation allocations**  
        Sum of `totalCostOrg` at participant level. This measures costs allocated to
        organisations and is suitable for country and organisation comparisons.

        **Important interpretation**  
        Public funding and clinical-trial activity are opportunity signals, not
        confirmed purchasing intent. Keyword filtering may contain false positives,
        and organisation names have not yet been fully normalized across sources.
        """
    )

    with st.expander("Dataset diagnostics"):
        diagnostics = pd.DataFrame(
            [
                {
                    "Dataset": "CORDIS opportunity base",
                    "Rows after filters": len(filtered_consur),
                    "Unique entities": unique_projects,
                    "Entity definition": "Project",
                },
                {
                    "Dataset": "CTIS trials",
                    "Rows after filters": len(filtered_trials),
                    "Unique entities": unique_trials,
                    "Entity definition": "Trial",
                },
            ]
        )
        st.dataframe(diagnostics, hide_index=True, use_container_width=True)
