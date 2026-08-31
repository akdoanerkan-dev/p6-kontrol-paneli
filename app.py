# =============================================================================
# CONSTRUCTION PLANNING & CONTROL DASHBOARD
# Planning and control platform built on Primavera P6 (.xer) files
#
# Run with:  streamlit run app.py
# =============================================================================

import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 0. PAGE SETUP & THEME
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Construction Planning & Control",
    page_icon="◱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# The palette comes from the drawing office: ink on paper, with the setting-out
# colours P6 planners already read fluently (blue plan, green earned, red critical).
INK = "#15242F"        # title block, headings
SLATE = "#6B7F8C"      # secondary text
RULE = "#E3E9ED"       # hairlines
GRID = "#F1F4F7"       # chart gridlines
PLANNED = "#3D7EA6"    # planned value
EARNED = "#3E8E6D"     # earned value
ACTUAL = "#C08A3E"     # actual cost
ALERT = "#BE4B48"      # critical / adverse variance
FORECAST = "#7B6AA6"   # forecast
GOOD_DK = "#8FD9B4"    # positive figure on the dark title block
BAD_DK = "#F0A39B"     # adverse figure on the dark title block

FONT = "'IBM Plex Sans', -apple-system, Segoe UI, sans-serif"
MONO = "'IBM Plex Mono', ui-monospace, monospace"

st.markdown(
    f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

      /* Set the family once on the root and let it inherit. Naming span/div
         here would also capture Streamlit's icon spans, whose glyphs are font
         ligatures: override their font and the raw names ("upload",
         "keyboard_double_arrow_right") print as text. Form controls need it
         spelled out because they do not inherit font by default. */
      .stApp {{font-family: {FONT}; font-feature-settings: 'tnum' 1;}}
      button, input, select, textarea, optgroup {{font-family: {FONT};}}

      /* Never touch the icon fonts. */
      [data-testid="stIconMaterial"],
      span[data-testid="stIconMaterial"],
      .material-icons, .material-icons-outlined,
      .material-symbols-rounded, .material-symbols-outlined,
      [class^="material-symbols"], [class*=" material-symbols"],
      [class^="material-icons"], [class*=" material-icons"] {{
        font-family: 'Material Symbols Rounded', 'Material Icons',
                     'Material Symbols Outlined' !important;
        font-feature-settings: 'liga' 1 !important;
      }}
      .block-container {{padding-top: 2.6rem; padding-bottom: 4rem; max-width: 1560px;}}
      h1, h2, h3, h4 {{color: {INK}; letter-spacing: -0.011em; font-weight: 600;}}

      /* --- tab bar: give the labels room instead of a fixed height --------- */
      .stTabs [data-baseweb="tab-list"] {{
        gap: .15rem; border-bottom: 1px solid {RULE};
        overflow-x: auto; overflow-y: visible;
        padding: .3rem 0 0 0; align-items: stretch;
      }}
      .stTabs [data-baseweb="tab"] {{
        height: auto; min-height: 2.6rem; padding: .55rem 1.05rem;
        display: flex; align-items: center; white-space: nowrap;
      }}
      .stTabs [data-baseweb="tab"] p {{
        font-size: .92rem; line-height: 1.5; margin: 0; color: {SLATE}; font-weight: 500;
      }}
      .stTabs [aria-selected="true"] p {{color: {INK}; font-weight: 600;}}
      .stTabs [data-baseweb="tab-highlight"] {{background-color: {PLANNED};}}
      .stTabs [data-baseweb="tab-border"] {{background-color: {RULE};}}

      /* --- title block: the one bold element on the page ------------------- */
      .tb {{background: {INK}; border-radius: 4px; overflow: hidden; margin-bottom: 1.1rem;}}
      .tb-head {{display: flex; align-items: baseline; gap: .8rem; flex-wrap: wrap;
                 padding: .95rem 1.25rem .8rem 1.25rem;
                 border-top: 3px solid {PLANNED};}}
      .tb-proj {{color: #fff; font-size: 1.2rem; font-weight: 600; letter-spacing: -.015em;}}
      .tb-meta {{color: #9DB4C2; font-size: .82rem; font-family: {MONO};}}
      .tb-grid {{display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                 border-top: 1px solid #243A47;}}
      .tb-cell {{padding: .75rem 1.25rem .8rem 1.25rem; border-left: 1px solid #243A47;
                 border-bottom: 3px solid transparent;}}
      .tb-cell:first-child {{border-left: none;}}
      .tb-cell.good {{border-bottom-color: {EARNED};}}
      .tb-cell.bad {{border-bottom-color: {ALERT};}}
      .tb-cell.warn {{border-bottom-color: {ACTUAL};}}
      .tb-lab {{display:block; color: #93AAB8; font-size: .73rem; margin-bottom: .2rem;}}
      .tb-val {{display:block; color: #fff; font-size: 1.45rem; font-weight: 500;
                line-height: 1.15; font-variant-numeric: tabular-nums;}}
      .tb-val.good {{color: {GOOD_DK};}}
      .tb-val.bad {{color: {BAD_DK};}}
      .tb-val.warn {{color: #F2C879;}}
      .tb-sub {{display:block; color: #86A0AF; font-size: .73rem; font-family: {MONO};
                margin-top: .14rem;}}

      /* --- figure strip: colour-coded accents ------------------------------ */
      .fs {{display: grid; grid-template-columns: repeat(auto-fit, minmax(128px, 1fr));
            border: 1px solid {RULE}; border-radius: 4px; margin-bottom: 1.1rem;
            overflow: hidden; background: #fff;}}
      .fs-cell {{padding: .62rem .95rem .7rem .95rem; border-left: 1px solid {RULE};
                 border-top: 3px solid {RULE};}}
      .fs-cell:first-child {{border-left: none;}}
      .fs-lab {{display:block; color: {SLATE}; font-size: .73rem; margin-bottom: .12rem;}}
      .fs-val {{display:block; color: {INK}; font-size: 1.14rem; font-weight: 600;
                font-variant-numeric: tabular-nums;}}
      .fs-val.good {{color: {EARNED};}} .fs-val.bad {{color: {ALERT};}}
      .fs-val.warn {{color: {ACTUAL};}}
      .fs-sub {{display:block; color: {SLATE}; font-size: .71rem; font-family: {MONO};}}

      /* --- section headings replace dividers -------------------------------- */
      .sec {{border-top: 1px solid {RULE}; margin: 1.9rem 0 .9rem 0; padding-top: .85rem;}}
      .sec h3 {{margin: 0; font-size: 1.04rem;}}
      .sec p {{margin: .2rem 0 0 0; color: {SLATE}; font-size: .83rem; max-width: 76ch;}}
      .sec.tight {{margin-top: 1.1rem;}}

      /* --- verdict banner ---------------------------------------------------- */
      .verdict {{display: flex; gap: .6rem; flex-wrap: wrap; align-items: center;
                 border: 1px solid {RULE}; border-left: 4px solid {PLANNED};
                 border-radius: 4px; padding: .7rem .95rem; margin-bottom: 1.2rem;
                 background: #FBFDFE;}}
      .verdict.bad {{border-left-color: {ALERT}; background: #FDF8F7;}}
      .verdict.good {{border-left-color: {EARNED}; background: #F7FCF9;}}
      .vd-pill {{font-size: .78rem; padding: .18rem .55rem; border-radius: 999px;
                 color: #fff; font-weight: 500;}}
      .verdict span.txt {{font-size: .88rem; color: {INK};}}

      /* --- streamlit chrome --------------------------------------------------- */
      section[data-testid="stSidebar"] {{background: #F7F9FB; border-right: 1px solid {RULE};}}
      section[data-testid="stSidebar"] h3 {{font-size: .82rem; color: {SLATE};
                                            font-weight: 600; margin-bottom: .3rem;}}
      label[data-testid="stWidgetLabel"] p {{font-size: .79rem; color: {SLATE};
                                             margin-bottom: .15rem;}}
      div[data-testid="stMetricValue"] {{font-size: 1.2rem; color: {INK};
                                         font-variant-numeric: tabular-nums;}}
      div[data-testid="stDataFrame"] {{border: 1px solid {RULE}; border-radius: 4px;}}
      div[data-testid="stVerticalBlockBorderWrapper"] {{border-radius: 4px;}}
      .stDownloadButton button, .stButton button {{border-radius: 4px; font-weight: 500;}}
      .stAlert {{border-radius: 4px;}}
      #MainMenu, footer {{visibility: hidden;}}
    </style>
    """,
    unsafe_allow_html=True,
)


def fmt(x, dp=0, unit=""):
    """Compact figure for the header strips: 2.35M rather than 2,345,600."""
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    a = abs(x)
    if a >= 1e9:
        return f"{x/1e9:,.2f}B{unit}"
    if a >= 1e6:
        return f"{x/1e6:,.2f}M{unit}"
    if a >= 1e4:
        return f"{x/1e3:,.1f}k{unit}"
    return f"{x:,.{dp}f}{unit}"


def _cells(items, prefix):
    """Each cell carries a tone (colours the figure) and an accent (colours the
    rule above or below it, grouping metrics into families at a glance)."""
    out = []
    for i in items:
        tone = i.get("tone", "")
        tip = f' title="{i["help"]}"' if i.get("help") else ""
        accent = i.get("accent")
        style = f' style="border-top-color:{accent}"' if accent and prefix == "fs" else ""
        out.append(
            f'<div class="{prefix}-cell {tone}"{tip}{style}>'
            f'<span class="{prefix}-lab">{i["label"]}</span>'
            f'<span class="{prefix}-val {tone}">{i["value"]}</span>'
            f'<span class="{prefix}-sub">{i.get("sub", "&nbsp;")}</span></div>')
    return "".join(out)


def verdict(messages, tone="good"):
    """Coloured one-line read on the state of the project."""
    pills = {"good": (EARNED, "On track"), "warn": (ACTUAL, "Watch"), "bad": (ALERT, "Attention")}
    color, word = pills.get(tone, pills["good"])
    body = " ".join(f'<span class="txt">{m}</span>' for m in messages)
    st.markdown(
        f'<div class="verdict {tone}"><span class="vd-pill" style="background:{color}">'
        f'{word}</span>{body}</div>', unsafe_allow_html=True)


def title_block(project, meta, items):
    st.markdown(
        f'<div class="tb"><div class="tb-head"><span class="tb-proj">{project}</span>'
        f'<span class="tb-meta">{meta}</span></div>'
        f'<div class="tb-grid">{_cells(items, "tb")}</div></div>',
        unsafe_allow_html=True)


def figure_strip(items):
    st.markdown(f'<div class="fs">{_cells(items, "fs")}</div>', unsafe_allow_html=True)


def donut(labels, values, colors, center, center_sub="", height=250):
    """Ring chart with the headline figure sitting in the hole."""
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.68, sort=False, direction="clockwise",
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        textinfo="none",
        hovertemplate="%{label}: %{value:,.0f} (%{percent})<extra></extra>"))
    fig.add_annotation(text=str(center), x=0.5, y=0.55, showarrow=False,
                       font=dict(size=26, color=INK, family="IBM Plex Sans, sans-serif"))
    if center_sub:
        fig.add_annotation(text=center_sub, x=0.5, y=0.36, showarrow=False,
                           font=dict(size=11, color=SLATE, family="IBM Plex Sans, sans-serif"))
    fig.update_layout(
        height=height, margin=dict(l=6, r=6, t=8, b=42),
        paper_bgcolor="white", showlegend=True,
        legend=dict(orientation="h", y=-0.06, x=0.5, xanchor="center",
                    font=dict(size=10.5, color=SLATE)),
        hoverlabel=dict(bgcolor="white", bordercolor=RULE,
                        font=dict(family="IBM Plex Sans, sans-serif", size=12, color=INK)))
    return fig


def section(title, note="", tight=False):
    cls = "sec tight" if tight else "sec"
    body = f'<p>{note}</p>' if note else ""
    st.markdown(f'<div class="{cls}"><h3>{title}</h3>{body}</div>', unsafe_allow_html=True)


# =============================================================================
# 1. XER PARSER
# =============================================================================

STATUS_LABELS = {"TK_NotStart": "Not started", "TK_Active": "In progress", "TK_Complete": "Complete"}
TYPE_LABELS = {
    "TT_Task": "Task", "TT_Rsrc": "Resource dependent", "TT_Mile": "Start milestone",
    "TT_FinMile": "Finish milestone", "TT_LOE": "Level of Effort", "TT_WBS": "WBS summary",
}
REL_LABELS = {"PR_FS": "FS", "PR_SS": "SS", "PR_FF": "FF", "PR_SF": "SF"}
HARD_CSTR = {"CS_MANDSTART", "CS_MANDFIN", "CS_MSO", "CS_MEO"}
MILESTONE_TYPES = {"TT_Mile", "TT_FinMile"}


def _decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1254", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def _frame(columns, rows):
    if not columns:
        return pd.DataFrame()
    fixed = []
    n = len(columns)
    for r in rows:
        if len(r) < n:
            r = r + [""] * (n - len(r))
        elif len(r) > n:
            r = r[:n]
        fixed.append(r)
    return pd.DataFrame(fixed, columns=columns)


@st.cache_data(show_spinner=False)
def parse_xer(raw: bytes) -> dict:
    """Turn an XER file into a {table name: DataFrame} dictionary."""
    text = _decode(raw)
    tables, cur, cols, rows = {}, None, [], []

    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        tag = parts[0].strip()

        if tag == "%T":
            if cur:
                tables[cur] = _frame(cols, rows)
            cur, cols, rows = parts[1].strip(), [], []
        elif tag == "%F" and cur:
            cols = [c.strip() for c in parts[1:]]
        elif tag == "%R" and cur:
            rows.append(parts[1:])
        elif tag == "%E":
            if cur:
                tables[cur] = _frame(cols, rows)
            cur, cols, rows = None, [], []

    if cur:
        tables[cur] = _frame(cols, rows)
    return tables


def num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0.0)


def dt(s):
    return pd.to_datetime(s, errors="coerce")


def col_or(df, name, default=None):
    """Return the column, or a Series filled with a default if it is missing."""
    if name in df.columns:
        return df[name]
    return pd.Series([default] * len(df), index=df.index)


# =============================================================================
# 2. MODEL BUILD
# =============================================================================

def build_wbs_paths(df_wbs: pd.DataFrame, max_levels: int = 6) -> pd.DataFrame:
    """Flatten the WBS hierarchy. Level 0 is the project node itself, level 1 the
    packages directly under it, and so on. An activity sitting higher than the
    requested level reports its own deepest node, so no row is ever blank."""
    cols = ["wbs_id", "WBS_Name", "WBS_Path", "WBS_Depth"] + [f"WBS_L{i}" for i in range(max_levels)]
    if df_wbs.empty:
        return pd.DataFrame(columns=cols)

    name_col = "wbs_name" if "wbs_name" in df_wbs.columns else "wbs_short_name"
    w = df_wbs.copy()
    w["_name"] = col_or(w, name_col, "").astype(str)
    parents = dict(zip(w["wbs_id"], col_or(w, "parent_wbs_id", "").astype(str)))
    names = dict(zip(w["wbs_id"], w["_name"]))

    def chain(wid):
        out, seen = [], set()
        while wid in names and wid not in seen:
            seen.add(wid)
            out.append(names[wid])
            wid = parents.get(wid, "")
        return list(reversed(out))

    paths = {wid: chain(wid) for wid in w["wbs_id"]}
    w["WBS_Path"] = w["wbs_id"].map(lambda x: " > ".join(paths[x]))
    w["WBS_Depth"] = w["wbs_id"].map(lambda x: len(paths[x]))
    for i in range(max_levels):
        w[f"WBS_L{i}"] = w["wbs_id"].map(
            lambda x, i=i: paths[x][i] if len(paths[x]) > i else (paths[x][-1] if paths[x] else ""))
    w["WBS_Name"] = w["_name"]
    return w[cols]


def pct_complete(row) -> float:
    """Physical progress, respecting the P6 percent-complete type."""
    if row["status_code"] == "TK_Complete":
        return 100.0
    if row["status_code"] == "TK_NotStart":
        return 0.0
    t = row.get("complete_pct_type", "")
    if t == "CP_Phys":
        return float(row.get("phys_complete_pct", 0) or 0)
    if t == "CP_Units":
        tq = row.get("_target_qty", 0) or 0
        aq = row.get("_act_qty", 0) or 0
        return min(100.0, (aq / tq * 100) if tq > 0 else 0.0)
    # CP_Drtn or unknown -> duration based
    td = row.get("target_drtn_hr_cnt", 0) or 0
    rd = row.get("remain_drtn_hr_cnt", 0) or 0
    if td > 0:
        return float(np.clip((td - rd) / td * 100, 0, 100))
    return float(row.get("phys_complete_pct", 0) or 0)


def build_model(_tables: dict, proj_id: str, weight_basis: str) -> dict:
    """Build an enriched activity table from the raw XER tables."""
    tables = _tables
    df_task = tables["TASK"].copy()
    df_proj = tables["PROJECT"].copy()
    df_wbs = tables.get("PROJWBS", pd.DataFrame()).copy()
    df_pred = tables.get("TASKPRED", pd.DataFrame()).copy()
    df_rsrc_asg = tables.get("TASKRSRC", pd.DataFrame()).copy()
    df_rsrc = tables.get("RSRC", pd.DataFrame()).copy()

    df_task = df_task[df_task["proj_id"] == proj_id].copy()
    proj_row = df_proj[df_proj["proj_id"] == proj_id].iloc[0]

    # --- calendar / data date -----------------------------------------------
    day_hr = float(pd.to_numeric(proj_row.get("day_hr_cnt", 8), errors="coerce") or 8)
    data_date = pd.to_datetime(proj_row.get("last_recalc_date"), errors="coerce")
    if pd.isna(data_date):
        data_date = pd.to_datetime(proj_row.get("plan_start_date"), errors="coerce")
    if pd.isna(data_date):
        data_date = pd.Timestamp.today().normalize()

    # --- dates --------------------------------------------------------------
    for c in ["target_start_date", "target_end_date", "act_start_date", "act_end_date",
              "early_start_date", "early_end_date", "late_start_date", "late_end_date",
              "reend_date", "restart_date", "cstr_date", "cstr_date2"]:
        if c in df_task.columns:
            df_task[c] = dt(df_task[c])
        else:
            df_task[c] = pd.NaT

    for c in ["total_float_hr_cnt", "free_float_hr_cnt", "target_drtn_hr_cnt",
              "remain_drtn_hr_cnt", "phys_complete_pct"]:
        df_task[c] = num(col_or(df_task, c, 0))

    df_task["status_code"] = col_or(df_task, "status_code", "TK_NotStart").astype(str)
    df_task["task_type"] = col_or(df_task, "task_type", "TT_Task").astype(str)
    df_task["complete_pct_type"] = col_or(df_task, "complete_pct_type", "CP_Drtn").astype(str)
    df_task["cstr_type"] = col_or(df_task, "cstr_type", "").astype(str)
    df_task["task_code"] = col_or(df_task, "task_code", "").astype(str)
    df_task["task_name"] = col_or(df_task, "task_name", "").astype(str)

    # --- resource / cost assignments ----------------------------------------
    if not df_rsrc_asg.empty:
        for c in ["target_cost", "act_reg_cost", "act_ot_cost", "remain_cost",
                  "target_qty", "act_reg_qty", "act_ot_qty", "remain_qty"]:
            df_rsrc_asg[c] = num(col_or(df_rsrc_asg, c, 0))
        agg = df_rsrc_asg.groupby("task_id").agg(
            _target_cost=("target_cost", "sum"),
            _act_cost=("act_reg_cost", "sum"),
            _act_ot_cost=("act_ot_cost", "sum"),
            _rem_cost=("remain_cost", "sum"),
            _target_qty=("target_qty", "sum"),
            _act_qty=("act_reg_qty", "sum"),
            _act_ot_qty=("act_ot_qty", "sum"),
            _rem_qty=("remain_qty", "sum"),
            _rsrc_cnt=("rsrc_id", "count"),
        ).reset_index()
        agg["_act_cost"] += agg["_act_ot_cost"]
        agg["_act_qty"] += agg["_act_ot_qty"]
        df_task = df_task.merge(agg, on="task_id", how="left")

    for c in ["_target_cost", "_act_cost", "_rem_cost", "_target_qty", "_act_qty", "_rem_qty", "_rsrc_cnt"]:
        df_task[c] = num(col_or(df_task, c, 0))

    # --- weighting basis (BAC) ----------------------------------------------
    has_cost = df_task["_target_cost"].sum() > 0
    has_qty = df_task["_target_qty"].sum() > 0

    if weight_basis == "Auto":
        basis = "Cost" if has_cost else ("Man-hours" if has_qty else "Duration")
    else:
        basis = weight_basis

    if basis == "Cost" and has_cost:
        df_task["BAC"] = df_task["_target_cost"]
        df_task["AC"] = df_task["_act_cost"]
        unit = "Cost"
    elif basis == "Man-hours" and has_qty:
        df_task["BAC"] = df_task["_target_qty"]
        df_task["AC"] = df_task["_act_qty"]
        unit = "Man-hours"
    else:
        df_task["BAC"] = df_task["target_drtn_hr_cnt"].replace(0, np.nan).fillna(day_hr)
        df_task["AC"] = df_task["BAC"] * df_task["phys_complete_pct"] / 100.0
        unit = "Duration-hours (weight)"
        basis = "Duration"

    # --- progress -----------------------------------------------------------
    df_task["Actual_Pct"] = df_task.apply(pct_complete, axis=1)
    df_task["EV"] = df_task["BAC"] * df_task["Actual_Pct"] / 100.0

    # --- planned progress at the data date ----------------------------------
    ts, te = df_task["target_start_date"], df_task["target_end_date"]
    span = (te - ts).dt.days.astype(float)
    elapsed = (data_date - ts).dt.days.astype(float)
    ratio = np.where(span > 0, elapsed / span.replace(0, np.nan) * 100.0, 0.0)
    planned = pd.Series(ratio, index=df_task.index).clip(0, 100)
    planned = planned.mask(data_date >= te, 100.0)
    planned = planned.mask(data_date <= ts, 0.0)
    df_task["Planned_Pct"] = planned.fillna(0.0)
    df_task["PV"] = df_task["BAC"] * df_task["Planned_Pct"] / 100.0

    # --- durations / float in days ------------------------------------------
    df_task["Total_Float_d"] = df_task["total_float_hr_cnt"] / day_hr
    df_task["Free_Float_d"] = df_task["free_float_hr_cnt"] / day_hr
    df_task["Orig_Dur_d"] = df_task["target_drtn_hr_cnt"] / day_hr
    df_task["Rem_Dur_d"] = df_task["remain_drtn_hr_cnt"] / day_hr

    df_task["Is_Critical"] = np.where(df_task["Total_Float_d"] <= 0, "Critical", "Not critical")
    if "driving_path_flag" in df_task.columns:
        df_task.loc[df_task["driving_path_flag"].astype(str) == "Y", "Is_Critical"] = "Critical"

    df_task["Status"] = df_task["status_code"].map(STATUS_LABELS).fillna("Unknown")
    df_task["Type"] = df_task["task_type"].map(TYPE_LABELS).fillna("Task")
    df_task["Is_Milestone"] = df_task["task_type"].isin(MILESTONE_TYPES)

    # --- display dates: actual if finished, otherwise early/planned ---------
    df_task["Start"] = df_task["act_start_date"].fillna(
        df_task["early_start_date"].fillna(df_task["target_start_date"]))
    df_task["Finish"] = df_task["act_end_date"].fillna(
        df_task["early_end_date"].fillna(df_task["target_end_date"]))
    df_task["BL_Start"] = df_task["target_start_date"]
    df_task["BL_Finish"] = df_task["target_end_date"]

    # Remaining early dates (P6: restart_date / reend_date). These are what P6
    # itself filters on when you build a lookahead, so keep them separate from
    # the display dates above.
    df_task["RES"] = df_task["restart_date"].fillna(
        df_task["early_start_date"]).fillna(df_task["Start"])
    df_task["REF"] = df_task["reend_date"].fillna(
        df_task["early_end_date"]).fillna(df_task["Finish"])
    started = df_task["act_start_date"].notna()
    df_task.loc[started, "RES"] = df_task.loc[started, "RES"].fillna(data_date)

    df_task["Start_Var_d"] = (df_task["Start"] - df_task["BL_Start"]).dt.days
    df_task["Finish_Var_d"] = (df_task["Finish"] - df_task["BL_Finish"]).dt.days

    # --- WBS ----------------------------------------------------------------
    wbs = build_wbs_paths(df_wbs[df_wbs["proj_id"] == proj_id] if "proj_id" in df_wbs.columns else df_wbs)
    if not wbs.empty:
        df_task = df_task.merge(wbs, on="wbs_id", how="left")
    level_cols = [c for c in df_task.columns if c.startswith("WBS_L") and c[5:].isdigit()]
    for c in ["WBS_Name", "WBS_Path"] + level_cols:
        df_task[c] = col_or(df_task, c, "Unassigned").fillna("Unassigned").replace("", "Unassigned")
    if not level_cols:
        df_task["WBS_L0"] = "Unassigned"

    # --- relationships ------------------------------------------------------
    if not df_pred.empty:
        df_pred = df_pred[df_pred["task_id"].isin(df_task["task_id"])].copy()
        df_pred["lag_d"] = num(col_or(df_pred, "lag_hr_cnt", 0)) / day_hr
        df_pred["Rel"] = col_or(df_pred, "pred_type", "PR_FS").map(REL_LABELS).fillna("FS")
        succ = df_pred.groupby("task_id").size().rename("Pred_Cnt")
        pred = df_pred.groupby("pred_task_id").size().rename("Succ_Cnt")
        df_task = df_task.merge(succ, left_on="task_id", right_index=True, how="left")
        df_task = df_task.merge(pred, left_on="task_id", right_index=True, how="left")
    df_task["Pred_Cnt"] = num(col_or(df_task, "Pred_Cnt", 0))
    df_task["Succ_Cnt"] = num(col_or(df_task, "Succ_Cnt", 0))

    # --- activity codes -----------------------------------------------------
    code_map = {}
    if all(t in tables for t in ("TASKACTV", "ACTVCODE", "ACTVTYPE")):
        ta, ac, at = tables["TASKACTV"], tables["ACTVCODE"], tables["ACTVTYPE"]
        try:
            j = ta.merge(ac, on="actv_code_id", how="left", suffixes=("", "_c"))
            j = j.merge(at, on="actv_code_type_id", how="left", suffixes=("", "_t"))
            name_col = "actv_code_name" if "actv_code_name" in j.columns else "short_name"
            for tname, grp in j.groupby("actv_code_type"):
                m = grp.drop_duplicates("task_id").set_index("task_id")[name_col]
                col = f"AC: {tname}"
                df_task[col] = df_task["task_id"].map(m).fillna("(none)")
                code_map[tname] = col
        except Exception:
            code_map = {}

    return {
        "tasks": df_task,
        "preds": df_pred,
        "rsrc_asg": df_rsrc_asg,
        "rsrc": df_rsrc,
        "project": proj_row,
        "data_date": data_date,
        "day_hr": day_hr,
        "unit": unit,
        "basis": basis,
        "code_map": code_map,
    }


# =============================================================================
# 3. TIME-PHASED CURVES (S-CURVE ENGINE)
# =============================================================================

def spread_daily(starts, ends, amounts, grid):
    """Spread amounts evenly between start and finish, returning a daily series.
    Uses a difference array, so it stays O(n) on large schedules."""
    n = len(grid)
    daily = np.zeros(n + 2)
    g0 = grid[0]
    s = pd.to_datetime(pd.Series(starts)).values
    e = pd.to_datetime(pd.Series(ends)).values
    a = np.asarray(amounts, dtype=float)

    ok = ~(pd.isna(s) | pd.isna(e)) & (a != 0)
    if ok.sum() == 0:
        return pd.Series(np.zeros(n), index=grid)

    si = ((s[ok] - np.datetime64(g0)) / np.timedelta64(1, "D")).astype(int)
    ei = ((e[ok] - np.datetime64(g0)) / np.timedelta64(1, "D")).astype(int)
    av = a[ok]

    ei = np.maximum(ei, si)
    dur = (ei - si + 1).astype(float)
    rate = av / dur

    si_c = np.clip(si, 0, n - 1)
    ei_c = np.clip(ei, 0, n - 1)
    # Anything outside the grid is clipped; the daily rate is preserved
    np.add.at(daily, si_c, rate)
    np.add.at(daily, ei_c + 1, -rate)

    return pd.Series(np.cumsum(daily)[:n], index=grid)


def build_curves(df, data_date, freq="W"):
    """Build time-phased PV / EV / AC / ETC curves."""
    dates = pd.concat([df["BL_Start"], df["BL_Finish"], df["Start"], df["Finish"]]).dropna()
    if dates.empty:
        return None
    lo = min(dates.min(), data_date).normalize()
    hi = max(dates.max(), data_date).normalize()
    grid = pd.date_range(lo, hi, freq="D")

    pv = spread_daily(df["BL_Start"], df["BL_Finish"], df["BAC"], grid)

    # EV and AC are spread over the worked window and cut off at the data date
    ev_start = df["act_start_date"].fillna(df["BL_Start"])
    ev_end = df["act_end_date"].fillna(pd.Series([data_date] * len(df), index=df.index))
    ev_end = ev_end.where(ev_end <= data_date, data_date)
    ev = spread_daily(ev_start, ev_end, df["EV"], grid)
    ac = spread_daily(ev_start, ev_end, df["AC"], grid)

    # Remaining work (ETC) - forecast beyond the data date
    rem_start = df["Start"].where(df["Start"] > data_date, data_date)
    rem_end = df["Finish"].where(df["Finish"] > data_date, data_date + pd.Timedelta(days=1))
    etc = spread_daily(rem_start, rem_end, (df["BAC"] - df["EV"]).clip(lower=0), grid)

    out = pd.DataFrame({"Date": grid, "PV_d": pv.values, "EV_d": ev.values,
                        "AC_d": ac.values, "ETC_d": etc.values})
    out["PV"] = out["PV_d"].cumsum()
    out["EV"] = out["EV_d"].cumsum()
    out["AC"] = out["AC_d"].cumsum()

    future = out["Date"] >= data_date
    ev_at_dd = float(out.loc[~future, "EV"].max()) if (~future).any() else 0.0
    if not np.isfinite(ev_at_dd):
        ev_at_dd = 0.0
    etc_cum = out.loc[future, "ETC_d"].cumsum()
    out["Forecast"] = np.nan
    out.loc[future, "Forecast"] = ev_at_dd + etc_cum
    out.loc[future & (out["Date"] > data_date), ["EV", "AC"]] = np.nan
    return out


def earned_schedule(curve, ev_total, data_date):
    """Earned Schedule (ES) and SPI(t)."""
    if curve is None or curve.empty or ev_total <= 0:
        return np.nan, np.nan
    c = curve[["Date", "PV"]].dropna()
    hit = c[c["PV"] >= ev_total]
    if hit.empty:
        return np.nan, np.nan
    es_date = hit["Date"].iloc[0]
    start = c["Date"].iloc[0]
    es = (es_date - start).days
    at = (data_date - start).days
    return es, (es / at if at > 0 else np.nan)


# =============================================================================
# 4. DCMA 14-POINT SCHEDULE QUALITY CHECK
# =============================================================================

def dcma_checks(df, preds, data_date, day_hr):
    res = []
    base = df[~df["task_type"].isin(["TT_LOE", "TT_WBS"])]
    n = max(len(base), 1)

    def add(no, name, value, target, ok, detail=""):
        res.append({"#": no, "Check": name, "Sonuc": value, "Target": target,
                    "Status": "Pass" if ok else "Fail", "Detail": detail})

    # 1 - Logic (missing predecessor/successor)
    miss = base[(base["Pred_Cnt"] == 0) | (base["Succ_Cnt"] == 0)]
    p = len(miss) / n * 100
    add(1, "Missing logic", f"{p:.1f}%", "<= 5%", p <= 5, f"{len(miss)} activities missing a predecessor or successor")

    if not preds.empty:
        # 2 - Leads (negative lag)
        leads = preds[preds["lag_d"] < 0]
        p = len(leads) / max(len(preds), 1) * 100
        add(2, "Leads (negative lag)", f"{p:.1f}%", "0%", len(leads) == 0, f"{len(leads)} relationships")

        # 3 - Lags
        lags = preds[preds["lag_d"] > 0]
        p = len(lags) / max(len(preds), 1) * 100
        add(3, "Lags", f"{p:.1f}%", "<= 5%", p <= 5, f"{len(lags)} relationships")

        # 4 - FS share
        fs = (preds["Rel"] == "FS").sum()
        p = fs / max(len(preds), 1) * 100
        add(4, "FS relationship share", f"{p:.1f}%", ">= 90%", p >= 90, f"{fs} of {len(preds)} relationships are FS")
    else:
        for i, nm in [(2, "Leads (negative lag)"), (3, "Lags"), (4, "FS relationship share")]:
            add(i, nm, "no data", "-", False, "TASKPRED table not found")

    # 5 - Hard constraints
    hard = base[base["cstr_type"].isin(HARD_CSTR)]
    p = len(hard) / n * 100
    add(5, "Hard constraints", f"{p:.1f}%", "<= 5%", p <= 5, f"{len(hard)} activities")

    # 6 - High float
    open_t = base[base["status_code"] != "TK_Complete"]
    hf = open_t[open_t["Total_Float_d"] > 44]
    p = len(hf) / max(len(open_t), 1) * 100
    add(6, "High total float (>44d)", f"{p:.1f}%", "<= 5%", p <= 5, f"{len(hf)} activities")

    # 7 - Negative float
    nf = open_t[open_t["Total_Float_d"] < 0]
    p = len(nf) / max(len(open_t), 1) * 100
    add(7, "Negative float", f"{p:.1f}%", "0%", len(nf) == 0, f"{len(nf)} activities under schedule pressure")

    # 8 - High duration
    hd = open_t[open_t["Rem_Dur_d"] > 44]
    p = len(hd) / max(len(open_t), 1) * 100
    add(8, "High remaining duration (>44d)", f"{p:.1f}%", "<= 5%", p <= 5, f"{len(hd)} activities")

    # 9 - Invalid dates
    bad = base[
        ((base["act_start_date"] > data_date) & base["act_start_date"].notna())
        | ((base["act_end_date"] > data_date) & base["act_end_date"].notna())
        | ((base["status_code"] != "TK_Complete") & (base["Finish"] < data_date) & base["Finish"].notna())
    ]
    add(9, "Invalid dates", f"{len(bad)} found", "0", len(bad) == 0, "Actual date after data date, or open work left in the past")

    # 10 - Resource assignment
    need = base[(base["Orig_Dur_d"] > 0) & (~base["Is_Milestone"])]
    nores = need[need["_rsrc_cnt"] == 0] if "_rsrc_cnt" in need.columns else need
    p = len(nores) / max(len(need), 1) * 100
    add(10, "No resource or cost assigned", f"{p:.1f}%", "<= 5%", p <= 5, f"{len(nores)} activities")

    # 11 - Missed tasks
    done_late = base[(base["status_code"] == "TK_Complete") & (base["act_end_date"] > base["BL_Finish"])]
    late_open = base[(base["status_code"] != "TK_Complete") & (base["BL_Finish"] < data_date)]
    missed = len(done_late) + len(late_open)
    should = base[base["BL_Finish"] <= data_date]
    p = missed / max(len(should), 1) * 100
    add(11, "Missed tasks", f"{p:.1f}%", "<= 5%", p <= 5, f"{missed} activities passed their planned finish")

    # 12 - Critical path test (manual)
    add(12, "Critical path test", "manual", "-", True, "Add an artificial delay to a critical activity and confirm the project finish moves")

    # 13 - CPLI
    fin = base["Finish"].max()
    pd_days = (fin - data_date).days if pd.notna(fin) else 0
    tf_fin = base.loc[base["Finish"] == fin, "Total_Float_d"].min() if pd.notna(fin) else 0
    cpli = (pd_days + (tf_fin or 0)) / pd_days if pd_days > 0 else np.nan
    add(13, "CPLI", f"{cpli:.2f}" if pd.notna(cpli) else "-", ">= 0.95",
        bool(pd.notna(cpli) and cpli >= 0.95), f"Remaining project duration {pd_days} days")

    # 14 - BEI
    completed = (base["status_code"] == "TK_Complete").sum()
    bei = completed / max(len(should), 1)
    add(14, "BEI (Baseline Execution Index)", f"{bei:.2f}", ">= 0.95", bei >= 0.95,
        f"{completed} complete of {len(should)} that should be complete")

    return pd.DataFrame(res)


# =============================================================================
# 5. CHART HELPERS
# =============================================================================

def vline(fig, x, text="Data Date", color=ALERT):
    fig.add_shape(type="line", x0=x, x1=x, y0=0, y1=1, yref="paper",
                  line=dict(color=color, width=2, dash="dash"))
    fig.add_annotation(x=x, y=1.03, yref="paper", text=text, showarrow=False,
                       font=dict(color=color, size=11))
    return fig


def style(fig, height=430, hover="x unified"):
    fig.update_layout(
        height=height, margin=dict(l=8, r=12, t=44, b=8),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(color=INK, size=12, family="IBM Plex Sans, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(size=11, color=SLATE)),
        hoverlabel=dict(bgcolor="white", bordercolor=RULE,
                        font=dict(family="IBM Plex Sans, sans-serif", size=12, color=INK)),
        hovermode=hover,
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=RULE,
                     tickfont=dict(size=11, color=SLATE),
                     title_font=dict(size=11, color=SLATE))
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=RULE,
                     tickfont=dict(size=11, color=SLATE),
                     title_font=dict(size=11, color=SLATE))
    return fig


# =============================================================================
# 5b. P6-STYLE GANTT
# =============================================================================

BAR_H = 0.34          # activity bar half-height
BASE_H = 0.13         # baseline bar half-height
ROW_PX = 21           # pixels per row
BAND = "#F6F9FB"      # alternating group band
REMAIN = "#BBD4E3"    # remaining (unworked) portion, non-critical
REMAIN_CR = "#EDC0BC"  # remaining portion, critical
SUMMARY = "#3A5566"   # WBS summary bar


def _ms(delta):
    """Timedelta -> milliseconds, the unit a datetime x-axis expects for bar length."""
    return delta.dt.total_seconds().values * 1000.0


def gantt_figure(d, data_date, group_col=None, show_baseline=True, show_links=False,
                 preds=None, x_range=None, row_limit=250):
    """Primavera-style bar chart: WBS bands, split progress bars, baseline
    shadows, milestone diamonds and optional relationship lines."""
    d = d.copy()
    if len(d) > row_limit:
        d = d.head(row_limit)

    # --- row layout: WBS group header followed by its activities --------------
    rows = []
    if group_col and group_col in d.columns:
        for gname, grp in d.groupby(group_col, sort=True):
            grp = grp.sort_values(["Start", "task_code"])
            rows.append({"kind": "group", "label": str(gname),
                         "start": grp["Start"].min(), "finish": grp["Finish"].max(),
                         "count": len(grp)})
            for _, r in grp.iterrows():
                rows.append({"kind": "task", "r": r})
    else:
        for _, r in d.sort_values(["Start", "task_code"]).iterrows():
            rows.append({"kind": "task", "r": r})

    n = len(rows)
    if n == 0:
        return None

    ticks, tick_y, shapes = [], [], []
    band_on, band_start = False, 0

    for y, row in enumerate(rows):
        tick_y.append(y)
        if row["kind"] == "group":
            ticks.append(f"<b>{row['label'][:40]}</b>")
            if band_on:
                shapes.append(dict(type="rect", xref="paper", x0=0, x1=1, yref="y",
                                   y0=band_start - .5, y1=y - .5, fillcolor=BAND,
                                   line_width=0, layer="below"))
            band_on = not band_on
            band_start = y
        else:
            r = row["r"]
            ticks.append(f"{r['task_code']}  {str(r['task_name'])[:38]}")
    if band_on:
        shapes.append(dict(type="rect", xref="paper", x0=0, x1=1, yref="y",
                           y0=band_start - .5, y1=n - .5, fillcolor=BAND,
                           line_width=0, layer="below"))

    idx = {}          # task_id -> (y, start, finish)
    groups = {"y": [], "base": [], "len": [], "text": []}
    bars = {k: {"y": [], "base": [], "len": [], "cd": []}
            for k in ("done", "remain", "done_cr", "remain_cr", "bl")}
    mile = {"y": [], "x": [], "cd": [], "color": []}

    for y, row in enumerate(rows):
        if row["kind"] == "group":
            s, f = row["start"], row["finish"]
            if pd.notna(s) and pd.notna(f):
                groups["y"].append(y)
                groups["base"].append(s)
                groups["len"].append(max((f - s).total_seconds() * 1000.0, 8.64e7))
                groups["text"].append(f"{row['label']} — {row['count']} activities")
            continue

        r = row["r"]
        s, f = r["Start"], r["Finish"]
        if pd.isna(s) or pd.isna(f):
            continue
        idx[r["task_id"]] = (y, s, f)
        cd = [r["task_code"], str(r["task_name"])[:60], r["WBS_Path"],
              s.strftime("%d %b %Y"), f.strftime("%d %b %Y"),
              round(float(r["Actual_Pct"]), 1), round(float(r["Total_Float_d"]), 1),
              r["Status"]]

        if r["Is_Milestone"]:
            mile["y"].append(y)
            mile["x"].append(f)
            mile["cd"].append(cd)
            mile["color"].append(ALERT if r["Is_Critical"] == "Critical" else INK)
            continue

        total = max((f - s).total_seconds() * 1000.0, 8.64e7)
        pct = float(np.clip(r["Actual_Pct"], 0, 100)) / 100.0
        crit = r["Is_Critical"] == "Critical"
        dk, rk = ("done_cr", "remain_cr") if crit else ("done", "remain")

        if pct > 0:
            bars[dk]["y"].append(y); bars[dk]["base"].append(s)
            bars[dk]["len"].append(total * pct); bars[dk]["cd"].append(cd)
        if pct < 1:
            bars[rk]["y"].append(y)
            bars[rk]["base"].append(s + pd.Timedelta(milliseconds=total * pct))
            bars[rk]["len"].append(total * (1 - pct)); bars[rk]["cd"].append(cd)

        if show_baseline and pd.notna(r["BL_Start"]) and pd.notna(r["BL_Finish"]):
            bs, bf = r["BL_Start"], r["BL_Finish"]
            bars["bl"]["y"].append(y); bars["bl"]["base"].append(bs)
            bars["bl"]["len"].append(max((bf - bs).total_seconds() * 1000.0, 8.64e7))
            bars["bl"]["cd"].append([r["task_code"], bs.strftime("%d %b %Y"),
                                     bf.strftime("%d %b %Y")])

    fig = go.Figure()
    HT = ("<b>%{customdata[0]}</b>  %{customdata[1]}<br>%{customdata[2]}<br>"
          "%{customdata[3]} → %{customdata[4]}<br>"
          "Complete %{customdata[5]}%  ·  Float %{customdata[6]}d  ·  %{customdata[7]}"
          "<extra></extra>")

    # baseline shadow sits under the activity bar
    if bars["bl"]["y"]:
        fig.add_trace(go.Bar(
            y=[v + 0.30 for v in bars["bl"]["y"]], base=bars["bl"]["base"],
            x=bars["bl"]["len"], orientation="h", width=BASE_H * 2,
            marker=dict(color="#CBD5DC"), name="Baseline",
            customdata=bars["bl"]["cd"],
            hovertemplate="Baseline %{customdata[1]} → %{customdata[2]}<extra></extra>"))

    for key, color, label, show in (
        ("remain", REMAIN, "Remaining", True),
        ("done", PLANNED, "Progress", True),
        ("remain_cr", REMAIN_CR, "Remaining · critical", True),
        ("done_cr", ALERT, "Progress · critical", True),
    ):
        if bars[key]["y"]:
            fig.add_trace(go.Bar(
                y=[v - 0.06 for v in bars[key]["y"]], base=bars[key]["base"],
                x=bars[key]["len"], orientation="h", width=BAR_H * 2,
                marker=dict(color=color, line=dict(width=0)), name=label,
                showlegend=show, customdata=bars[key]["cd"], hovertemplate=HT))

    if groups["y"]:
        fig.add_trace(go.Bar(
            y=groups["y"], base=groups["base"], x=groups["len"], orientation="h",
            width=0.22, marker=dict(color=SUMMARY), name="WBS summary",
            text=groups["text"], hovertemplate="%{text}<extra></extra>"))

    if mile["y"]:
        fig.add_trace(go.Scatter(
            x=mile["x"], y=mile["y"], mode="markers", name="Milestone",
            marker=dict(symbol="diamond", size=11, color=mile["color"],
                        line=dict(color="white", width=1)),
            customdata=mile["cd"], hovertemplate=HT))

    # relationship lines between visible activities
    if show_links and preds is not None and not preds.empty:
        lx, ly, drawn = [], [], 0
        for _, p in preds.iterrows():
            if drawn >= 400:
                break
            a, b = idx.get(p["pred_task_id"]), idx.get(p["task_id"])
            if not a or not b:
                continue
            (py, _, pf), (sy, ss, _) = a, b
            lx += [pf, pf, ss, None]
            ly += [py, sy, sy, None]
            drawn += 1
        if lx:
            fig.add_trace(go.Scatter(x=lx, y=ly, mode="lines", name="Logic",
                                     line=dict(color="#9BAAB6", width=1),
                                     hoverinfo="skip", showlegend=False))

    shapes.append(dict(type="line", x0=data_date, x1=data_date, yref="paper", y0=0, y1=1,
                       line=dict(color=ALERT, width=2)))

    # timescale granularity follows the span on screen, as P6 does
    if x_range is not None:
        span_days = (pd.Timestamp(x_range[1]) - pd.Timestamp(x_range[0])).days
    else:
        allx = [b for b in bars["remain"]["base"] + bars["done"]["base"] +
                bars["remain_cr"]["base"] + bars["done_cr"]["base"] if pd.notna(b)]
        span_days = (max(allx) - min(allx)).days if allx else 90
    if span_days <= 45:
        tick_step, tick_fmt = 7 * 86400000.0, "%d %b"
    elif span_days <= 240:
        tick_step, tick_fmt = "M1", "%b<br>%Y"
    elif span_days <= 900:
        tick_step, tick_fmt = "M3", "%b<br>%Y"
    else:
        tick_step, tick_fmt = "M6", "%b<br>%Y"

    height = int(np.clip(n * ROW_PX + 150, 340, 2400))
    fig.update_layout(
        barmode="overlay", height=height, shapes=shapes,
        margin=dict(l=8, r=24, t=54, b=46), bargap=0,
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(color=INK, size=11, family="IBM Plex Sans, sans-serif"),
        legend=dict(orientation="h", yanchor="top", y=-0.012, x=0,
                    font=dict(size=10.5, color=SLATE)),
        hoverlabel=dict(bgcolor="white", bordercolor=RULE,
                        font=dict(family="IBM Plex Sans, sans-serif", size=12, color=INK)),
        hovermode="closest",
        annotations=[dict(x=data_date, y=1.005, yref="paper", text="Data date",
                          showarrow=False, font=dict(color=ALERT, size=11), xanchor="left")],
    )
    fig.update_yaxes(autorange="reversed", tickmode="array", tickvals=tick_y,
                     ticktext=ticks, tickfont=dict(size=10, color=INK,
                                                   family="IBM Plex Mono, monospace"),
                     showgrid=False, zeroline=False, range=[n - .5, -.5],
                     showline=True, linecolor=RULE)
    fig.update_xaxes(type="date", side="top", showgrid=True, gridcolor=GRID, ticks="outside",
                     tickcolor=RULE, zeroline=False,
                     range=x_range, showline=True, linecolor=RULE,
                     tickfont=dict(size=10.5, color=SLATE), tickangle=0,
                     ticklabelmode="period", dtick=tick_step, tickformat=tick_fmt)
    return fig


def to_excel(sheets: dict) -> bytes:
    buf = io.BytesIO()
    engine = None
    for eng in ("xlsxwriter", "openpyxl"):
        try:
            __import__(eng)
            engine = eng
            break
        except ImportError:
            continue
    with pd.ExcelWriter(buf, engine=engine) as xl:
        for name, d in sheets.items():
            if d is None or d.empty:
                continue
            d.copy().to_excel(xl, sheet_name=name[:31], index=False)
    return buf.getvalue()



# =============================================================================
# 5c. ACCESS, PRIVACY AND CONTACT
# =============================================================================

def secret(key, default=None):
    """Read a Streamlit secret without exploding when no secrets file exists."""
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def require_access():
    """Optional shared-password gate. Dormant unless app_password is set in
    .streamlit/secrets.toml, so local runs are never blocked."""
    pw = secret("app_password")
    if not pw:
        return True
    if st.session_state.get("_granted"):
        return True
    st.markdown(
        '<div class="tb"><div class="tb-head">'
        '<span class="tb-proj">Construction Planning &amp; Control</span>'
        '<span class="tb-meta">Access restricted</span></div></div>',
        unsafe_allow_html=True)
    entered = st.text_input("Access code", type="password",
                            help="Ask the person who shared this link.")
    if entered and entered == pw:
        st.session_state["_granted"] = True
        st.rerun()
    elif entered:
        st.error("That code is not recognised.")
    st.stop()


PRIVACY = """
**Your schedule stays yours.**

- The .xer file you upload is read into memory to draw this dashboard. The app
  never writes it to disk and never sends it anywhere else.
- Parsing results live in the cache for your browser session only. Press
  **Clear my data** below, or close the tab, and they are dropped.
- Sessions are isolated. Nobody else using this link can see your project, your
  filters or your figures.
- Nothing is logged about the contents of your schedule: no activity names, no
  costs, no dates.
- No cookies are set for tracking and no usage analytics are collected.

Please only upload schedules you are permitted to share, and check your own
organisation's rules before putting commercially sensitive programmes on any
hosted service.
"""

CONTACT_NOTICE = """
**What happens to a message you send**

- Only the name, email address and text you type are transmitted. Your uploaded
  schedule is never attached, quoted or referenced in a message.
- A message becomes ordinary email. It is stored in the recipient's mailbox and
  on the mail provider's servers, including their backups, and it is not covered
  by the in-memory handling described above. Treat it as permanent.
- For that reason, do not paste activity names, costs, dates or anything else
  from a programme into the message. Describe the problem in general terms.
- Your name and email are used only to reply to you. They are not added to a
  mailing list, not shared, and not used for anything else.
- Messages are kept for {retention} and then deleted. To have yours removed
  sooner, or to ask what is held about you, reply to the same address.
- Data controller: {controller}.
"""


def contact_notice_text():
    return CONTACT_NOTICE.format(
        retention=secret("contact_retention", "as long as needed to answer you"),
        controller=secret("contact_controller",
                          "the person operating this deployment (see the address below)"))


APP_VERSION = "1.0"

ABOUT = """
A free tool for planning and project controls engineers. Upload a Primavera P6
`.xer` export and it builds the earned value picture, the critical path view, the
lookahead and a DCMA 14-point quality check in one pass. Nothing to install and
no account needed.

It reads your schedule; it never changes it. Figures are derived from the file
you upload, so check anything that matters against P6 itself before using it in a
contractual or commercial decision. Provided as-is, with no warranty.
"""


def privacy_and_contact():
    """Sidebar footer: what this is, confidentiality, data reset, contact route."""
    st.divider()
    with st.expander("About"):
        st.markdown(ABOUT)
        repo = secret("repo_url", "")
        if repo:
            st.markdown(f"[Source code and issue tracker]({repo})")
        st.caption(f"Version {APP_VERSION}")

    with st.expander("Privacy"):
        st.markdown(PRIVACY)
        if st.button("Clear my data", width="stretch"):
            st.cache_data.clear()
            for k in list(st.session_state.keys()):
                if k != "_granted":
                    del st.session_state[k]
            st.rerun()

    to = secret("contact_email", "")
    mode = secret("contact_mode", "auto")
    if mode == "off" or not to:
        return
    # Without SMTP credentials there is nothing to gain from a server-side form:
    # hand the visitor a mailto link so nothing passes through this app at all.
    if mode == "auto":
        mode = "form" if secret("smtp_host") else "mailto"

    with st.expander("Contact"):
        st.markdown(contact_notice_text())

        if mode == "mailto":
            st.markdown(f"**Email:** [{to}](mailto:{to})")
            st.caption("Opens in your own mail client. Nothing is sent through this app.")
            return

        with st.form("contact", clear_on_submit=True):
            c_name = st.text_input("Your name")
            c_from = st.text_input("Your email")
            c_subj = st.selectbox("Topic", ["Question", "Bug report", "Feature request",
                                            "Access request", "Something else"])
            c_body = st.text_area("Message", height=110,
                                  placeholder="Describe the issue in general terms.")
            st.caption("Do not paste schedule content here — activity names, costs or dates.")
            trap = st.text_input("Leave this field empty", key="_hp",
                                 label_visibility="collapsed", placeholder="")
            agree = st.checkbox("I agree to my name and email being used to reply to me.")
            sent = st.form_submit_button("Send", width="stretch")

        if sent:
            if trap:
                st.success("Message sent.")          # silent drop: automated submission
            elif not (c_from and c_body):
                st.warning("An email address and a message are needed.")
            elif "@" not in c_from:
                st.warning("That email address does not look right.")
            elif not agree:
                st.warning("Please tick the consent box before sending.")
            else:
                ok, err = send_mail(to, c_name, c_from, c_subj, c_body)
                if ok:
                    st.success("Message sent. You will get a reply at the address given.")
                elif err == "no_smtp":
                    st.info("Mail delivery is not configured on this deployment.")
                    st.markdown(f"[Open this message in your mail app]"
                                f"({mailto_link(to, c_subj, c_name, c_from, c_body)})")
                else:
                    st.error("The message could not be sent. Please email directly instead.")


def mailto_link(to, subject, name, sender, body):
    from urllib.parse import quote
    text = f"{body}\n\n—\n{name} <{sender}>"
    return f"mailto:{to}?subject={quote('[Planning dashboard] ' + subject)}&body={quote(text)}"


def send_mail(to, name, sender, subject, body):
    """Send through SMTP when credentials are configured, otherwise report back
    so the caller can fall back to a mailto link."""
    host = secret("smtp_host")
    if not (host and to):
        return False, "no_smtp"
    import smtplib
    from email.message import EmailMessage
    try:
        msg = EmailMessage()
        msg["Subject"] = f"[Planning dashboard] {subject}"
        msg["From"] = secret("smtp_user", sender)
        msg["To"] = to
        msg["Reply-To"] = sender
        msg.set_content(f"{body}\n\n---\nFrom: {name} <{sender}>")
        port = int(secret("smtp_port", 587))
        with smtplib.SMTP(host, port, timeout=20) as srv:
            srv.starttls()
            user, pwd = secret("smtp_user"), secret("smtp_password")
            if user and pwd:
                srv.login(user, pwd)
            srv.send_message(msg)
        return True, None
    except Exception as exc:
        return False, str(exc)


# =============================================================================
# 6. USER INTERFACE
# =============================================================================

require_access()

with st.sidebar:
    st.subheader("Data")
    up = st.file_uploader("Current schedule (.xer)", type=["xer"])
    up_bl = st.file_uploader("Baseline schedule (.xer) — optional", type=["xer"])
    st.caption("Upload a baseline to get activity-level date variances.")
    st.caption("Files are processed in memory and never stored. See Privacy below.")

if up is None:
    title_block("Construction Planning &amp; Control",
                "Primavera P6 · schedule, cost, resource and quality control",
                [{"label": "Status", "value": "Awaiting file"},
                 {"label": "Source", "value": ".xer export"},
                 {"label": "Scope", "value": "Single or multi-project"}])
    with st.sidebar:
        privacy_and_contact()
    st.info("Upload an .xer file from the sidebar to begin.")
    st.markdown(
        """
**What this dashboard covers**

| Tab | Contents |
|---|---|
| Overview | SPI, CPI, EAC, TCPI, Earned Schedule, progress and cash curve |
| Schedule | Gantt, milestones, 3/6-week lookahead, late activities |
| Critical Path | Float distribution, critical and negative-float work, longest path |
| Earned Value | EVM table by WBS, variance analysis, forecasts |
| Resources | Monthly or weekly man-hour histogram, resource breakdown |
| Schedule Quality | DCMA 14-point check |
| Baseline | Date and scope comparison between two schedules |
| Data | Activity table and Excel export |
"""    )
    st.stop()

tables = parse_xer(up.getvalue())

missing = [t for t in ("TASK", "PROJECT") if t not in tables]
if missing:
    st.error(f"Required tables are missing from the XER: {', '.join(missing)}. Export the file from P6 again.")
    st.stop()

# --- project selection --------------------------------------------------------
df_proj_all = tables["PROJECT"]
proj_ids = df_proj_all["proj_id"].tolist()
labels = {r["proj_id"]: f"{r.get('proj_short_name', r['proj_id'])}" for _, r in df_proj_all.iterrows()}

with st.sidebar:
    st.subheader("Scope")
    proj_id = st.selectbox("Project", proj_ids, format_func=lambda x: labels.get(x, x))
    weight_basis = st.radio("Weighting basis", ["Auto", "Cost", "Man-hours", "Duration"], horizontal=False,
                            help="What activity weights are based on in the EVM calculation.")

model = build_model(tables, proj_id, weight_basis)
tasks = model["tasks"]
data_date = model["data_date"]
unit = model["unit"]

if tasks.empty:
    st.error("No activities found in the selected project.")
    st.stop()

# --- filters ------------------------------------------------------------------
with st.sidebar:
    st.subheader("Filters")
    lvl_cols = sorted([c for c in tasks.columns if c.startswith("WBS_L") and c[5:].isdigit()],
                      key=lambda c: int(c[5:]))
    # Stop at the depth the schedule actually has: deeper levels would just
    # repeat the one above and clutter the list.
    keep, prev = [], None
    for c in lvl_cols:
        if prev is not None and tasks[c].equals(tasks[prev]):
            break
        keep.append(c)
        prev = c
    lvl_cols = keep or ["WBS_L0"]
    lvl_opts = lvl_cols + ["WBS_Path"]
    lvl_names = {c: (f"Level {c[5:]} · project" if c == "WBS_L0" else f"Level {c[5:]}")
                 for c in lvl_cols}
    lvl_names["WBS_Path"] = "Full path"
    default = 1 if len(lvl_cols) > 1 else 0
    lvl = st.selectbox("WBS level", lvl_opts, index=default,
                       format_func=lambda x: lvl_names[x],
                       help="Level 0 is the project itself, level 1 the packages directly "
                            "beneath it, and so on down the breakdown structure.")
    st.caption(f"{tasks[lvl].nunique()} group(s) at this level.")
    wbs_opts = sorted([w for w in tasks[lvl].dropna().unique() if w])
    sel_wbs = st.multiselect("WBS", wbs_opts, default=[], key=f"wbs_sel_{lvl}")
    sel_status = st.multiselect("Status", ["Not started", "In progress", "Complete"], default=[])
    only_crit = st.checkbox("Critical activities only", value=False)
    hide_loe = st.checkbox("Exclude LOE and summary rows", value=True)

    for cname, colname in model["code_map"].items():
        vals = sorted(tasks[colname].dropna().unique())
        if 1 < len(vals) <= 60:
            pick = st.multiselect(cname, vals, default=[])
            if pick:
                tasks = tasks[tasks[colname].isin(pick)]

df = tasks.copy()
if sel_wbs:
    df = df[df[lvl].isin(sel_wbs)]
if sel_status:
    df = df[df["Status"].isin(sel_status)]
if only_crit:
    df = df[df["Is_Critical"] == "Critical"]
if hide_loe:
    df = df[~df["task_type"].isin(["TT_LOE", "TT_WBS"])]

if df.empty:
    st.warning("No activities match the filters. Loosen the selection in the sidebar.")
    st.stop()

# --- headline indicators ------------------------------------------------------
BAC, PV, EV, AC = df["BAC"].sum(), df["PV"].sum(), df["EV"].sum(), df["AC"].sum()
SPI = EV / PV if PV > 0 else np.nan
CPI = EV / AC if AC > 0 else np.nan
SV, CV = EV - PV, EV - AC
EAC = BAC / CPI if CPI and CPI > 0 else BAC
ETC = max(EAC - AC, 0)
VAC = BAC - EAC
TCPI = (BAC - EV) / (BAC - AC) if (BAC - AC) != 0 else np.nan
plan_pct = PV / BAC * 100 if BAC > 0 else 0
act_pct = EV / BAC * 100 if BAC > 0 else 0

curve = build_curves(df, data_date)
ES, SPIt = earned_schedule(curve, EV, data_date)


def wbs_evm_table(d: pd.DataFrame, level_col: str) -> pd.DataFrame:
    t = d.groupby(level_col).agg(
        Activities=("task_id", "count"), BAC=("BAC", "sum"), PV=("PV", "sum"),
        EV=("EV", "sum"), AC=("AC", "sum")).reset_index()
    t["SV"] = t["EV"] - t["PV"]
    t["CV"] = t["EV"] - t["AC"]
    t["SPI"] = np.where(t["PV"] > 0, t["EV"] / t["PV"], np.nan)
    t["CPI"] = np.where(t["AC"] > 0, t["EV"] / t["AC"], np.nan)
    t["EAC"] = np.where(t["CPI"] > 0, t["BAC"] / t["CPI"], t["BAC"])
    t["VAC"] = t["BAC"] - t["EAC"]
    return t.sort_values("BAC", ascending=False).rename(columns={level_col: "WBS"})


wbs_evm = wbs_evm_table(df, lvl)
checks_df = dcma_checks(df, model["preds"], data_date, model["day_hr"])

proj_finish = df["Finish"].max()
bl_finish = df["BL_Finish"].max()
slip = (proj_finish - bl_finish).days if pd.notna(proj_finish) and pd.notna(bl_finish) else 0

tab_sum, tab_sch, tab_cp, tab_ev, tab_res, tab_q, tab_bl, tab_data = st.tabs(
    ["Overview", "Schedule", "Critical Path", "Earned Value", "Resources", "Schedule Quality", "Baseline", "Data"]
)

# -----------------------------------------------------------------------------
# OVERVIEW
# -----------------------------------------------------------------------------
with tab_sum:
    proj_name = labels.get(proj_id, proj_id) or "Project"
    scope = "all WBS" if not sel_wbs else f"{len(sel_wbs)} WBS selected"
    title_block(
        proj_name,
        f"Data date {data_date.strftime('%d %b %Y')} · {len(df):,} activities · "
        f"{scope} · weighted by {model['basis'].lower()}",
        [
            {"label": "Schedule performance (SPI)",
             "value": f"{SPI:.3f}" if pd.notna(SPI) else "—",
             "sub": f"SV {fmt(SV)}",
             "tone": "" if not pd.notna(SPI) else
                     ("good" if SPI >= 0.98 else ("warn" if SPI >= 0.92 else "bad")),
             "help": "Earned value divided by planned value. Below 1.00 means less work has "
                     "been earned than the plan called for by the data date."},
            {"label": "Cost performance (CPI)",
             "value": f"{CPI:.3f}" if pd.notna(CPI) else "—",
             "sub": f"CV {fmt(CV)}",
             "tone": "" if not pd.notna(CPI) else
                     ("good" if CPI >= 0.98 else ("warn" if CPI >= 0.92 else "bad")),
             "help": "Earned value divided by actual cost. Below 1.00 means the work is "
                     "costing more than budgeted."},
            {"label": "Planned progress", "value": f"{plan_pct:.1f}%", "sub": "to data date"},
            {"label": "Actual progress", "value": f"{act_pct:.1f}%",
             "sub": f"{act_pct - plan_pct:+.1f} pts vs plan",
             "tone": "good" if act_pct >= plan_pct else
                     ("warn" if act_pct >= plan_pct - 5 else "bad")},
            {"label": "Forecast finish",
             "value": proj_finish.strftime("%d %b %Y") if pd.notna(proj_finish) else "—",
             "sub": f"{slip:+d} days vs baseline" if pd.notna(proj_finish) else "",
             "tone": "good" if slip <= 0 else ("warn" if slip <= 14 else "bad")},
        ])

    figure_strip([
        {"label": f"Budget at completion ({unit})", "value": fmt(BAC), "sub": "BAC", "accent": INK,
         "help": "Total budget for the filtered activities, in the weighting unit shown. "
                 "Every earned value figure on this page is measured against it."},
        {"label": "Earned value", "value": fmt(EV), "sub": "EV", "accent": EARNED,
         "help": "Budgeted value of the work physically completed so far."},
        {"label": "Actual cost", "value": fmt(AC), "sub": "AC", "accent": ACTUAL,
         "help": "What that completed work has actually consumed."},
        {"label": "Estimate at completion", "value": fmt(EAC), "sub": "EAC = BAC / CPI", "accent": FORECAST,
         "help": "Forecast total, assuming cost performance to date continues."},
        {"label": "Variance at completion", "value": fmt(VAC), "sub": "VAC = BAC - EAC",
         "accent": EARNED if VAC >= 0 else ALERT,
         "tone": "good" if VAC >= 0 else "bad",
         "help": "Expected overrun (negative) or underrun (positive) at completion."},
        {"label": "To-complete index", "value": f"{TCPI:.3f}" if pd.notna(TCPI) else "—",
         "sub": "TCPI", "accent": ACTUAL,
         "tone": "warn" if (pd.notna(TCPI) and TCPI > 1.1) else "",
         "help": "Cost efficiency the remaining work must achieve to still finish on "
                 "budget. Well above 1.00 is a warning sign."},
        {"label": "Earned schedule", "value": f"{SPIt:.3f}" if pd.notna(SPIt) else "—",
         "sub": "SPI(t)", "accent": PLANNED,
         "tone": "" if not pd.notna(SPIt) else ("good" if SPIt >= 0.98 else "bad"),
         "help": "Time-based schedule performance. Unlike SPI it does not drift back "
                 "towards 1.00 as the project ends."},
    ])

    # status line
    msgs, tone = [], "good"
    if pd.notna(SPI) and SPI < 0.95:
        msgs.append(f"Schedule is behind plan (SPI {SPI:.2f}).")
        tone = "bad"
    if pd.notna(CPI) and CPI < 0.95:
        msgs.append(f"Cost overrun trend (CPI {CPI:.2f}, VAC {fmt(VAC)}).")
        tone = "bad"
    neg = int((df["Total_Float_d"] < 0).sum())
    if neg:
        msgs.append(f"{neg} activities carry negative float.")
        tone = "bad"
    if slip > 0:
        msgs.append(f"Forecast finish is {slip} days later than baseline.")
        tone = "bad" if slip > 14 else ("warn" if tone == "good" else tone)
    if not msgs:
        msgs = ["Every headline indicator is inside tolerance."]
    verdict(msgs, tone)

    section("Where the project stands", tight=True)
    d1, d2, d3 = st.columns(3)
    with d1:
        st.plotly_chart(donut(
            ["Earned", "In progress", "Not started"],
            [EV, max(df.loc[df["status_code"] == "TK_Active", "BAC"].sum()
                     - df.loc[df["status_code"] == "TK_Active", "EV"].sum(), 0),
             max(df.loc[df["status_code"] == "TK_NotStart", "BAC"].sum(), 0)],
            [EARNED, "#8FC7AE", "#DDE5EA"],
            f"{act_pct:.0f}%", f"of {unit.lower()} earned"), width="stretch")
    with d2:
        sm = df["Status"].value_counts()
        order = ["Complete", "In progress", "Not started"]
        st.plotly_chart(donut(
            order, [int(sm.get(k, 0)) for k in order],
            [EARNED, ACTUAL, PLANNED],
            f"{int(sm.get('In progress', 0))}", "activities in progress"), width="stretch")
    with d3:
        open_n = int((df["status_code"] != "TK_Complete").sum())
        crit_n = int(((df["status_code"] != "TK_Complete") &
                      (df["Is_Critical"] == "Critical")).sum())
        fl_open = df[df["status_code"] != "TK_Complete"]["Total_Float_d"]
        bands = [int((fl_open < 0).sum()), int((fl_open == 0).sum()),
                 int(((fl_open > 0) & (fl_open <= 20)).sum()), int((fl_open > 20).sum())]
        st.plotly_chart(donut(
            ["Negative float", "Critical", "Under 20 days", "Comfortable"], bands,
            [ALERT, "#D98B6E", ACTUAL, PLANNED],
            f"{crit_n}", "critical activities open"), width="stretch")

    left, right = st.columns([1.35, 1])
    with left:
        section("S-curve", "Cumulative planned, earned and actual value, with the remaining-work forecast beyond the data date.", tight=True)
        if curve is not None:
            f = go.Figure()
            f.add_trace(go.Scatter(x=curve["Date"], y=curve["PV"], name="Planned value (PV)",
                                   line=dict(color=PLANNED, width=3)))
            f.add_trace(go.Scatter(x=curve["Date"], y=curve["EV"], name="Earned value (EV)",
                                   line=dict(color=EARNED, width=3)))
            f.add_trace(go.Scatter(x=curve["Date"], y=curve["AC"], name="Actual cost (AC)",
                                   line=dict(color=ACTUAL, width=3)))
            f.add_trace(go.Scatter(x=curve["Date"], y=curve["Forecast"], name="Forecast (ETC)",
                                   line=dict(color=FORECAST, width=2, dash="dot")))
            vline(f, data_date)
            f.update_yaxes(title=f"Cumulative {unit}")
            st.plotly_chart(style(f, 420), width="stretch")

    with right:
        section("Progress by WBS", "Plan against actual for the largest packages by budget.", tight=True)
        g = wbs_evm[wbs_evm["BAC"] > 0].copy()
        g["Plan %"] = g["PV"] / g["BAC"] * 100
        g["Actual %"] = g["EV"] / g["BAC"] * 100
        g = g.head(15).sort_values("BAC")
        f = go.Figure()
        g["bar_color"] = np.where(g["Actual %"] >= g["Plan %"], EARNED,
                          np.where(g["Actual %"] >= g["Plan %"] - 10, ACTUAL, ALERT))
        f.add_trace(go.Bar(y=g["WBS"], x=g["Plan %"], name="Plan", orientation="h",
                           marker_color="#DCE6EC",
                           hovertemplate="Plan %{x:.1f}%<extra></extra>"))
        f.add_trace(go.Bar(y=g["WBS"], x=g["Actual %"], name="Actual", orientation="h",
                           marker=dict(color=g["bar_color"]),
                           hovertemplate="Actual %{x:.1f}%<extra></extra>"))
        f.update_layout(barmode="overlay")
        f.update_xaxes(title="%", range=[0, 100])
        st.plotly_chart(style(f, 420), width="stretch")

# -----------------------------------------------------------------------------
# SCHEDULE
# -----------------------------------------------------------------------------
with tab_sch:
    section("Gantt chart", "Solid bar is the completed portion, pale bar the remaining, grey shadow the baseline, diamond a milestone. Red is critical.", tight=True)
    bar = st.container(border=True)
    cc = bar.columns([1.25, 1.15, 1.1, .85, .85], vertical_alignment="bottom")
    group_by = cc[0].selectbox(
        "Group by", ["WBS level (sidebar)", "Status", "Criticality", "No grouping"],
        help="WBS level follows the level chosen in the sidebar filter panel.")
    sort_by = cc[1].selectbox(
        "Sort by", ["Start", "Finish", "Total float", "Budget (BAC)"],
        help="Budget at completion: the share of the total budget carried by an activity, in the weighting unit chosen in the sidebar. Sorting by it puts the highest-value work at the top.")
    row_limit = cc[2].slider("Rows", 25, 400, 150, step=25)
    show_bl = cc[3].checkbox("Baseline bars", value=True)
    show_lk = cc[4].checkbox("Logic lines", value=False)

    group_col = {"WBS level (sidebar)": lvl, "Status": "Status",
                 "Criticality": "Is_Critical", "No grouping": None}[group_by]
    sort_col = {"Start": "Start", "Finish": "Finish",
                "Total float": "Total_Float_d", "Budget (BAC)": "BAC"}[sort_by]

    gdf = df.sort_values(sort_col, ascending=(sort_by != "Budget (BAC)")).head(row_limit).copy()
    fig = gantt_figure(gdf, data_date, group_col=group_col, show_baseline=show_bl,
                       show_links=show_lk, preds=model["preds"], row_limit=row_limit)
    if fig is None:
        st.caption("No activities with valid dates to draw.")
    else:
        st.plotly_chart(fig, width="stretch")
        st.caption(f"Showing {len(gdf)} of {len(df)} filtered activities.")

    section("Lookahead schedule", "Open work with remaining duration inside the window, selected on P6 remaining early dates.")
    lbar = st.container(border=True)
    lc = lbar.columns([1.7, 1.1, 1.1], vertical_alignment="bottom")
    weeks = lc[0].radio("Window", [1, 2, 3, 4, 6, 12], horizontal=True, index=2,
                        format_func=lambda w: f"{w}w")
    la_group = lc[1].selectbox("Group", ["WBS level (sidebar)", "No grouping"], key="la_group")
    include_late = lc[2].checkbox("Include overdue work", value=True,
                                  help="Activities that should already have finished but "
                                       "still carry remaining duration.")

    end = data_date + pd.Timedelta(weeks=weeks)
    # P6 lookahead logic: open activities whose remaining early dates overlap the
    # window. Remaining early start/finish (restart_date / reend_date) is what P6
    # filters on, not the original target dates.
    open_w = df[df["status_code"] != "TK_Complete"].copy()
    in_window = (open_w["RES"] <= end) & (open_w["REF"] >= data_date)
    if not include_late:
        in_window &= open_w["RES"] >= data_date
    la = open_w[in_window].sort_values(["RES", "task_code"]).copy()
    la["Start"] = la["RES"]
    la["Finish"] = la["REF"]

    figure_strip([
        {"label": "Activities in window", "value": f"{len(la):,}",
         "sub": f"{weeks}-week window"},
        {"label": "Starting in window", "value": f"{int((la['RES'] >= data_date).sum()):,}",
         "sub": "not yet begun"},
        {"label": "Carried in", "value": f"{int((la['status_code'] == 'TK_Active').sum()):,}",
         "sub": "in progress at data date"},
        {"label": "Critical", "value": f"{int((la['Is_Critical'] == 'Critical').sum()):,}",
         "sub": "zero float or less",
         "tone": "bad" if (la["Is_Critical"] == "Critical").any() else ""},
        {"label": "Remaining duration", "value": f"{la['Rem_Dur_d'].sum():,.0f} d",
         "sub": "sum across the window"},
    ])

    if la.empty:
        st.caption("Nothing scheduled in this window.")
    else:
        la_fig = gantt_figure(
            la, data_date, group_col=(lvl if la_group == "WBS level (sidebar)" else None),
            show_baseline=False, show_links=False,
            x_range=[data_date - pd.Timedelta(days=3), end + pd.Timedelta(days=3)],
            row_limit=200)
        if la_fig is not None:
            st.plotly_chart(la_fig, width="stretch")

        la_tbl = la[["task_code", "task_name", lvl, "RES", "REF", "Orig_Dur_d", "Rem_Dur_d",
                     "Total_Float_d", "Actual_Pct", "Status"]].rename(columns={
            "task_code": "ID", "task_name": "Activity", lvl: "WBS",
            "RES": "Rem. early start", "REF": "Rem. early finish",
            "Orig_Dur_d": "OD", "Rem_Dur_d": "RD", "Total_Float_d": "Float", "Actual_Pct": "%"})
        for c in ("OD", "RD", "Float", "%"):
            la_tbl[c] = la_tbl[c].round(1)
        st.dataframe(la_tbl, width="stretch", hide_index=True, height=340,
                     column_config={"Rem. early start": st.column_config.DateColumn(format="DD MMM YYYY"),
                                    "Rem. early finish": st.column_config.DateColumn(format="DD MMM YYYY")})
        st.download_button(
            f"Download {weeks}-week lookahead (Excel)",
            to_excel({f"{weeks}w lookahead": la_tbl}),
            file_name=f"lookahead_{weeks}w_{data_date.strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        with st.expander("How this window is selected"):
            st.markdown(
                f"""
Window runs from the data date ({data_date.strftime('%d %b %Y')}) to
{end.strftime('%d %b %Y')}. An activity is included when all of the following hold:

- it is not complete;
- its remaining early start falls on or before the end of the window;
- its remaining early finish falls on or after the data date, so work still
  physically sits inside the window.

Dates come from the P6 remaining early start and finish fields
(`restart_date` / `reend_date`), falling back to early dates when a schedule was
exported without them. This matches what P6 shows when you filter on remaining
early dates rather than the original target dates, so in-progress activities that
started before the data date stay on the list until their remaining work is done.
"""
            )

    a, b = st.columns(2)
    with a:
        section("Milestones", tight=True)
        ms = tasks[tasks["Is_Milestone"]].copy()
        if ms.empty:
            st.caption("No milestones defined in the schedule.")
        else:
            ms["Variance (days)"] = ms["Finish_Var_d"]
            show = ms[["task_code", "task_name", "BL_Finish", "Finish", "Variance (days)", "Status"]] \
                .sort_values("Finish").rename(columns={
                    "task_code": "ID", "task_name": "Milestone",
                    "BL_Finish": "Plan", "Finish": "Forecast / Actual"})
            st.dataframe(show, width="stretch", hide_index=True, height=340,
                         column_config={"Plan": st.column_config.DateColumn(format="DD MMM YYYY"),
                                        "Forecast / Actual": st.column_config.DateColumn(format="DD MMM YYYY")})
    with b:
        section("Float profile of the window", tight=True)
        if not la.empty:
            prof = la.copy()
            prof["Band"] = pd.cut(prof["Total_Float_d"], [-1e9, -.001, .001, 5, 20, 1e9],
                                  labels=["Negative", "0 (critical)", "1-5 days",
                                          "6-20 days", ">20 days"])
            pv_ = prof.groupby("Band", observed=False).size()
            fp = go.Figure(go.Bar(x=pv_.index.astype(str), y=pv_.values,
                                  marker_color=[ALERT, "#D98B6E", ACTUAL, "#7FA9C4", PLANNED]))
            fp.update_yaxes(title="Activities in window")
            st.plotly_chart(style(fp, 340, hover="closest"), width="stretch")

    section("Late activities", "Not complete, and already past the baseline finish date.")
    late = df[(df["status_code"] != "TK_Complete") & (df["BL_Finish"] < data_date)].copy()
    late["Days late"] = (data_date - late["BL_Finish"]).dt.days
    late = late.sort_values("Days late", ascending=False)
    st.caption(f"{len(late)} activities have passed their planned finish date.")
    st.dataframe(
        late[["task_code", "task_name", lvl, "BL_Finish", "Finish", "Days late",
              "Actual_Pct", "Total_Float_d"]]
        .rename(columns={"task_code": "ID", "task_name": "Activity", lvl: "WBS",
                         "BL_Finish": "Plan finish", "Finish": "Forecast finish",
                         "Actual_Pct": "%", "Total_Float_d": "Float"}),
        width="stretch", hide_index=True, height=320,
        column_config={"Plan finish": st.column_config.DateColumn(format="DD MMM YYYY"),
                       "Forecast finish": st.column_config.DateColumn(format="DD MMM YYYY")})

# -----------------------------------------------------------------------------
# CRITICAL PATH
# -----------------------------------------------------------------------------
with tab_cp:
    open_t = df[df["status_code"] != "TK_Complete"]
    n_neg = int((open_t["Total_Float_d"] < 0).sum())
    figure_strip([
        {"label": "Critical activities", "value": f"{int((df['Is_Critical'] == 'Critical').sum()):,}",
         "sub": "zero float or driving"},
        {"label": "Negative float", "value": f"{n_neg:,}",
         "sub": "behind a constraint", "tone": "bad" if n_neg else "good"},
        {"label": "Lowest float",
         "value": f"{open_t['Total_Float_d'].min():.0f} d" if not open_t.empty else "—",
         "sub": "open work"},
        {"label": "Median float",
         "value": f"{open_t['Total_Float_d'].median():.0f} d" if not open_t.empty else "—",
         "sub": "open work"},
        {"label": "Open activities", "value": f"{len(open_t):,}", "sub": "not complete"},
    ])

    a, b = st.columns([1, 1])
    with a:
        section("Float distribution", tight=True)
        bins = [-1e9, -0.001, 0.001, 5, 20, 44, 1e9]
        lbls = ["Negative", "0 (critical)", "1-5 days", "6-20 days", "21-44 days", ">44 days"]
        fl = pd.cut(open_t["Total_Float_d"], bins=bins, labels=lbls).value_counts().reindex(lbls).fillna(0)
        f = go.Figure(go.Bar(x=fl.index.astype(str), y=fl.values,
                             marker_color=[ALERT, "#D98B6E", ACTUAL, "#7FA9C4",
                                           PLANNED, "#2F5F7A"]))
        f.update_yaxes(title="Activity count")
        st.plotly_chart(style(f, 380), width="stretch")
    with b:
        section("Critical work by WBS", tight=True)
        cr = df[df["Is_Critical"] == "Critical"].groupby(lvl).size().sort_values(ascending=True).tail(12)
        if cr.empty:
            st.caption("No critical activities found.")
        else:
            f = go.Figure(go.Bar(x=cr.values, y=cr.index.astype(str), orientation="h", marker_color=ALERT))
            f.update_xaxes(title="Critical activity count")
            st.plotly_chart(style(f, 380), width="stretch")

    section("Critical and at-risk activities", "Open activities with five days of total float or less.")
    risky = df[(df["Total_Float_d"] <= 5) & (df["status_code"] != "TK_Complete")] \
        .sort_values("Total_Float_d")
    st.dataframe(
        risky[["task_code", "task_name", lvl, "Start", "Finish", "Total_Float_d",
               "Rem_Dur_d", "Actual_Pct", "Status"]]
        .rename(columns={"task_code": "ID", "task_name": "Activity", lvl: "WBS",
                         "Start": "Start", "Finish": "Finish", "Total_Float_d": "Float (days)",
                         "Rem_Dur_d": "Remaining days", "Actual_Pct": "%"}),
        width="stretch", hide_index=True, height=420,
        column_config={"Start": st.column_config.DateColumn(format="DD MMM YYYY"),
                       "Finish": st.column_config.DateColumn(format="DD MMM YYYY")})

# -----------------------------------------------------------------------------
# EARNED VALUE
# -----------------------------------------------------------------------------
with tab_ev:
    section("Earned value by WBS", f"Budget, earned and actual columns are all in {unit.lower()}.", tight=True)
    st.dataframe(
        wbs_evm, width="stretch", hide_index=True,
        column_config={
            "BAC": st.column_config.NumberColumn(format="%.0f"),
            "PV": st.column_config.NumberColumn(format="%.0f"),
            "EV": st.column_config.NumberColumn(format="%.0f"),
            "AC": st.column_config.NumberColumn(format="%.0f"),
            "SV": st.column_config.NumberColumn(format="%.0f"),
            "CV": st.column_config.NumberColumn(format="%.0f"),
            "EAC": st.column_config.NumberColumn(format="%.0f"),
            "VAC": st.column_config.NumberColumn(format="%.0f"),
            "SPI": st.column_config.NumberColumn(format="%.2f"),
            "CPI": st.column_config.NumberColumn(format="%.2f"),
        })

    a, b = st.columns(2)
    with a:
        section("Performance matrix", tight=True)
        m = wbs_evm[wbs_evm["BAC"] > 0].copy()
        f = px.scatter(m, x="SPI", y="CPI", size="BAC", color="VAC", hover_name="WBS",
                       color_continuous_scale=[[0, ALERT], [.5, "#EDF2F7"], [1, EARNED]])
        f.add_hline(y=1, line_dash="dot", line_color=SLATE)
        f.add_vline(x=1, line_dash="dot", line_color=SLATE)
        st.plotly_chart(style(f, 400, hover="closest"), width="stretch")
        st.caption("Top-right quadrant: on time and within budget. Bottom-left: both late and overspent.")
    with b:
        section("Largest schedule variances", tight=True)
        v = df.copy()
        v["SV"] = v["EV"] - v["PV"]
        v = v.reindex(v["SV"].sort_values().index).head(20)
        f = go.Figure(go.Bar(x=v["SV"], y=v["task_code"] + " · " + v["task_name"].str.slice(0, 30),
                             orientation="h", marker_color=ALERT))
        f.update_yaxes(autorange="reversed")
        f.update_xaxes(title=f"Schedule variance (SV, {unit})")
        st.plotly_chart(style(f, 400, hover="closest"), width="stretch")

    section("Forecast summary")
    fc = pd.DataFrame({
        "Indicator": ["BAC", "PV", "EV", "AC", "SV", "CV", "SPI", "CPI", "SPI(t)",
                     "EAC (CPI bazli)", "ETC", "VAC", "TCPI"],
        "Value": [BAC, PV, EV, AC, SV, CV, SPI, CPI, SPIt, EAC, ETC, VAC, TCPI],
    })
    fc["Value"] = fc["Value"].map(lambda x: f"{x:,.2f}" if pd.notna(x) else "-")
    st.dataframe(fc, width="stretch", hide_index=True)

# -----------------------------------------------------------------------------
# RESOURCES
# -----------------------------------------------------------------------------
with tab_res:
    section("Resource histogram", "Value placed in each period, with the cumulative curve overlaid.", tight=True)
    rbar = st.container(border=True)
    c = rbar.columns([1.2, 1, 2.4], vertical_alignment="bottom")
    freq = c[0].radio("Period", ["Weekly", "Monthly"], horizontal=True, index=1)
    cum = c[1].checkbox("Show cumulative curve", value=True)
    rule = "W-MON" if freq == "Weekly" else "MS"

    if curve is not None:
        h = curve.set_index("Date")[["PV_d", "EV_d", "AC_d", "ETC_d"]].resample(rule).sum().reset_index()
        h.loc[h["Date"] > data_date, ["EV_d", "AC_d"]] = np.nan
        h.loc[h["Date"] < data_date, "ETC_d"] = np.nan

        f = go.Figure()
        f.add_trace(go.Bar(x=h["Date"], y=h["PV_d"], name="Planned", marker_color=PLANNED, opacity=.85))
        f.add_trace(go.Bar(x=h["Date"], y=h["AC_d"], name="Actual", marker_color=ACTUAL))
        f.add_trace(go.Bar(x=h["Date"], y=h["ETC_d"], name="Remaining work (ETC)", marker_color=FORECAST, opacity=.6))
        if cum:
            f.add_trace(go.Scatter(x=curve["Date"], y=curve["PV"], name="Cumulative plan",
                                   yaxis="y2", line=dict(color=PLANNED, width=2, dash="dot")))
            f.add_trace(go.Scatter(x=curve["Date"], y=curve["EV"], name="Cumulative earned",
                                   yaxis="y2", line=dict(color=EARNED, width=2)))
            f.update_layout(yaxis2=dict(overlaying="y", side="right", title="Cumulative", showgrid=False))
        f.update_layout(barmode="group")
        f.update_yaxes(title=f"{unit} per period")
        vline(f, data_date)
        st.plotly_chart(style(f, 430), width="stretch")

    asg = model["rsrc_asg"]
    if not asg.empty:
        section("Resource breakdown")
        r = model["rsrc"]
        a = asg[asg["task_id"].isin(df["task_id"])].copy()
        if not r.empty and "rsrc_id" in r.columns:
            name_col = "rsrc_name" if "rsrc_name" in r.columns else "rsrc_short_name"
            a = a.merge(r[["rsrc_id", name_col]], on="rsrc_id", how="left")
            a["Resources"] = a[name_col].fillna("Unassigned")
        else:
            a["Resources"] = a["rsrc_id"]
        rs = a.groupby("Resources").agg(
            Planned_Qty=("target_qty", "sum"), Actual_Qty=("act_reg_qty", "sum"),
            Remaining_Qty=("remain_qty", "sum"), Planned_Cost=("target_cost", "sum"),
            Actual_Cost=("act_reg_cost", "sum")).reset_index()
        rs = rs.sort_values("Planned_Qty", ascending=False)
        top = rs.head(15).sort_values("Planned_Qty")
        f = go.Figure()
        f.add_trace(go.Bar(y=top["Resources"], x=top["Planned_Qty"], name="Planned",
                           orientation="h", marker_color=PLANNED, opacity=.6))
        f.add_trace(go.Bar(y=top["Resources"], x=top["Actual_Qty"], name="Actual",
                           orientation="h", marker_color=ACTUAL))
        f.update_layout(barmode="overlay")
        st.plotly_chart(style(f, 420, hover="closest"), width="stretch")
        st.dataframe(rs, width="stretch", hide_index=True)
    else:
        st.info("No resource assignments (TASKRSRC) in the XER; the histogram uses duration weighting.")

# -----------------------------------------------------------------------------
# SCHEDULE QUALITY (DCMA 14)
# -----------------------------------------------------------------------------
with tab_q:
    section("DCMA 14-point schedule quality check", "Checks run on the filtered activity set. Clear the sidebar filters to test the whole schedule.", tight=True)
    passed = int((checks_df["Status"] == "Pass").sum())
    figure_strip([
        {"label": "Checks passed", "value": f"{passed} / {len(checks_df)}",
         "sub": "DCMA 14-point",
         "tone": "good" if passed >= 12 else "bad"},
        {"label": "Relationships", "value": f"{len(model['preds']):,}", "sub": "in the filtered set"},
        {"label": "Activities tested", "value": f"{len(df):,}", "sub": "excluding LOE and summaries"},
    ])

    qa, qb = st.columns([1, 2.4])
    with qa:
        st.plotly_chart(donut(
            ["Passed", "Failed"], [passed, len(checks_df) - passed], [EARNED, ALERT],
            f"{passed}/{len(checks_df)}", "checks passed", height=280), width="stretch")
    with qb:
        st.markdown(
            '<div style="height:14px"></div>'
            '<p style="color:%s;font-size:.86rem;max-width:70ch">'
            'The fourteen checks below follow the US Defense Contract Management Agency '
            'assessment. They test whether the schedule is built soundly enough to be '
            'trusted for forecasting, not whether the project is going well.</p>' % SLATE,
            unsafe_allow_html=True)

    def paint(row):
        color = "#F1F8F4" if row["Status"] == "Pass" else "#FBF2F1"
        return [f"background-color: {color}"] * len(row)

    try:
        st.dataframe(checks_df.style.apply(paint, axis=1), width="stretch",
                     hide_index=True, height=560)
    except Exception:
        st.dataframe(checks_df, width="stretch", hide_index=True, height=560)

    section("Fix list", "The activities behind the failed checks above.")
    fix = df[(df["Pred_Cnt"] == 0) | (df["Succ_Cnt"] == 0) | (df["cstr_type"].isin(HARD_CSTR))
             | (df["Total_Float_d"] < 0)].copy()
    fix["Issue"] = np.where(fix["Total_Float_d"] < 0, "Negative float",
                    np.where(fix["cstr_type"].isin(HARD_CSTR), "Hard constraint",
                     np.where(fix["Pred_Cnt"] == 0, "No predecessor", "No successor")))
    st.dataframe(
        fix[["task_code", "task_name", "Issue", "Total_Float_d", "cstr_type", "Status"]]
        .rename(columns={"task_code": "ID", "task_name": "Activity",
                         "Total_Float_d": "Float", "cstr_type": "Constraint"}),
        width="stretch", hide_index=True, height=360)

# -----------------------------------------------------------------------------
# BASELINE COMPARISON
# -----------------------------------------------------------------------------
with tab_bl:
    if up_bl is None:
        st.info("Upload a baseline .xer from the sidebar to compare.")
    else:
        bl_tables = parse_xer(up_bl.getvalue())
        bl_proj = bl_tables["PROJECT"]
        bl_ids = bl_proj["proj_id"].tolist()
        bl_labels = dict(zip(bl_proj["proj_id"], col_or(bl_proj, "proj_short_name", "").astype(str)))
        bl_pid = st.selectbox("Baseline project", bl_ids,
                              format_func=lambda x: bl_labels.get(x) or x)
        bl_model = build_model(bl_tables, bl_pid, weight_basis)
        b = bl_model["tasks"][["task_code", "task_name", "Start", "Finish", "BAC", "Orig_Dur_d"]] \
            .rename(columns={"Start": "BL_Start_2", "Finish": "BL_Finish_2",
                             "BAC": "BL_BAC", "Orig_Dur_d": "BL_Dur", "task_name": "BL_Name"})
        cur = df[["task_code", "task_name", "Start", "Finish", "BAC", "Orig_Dur_d", "Actual_Pct", "Status"]]
        cmp = cur.merge(b, on="task_code", how="outer", indicator=True)

        added = (cmp["_merge"] == "left_only").sum()
        removed = (cmp["_merge"] == "right_only").sum()
        both = cmp[cmp["_merge"] == "both"].copy()
        both["Start variance"] = (both["Start"] - both["BL_Start_2"]).dt.days
        both["Finish variance"] = (both["Finish"] - both["BL_Finish_2"]).dt.days
        both["Duration change"] = both["Orig_Dur_d"] - both["BL_Dur"]

        slipped = int((both["Finish variance"] > 0).sum())
        figure_strip([
            {"label": "Matched activities", "value": f"{len(both):,}", "sub": "present in both"},
            {"label": "Added", "value": f"{int(added):,}", "sub": "current only"},
            {"label": "Removed", "value": f"{int(removed):,}", "sub": "baseline only"},
            {"label": "Slipped", "value": f"{slipped:,}", "sub": "finishing later",
             "tone": "bad" if slipped else "good"},
            {"label": "Average slip",
             "value": f"{both['Finish variance'].mean():.1f} d"
                      if both["Finish variance"].notna().any() else "—",
             "sub": "across matched work"},
        ])

        f = px.histogram(both.dropna(subset=["Finish variance"]), x="Finish variance", nbins=40,
                         color_discrete_sequence=[PLANNED])
        f.update_xaxes(title="Finish date variance (days)")
        st.plotly_chart(style(f, 340, hover="closest"), width="stretch")

        st.dataframe(
            both[["task_code", "task_name", "BL_Start_2", "Start", "BL_Finish_2", "Finish",
                  "Start variance", "Finish variance", "Duration change", "Actual_Pct"]]
            .sort_values("Finish variance", ascending=False)
            .rename(columns={"task_code": "ID", "task_name": "Activity", "BL_Start_2": "BL start",
                             "Start": "Current start", "BL_Finish_2": "BL finish",
                             "Finish": "Current finish", "Actual_Pct": "%"}),
            width="stretch", hide_index=True, height=480)

# -----------------------------------------------------------------------------
# DATA
# -----------------------------------------------------------------------------
with tab_data:
    section("Activity table", "Everything currently passing the filters.", tight=True)
    cols = ["task_code", "task_name", "WBS_Path", "Status", "Type", "Start", "Finish",
            "BL_Start", "BL_Finish", "Start_Var_d", "Finish_Var_d", "Orig_Dur_d", "Rem_Dur_d",
            "Total_Float_d", "Free_Float_d", "Planned_Pct", "Actual_Pct",
            "BAC", "PV", "EV", "AC", "Is_Critical"]
    out = df[[c for c in cols if c in df.columns]].copy()
    out["SV"] = out["EV"] - out["PV"]
    out["CV"] = out["EV"] - out["AC"]
    out = out.rename(columns={
        "task_code": "ID", "task_name": "Activity", "WBS_Path": "WBS",
        "Start": "Start", "Finish": "Finish", "BL_Start": "Plan start",
        "BL_Finish": "Plan finish", "Start_Var_d": "Start var. (d)",
        "Finish_Var_d": "Finish var. (d)", "Orig_Dur_d": "Duration (d)",
        "Rem_Dur_d": "Remaining (d)", "Total_Float_d": "Total float (d)",
        "Free_Float_d": "Free float (d)", "Planned_Pct": "Plan %",
        "Actual_Pct": "Actual %", "Is_Critical": "Criticality"})
    for c in ["Plan %", "Actual %", "Duration (d)", "Remaining (d)", "Total float (d)", "Free float (d)"]:
        if c in out.columns:
            out[c] = out[c].round(1)
    for c in ["BAC", "PV", "EV", "AC", "SV", "CV"]:
        out[c] = out[c].round(0)

    st.dataframe(out, width="stretch", hide_index=True, height=560)

    sheets = {"Activities": out, "WBS_EVM": wbs_evm, "DCMA": checks_df}
    if curve is not None:
        sheets["S_Curve"] = curve[["Date", "PV", "EV", "AC"]]
    st.download_button("Download as Excel", to_excel(sheets),
                       file_name=f"planning_control_{data_date.strftime('%Y%m%d')}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with st.expander("Tables found in the XER"):
        st.write({k: f"{len(v)} rows" for k, v in tables.items()})

with st.sidebar:
    privacy_and_contact()
