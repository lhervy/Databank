"""
Databank · client dashboard + pipeline health (Streamlit in Snowflake)

Reads only Gold (DATABANK.MARTS) and monitoring views (DATABANK.OPS).
Look and feel: same colours as the presentation deck (greens, Poppins).
Deploy: workspace > Add new > Streamlit App (warehouse DATABANK_WH), paste this file.
"""
import os
import re

import altair as alt
import pandas as pd
import streamlit as st

try:   # container runtime
    session = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL")).session()
except Exception:  # warehouse runtime
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()

st.set_page_config(page_title="Databank", layout="wide")

# ------------------------------------------------------------------ look and feel (deck colours)
DARK, GREEN, MID, LIGHT, PALE, GREY = "#347470", "#35b276", "#5ec57e", "#b8e28a", "#e7ffcc", "#5a6470"
FONT = "Poppins, Segoe UI, Helvetica, Arial, sans-serif"

ICONS = {
    "wallet": '<rect x="2" y="6" width="20" height="14" rx="2"/><path d="M16 13h2M2 10h20M6 6V4h12v2"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "chart": '<path d="M3 21h18"/><path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "shield": '<path d="M12 2l8 3v6c0 5-3.5 9-8 11-4.5-2-8-6-8-11V5z"/><path d="M9 12l2 2 4-4"/>',
    "bolt": '<path d="M13 2L4 14h8l-1 8 9-12h-8z"/>',
    "alert": '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18h.01"/>',
    "db": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, .stText, button, input, label {{ font-family: 'Poppins', 'Segoe UI', Arial, sans-serif; }}
.block-container {{ padding-top: 3.2rem; max-width: 1400px; }}
h2, h3 {{ color: {DARK} !important; font-weight: 700 !important; }}
.db-hero {{ background: linear-gradient(110deg, {DARK} 0%, {GREEN} 100%); border-radius: 22px; padding: 26px 32px;
           color: white; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; margin-bottom: 14px; }}
.db-hero h1 {{ color: white !important; font-size: 2.4rem; font-weight: 700; letter-spacing: 2px; margin: 0; padding: 0; }}
.db-hero p {{ margin: 4px 0 0 0; opacity: .92; font-size: 1rem; }}
.db-pills {{ display: flex; gap: 8px; flex-wrap: wrap; }}
.db-pill {{ background: rgba(255,255,255,.18); border: 1px solid rgba(255,255,255,.45); border-radius: 999px; padding: 6px 14px; font-size: .85rem; font-weight: 600; }}
.db-kpi {{ background: white; border: 2px solid {LIGHT}; border-radius: 18px; padding: 16px 18px; display: flex; gap: 14px; align-items: center; height: 100%; }}
.db-kpi .ic {{ background: {PALE}; border-radius: 50%; width: 52px; height: 52px; min-width: 52px; display: flex; align-items: center; justify-content: center; }}
.db-kpi .lb {{ color: {GREY}; font-size: .82rem; }}
.db-kpi .vl {{ color: {DARK}; font-size: 1.65rem; font-weight: 700; line-height: 1.2; }}
.db-kpi .sb {{ color: {GREY}; font-size: .78rem; }}
.db-kpi.hl {{ border-color: {GREEN}; background: {PALE}; }}
.db-kpi.hl .ic {{ background: white; }}
.db-fresh {{ border: 2px solid {LIGHT}; border-radius: 16px; padding: 14px 16px; background: white; }}
.db-fresh .nm {{ color: {DARK}; font-weight: 700; font-size: .95rem; }}
.db-fresh .ag {{ color: {GREY}; font-size: .8rem; margin-top: 2px; }}
.db-tag {{ display: inline-block; border-radius: 999px; padding: 2px 10px; font-size: .74rem; font-weight: 700; color: white; margin-top: 8px; }}
.stTabs [data-baseweb="tab-list"], .stTabs [role="tablist"] {{ gap: 8px; border-bottom: 0 !important; }}
.stTabs [data-baseweb="tab"], .stTabs [role="tab"] {{ background: {PALE}; border-radius: 999px; padding: 8px 20px !important; color: {DARK}; font-weight: 600; border: 0 !important; }}
.stTabs [role="tab"] p {{ font-weight: 600; }}
.stTabs [aria-selected="true"] {{ background: {DARK} !important; color: white !important; }}
.stTabs [aria-selected="true"] p {{ color: white !important; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none; }}
div.stButton > button {{ background: {GREEN}; color: white; border: 0; border-radius: 999px; font-weight: 600; padding: 6px 22px; }}
div.stButton > button:hover {{ background: {DARK}; color: white; }}
.db-foot {{ color: {GREY}; font-size: .78rem; margin-top: 24px; }}
</style>
<div class="db-hero">
  <div><h1>DATABANK</h1><p>Client dashboard &amp; pipeline health · data from Gold tables only</p></div>
  <div class="db-pills"><span class="db-pill">Snowflake · AWS Paris</span><span class="db-pill">6 sources</span>
  <span class="db-pill">Bronze → Silver → Gold</span><span class="db-pill">€0 · free trial</span></div>
</div>
""", unsafe_allow_html=True)


def q(sql: str) -> pd.DataFrame:
    return session.sql(sql).to_pandas()


def svg(name: str, size: int = 26, col: str = DARK) -> str:
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{col}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')


def kpi(col, icon: str, label: str, value: str, sub: str = "", highlight: bool = False):
    col.markdown(f'<div class="db-kpi{" hl" if highlight else ""}"><div class="ic">{svg(icon)}</div>'
                 f'<div><div class="lb">{label}</div><div class="vl">{value}</div><div class="sb">{sub}</div></div></div>',
                 unsafe_allow_html=True)


def eur(x) -> str:
    return f"{float(x):,.2f} €".replace(",", " ")


def style_chart(c: alt.Chart) -> alt.Chart:
    return (c.configure_axis(labelColor=GREY, titleColor=GREY, gridColor="#eef3ea", domainColor=LIGHT, labelFont=FONT, titleFont=FONT, labelLimit=260)
             .configure_view(strokeWidth=0).configure_legend(labelColor=GREY, titleColor=GREY, labelFont=FONT, orient="top"))


tab_client, tab_market, tab_ops = st.tabs(["Client view", "Markets", "Pipeline health"])

# ------------------------------------------------------------------ client
with tab_client:
    clients = q("""SELECT b.client_id FROM DATABANK.MARTS.ACCOUNT_LIVE_BALANCE b
                   LEFT JOIN (SELECT DISTINCT client_id FROM DATABANK.MARTS.PORTFOLIO_VALUATION) p ON p.client_id = b.client_id
                   ORDER BY (p.client_id IS NOT NULL) DESC, b.pending_count DESC, b.client_id
                   LIMIT 300""")
    ids = list(clients["CLIENT_ID"])
    pick, refresh = st.columns([4, 1])
    cid = pick.selectbox("Client", ids, index=0)
    if not re.fullmatch(r"C\d{6}", str(cid)):
        st.stop()
    refresh.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    refresh.button("Refresh")

    bal = q(f"""SELECT available_balance_eur, pending_amount_eur, pending_count, ledger_balance_eur
                FROM DATABANK.MARTS.ACCOUNT_LIVE_BALANCE WHERE client_id = '{cid}'""")
    pf = q(f"""SELECT COALESCE(SUM(market_value_eur), 0) v, COALESCE(SUM(unrealized_pnl_eur), 0) p
               FROM DATABANK.MARTS.PORTFOLIO_VALUATION WHERE client_id = '{cid}'""")
    fr = q(f"""SELECT COUNT_IF(is_suspicious) n, COUNT(*) t FROM DATABANK.MARTS.FCT_CARD_TRANSACTIONS
               WHERE client_id = '{cid}' AND event_ts >= DATEADD(day, -30, CURRENT_DATE())""")
    c1, c2, c3, c4 = st.columns(4)
    if not bal.empty:
        kpi(c1, "wallet", "Available balance", eur(bal["AVAILABLE_BALANCE_EUR"][0]),
            f"booked {eur(bal['LEDGER_BALANCE_EUR'][0])} minus pending", highlight=True)
        kpi(c2, "clock", "Pending card payments", eur(bal["PENDING_AMOUNT_EUR"][0]), f"{int(bal['PENDING_COUNT'][0])} payments, not booked yet")
    kpi(c3, "chart", "Portfolio (real prices, in €)", eur(pf["V"][0]), f"{eur(pf['P'][0])} unrealized")
    kpi(c4, "shield", "Fraud alerts · 30 days", f"{int(fr['N'][0])}", f"out of {int(fr['T'][0])} payments")

    st.subheader("Latest card payments")
    tx = q(f"""SELECT event_ts AS "Time (UTC)", merchant_name AS "Merchant", category AS "Category",
                      amount_eur::FLOAT AS "Amount", status AS "Status", booking_status AS "Booking",
                      is_suspicious AS "Fraud alert"
               FROM DATABANK.MARTS.FCT_CARD_TRANSACTIONS WHERE client_id = '{cid}'
               ORDER BY event_ts DESC LIMIT 15""")
    st.dataframe(tx, width="stretch", hide_index=True, column_config={
        "Amount": st.column_config.NumberColumn("Amount (€)", format="%.2f €"),
        "Fraud alert": st.column_config.CheckboxColumn("Fraud alert"),
        "Time (UTC)": st.column_config.DatetimeColumn("Time (UTC)", format="D MMM YYYY, HH:mm")})

    left, right = st.columns([1.1, 1])
    with left:
        st.subheader("Spending by category · 30 days")
        sp = q(f"""SELECT category AS "CATEGORY", SUM(spend_eur)::FLOAT AS "SPEND" FROM DATABANK.MARTS.CLIENT_DAILY_SPEND
                   WHERE client_id = '{cid}' AND event_date >= DATEADD(day, -30, CURRENT_DATE())
                   GROUP BY 1 ORDER BY 2 DESC""")
        if sp.empty:
            st.info("No spending in the last 30 days.")
        else:
            base = alt.Chart(sp).encode(y=alt.Y("CATEGORY:N", sort="-x", title=None), x=alt.X("SPEND:Q", title="€", scale=alt.Scale(domain=[0, float(sp["SPEND"].max()) * 1.15])))
            bars = base.mark_bar(cornerRadiusEnd=8, color=GREEN, size=22)
            labels = base.mark_text(align="left", dx=6, color=DARK, fontWeight="bold", font=FONT).encode(text=alt.Text("SPEND:Q", format=",.0f"))
            st.altair_chart(style_chart((bars + labels).properties(height=max(220, 38 * len(sp)))), use_container_width=True)
    with right:
        st.subheader("Portfolio")
        pt = q(f"""SELECT ticker AS "TICKER", quantity AS "QTY", market_value_eur::FLOAT AS "VALUE", unrealized_pnl_eur::FLOAT AS "PNL"
                   FROM DATABANK.MARTS.PORTFOLIO_VALUATION WHERE client_id = '{cid}' ORDER BY market_value_eur DESC""")
        if pt.empty:
            st.info("This client has no investment account.")
        else:
            donut = alt.Chart(pt).mark_arc(innerRadius=72, outerRadius=118, cornerRadius=4, stroke="white", strokeWidth=2).encode(
                theta="VALUE:Q",
                color=alt.Color("TICKER:N", title=None, scale=alt.Scale(range=[DARK, GREEN, MID, LIGHT, "#8fd19e", "#2a5d5a", "#cdeeb0"])),
                tooltip=["TICKER", alt.Tooltip("VALUE:Q", format=",.2f", title="Value (€)"), "QTY"])
            st.altair_chart(style_chart(donut.properties(height=260)), use_container_width=True)
            st.dataframe(pt, width="stretch", hide_index=True, column_config={
                "TICKER": "Share", "QTY": "Quantity",
                "VALUE": st.column_config.NumberColumn("Value (€)", format="%.2f €"),
                "PNL": st.column_config.NumberColumn("Unrealized (€)", format="%.2f €")})

# ------------------------------------------------------------------ markets
with tab_market:
    st.subheader("Share prices of the securities our clients hold")
    st.caption("Real data from the Snowflake Marketplace, converted to euros")
    tick = st.selectbox("Share", ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "JPM", "V", "MA", "TSLA"])
    px = q(f"""SELECT price_date AS "DATE", close_eur::FLOAT AS "CLOSE" FROM DATABANK.MARTS.STOCK_PRICES_DAILY
               WHERE ticker = '{tick}' AND price_date >= DATEADD(year, -1, CURRENT_DATE()) ORDER BY 1""")
    if not px.empty:
        m1, m2, m3 = st.columns(3)
        last, first = float(px["CLOSE"].iloc[-1]), float(px["CLOSE"].iloc[0])
        kpi(m1, "chart", f"{tick} · last close", eur(last), str(px["DATE"].iloc[-1])[:10], highlight=True)
        kpi(m2, "bolt", "Change over 1 year", f"{(last / first - 1) * 100:+.1f} %", f"from {eur(first)}")
        kpi(m3, "db", "Trading days shown", f"{len(px)}", "last 12 months")
        lo, hi = float(px["CLOSE"].min()), float(px["CLOSE"].max())
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        area = alt.Chart(px).mark_area(
            clip=True, line={"color": DARK, "strokeWidth": 2.5},
            color=alt.Gradient(gradient="linear", stops=[alt.GradientStop(color="white", offset=0), alt.GradientStop(color=LIGHT, offset=1)],
                               x1=1, x2=1, y1=1, y2=0)).encode(
            x=alt.X("DATE:T", title=None), y=alt.Y("CLOSE:Q", title="€", scale=alt.Scale(domain=[lo * 0.96, hi * 1.02])),
            tooltip=[alt.Tooltip("DATE:T"), alt.Tooltip("CLOSE:Q", format=",.2f", title="Close (€)")])
        st.altair_chart(style_chart(area.properties(height=320)), use_container_width=True)

    st.subheader("EUR/USD from two independent sources")
    st.caption("ECB API (our Docker job) against the Marketplace rate: the pipeline uses the ECB rate first and the Marketplace as fallback")
    fx = q("""SELECT rate_date AS "DATE", ecb_api_rate::FLOAT AS "ECB API", marketplace_rate::FLOAT AS "Marketplace"
              FROM DATABANK.MARTS.FX_RATES_DAILY WHERE currency = 'USD'
                AND rate_date >= DATEADD(year, -1, CURRENT_DATE()) ORDER BY 1""")
    fxl = fx.melt("DATE", var_name="Source", value_name="Rate").dropna()
    if not fxl.empty:
        lines = alt.Chart(fxl).mark_line(strokeWidth=2.5).encode(
            x=alt.X("DATE:T", title=None), y=alt.Y("Rate:Q", title="USD per EUR", scale=alt.Scale(zero=False)),
            color=alt.Color("Source:N", title=None, scale=alt.Scale(domain=["ECB API", "Marketplace"], range=[DARK, MID])),
            strokeDash=alt.StrokeDash("Source:N", scale=alt.Scale(domain=["ECB API", "Marketplace"], range=[[1, 0], [6, 4]]), legend=None),
            tooltip=["DATE:T", "Source", alt.Tooltip("Rate:Q", format=".4f")])
        st.altair_chart(style_chart(lines.properties(height=280)), use_container_width=True)

# ------------------------------------------------------------------ ops
with tab_ops:
    st.subheader("Source freshness")
    fs = q("""SELECT source AS "SOURCE", last_arrival AS "LAST", total_rows AS "ROWS",
                     DATEDIFF(minute, last_arrival, SYSDATE()) AS "AGE_MIN"
              FROM DATABANK.OPS.SOURCE_FRESHNESS ORDER BY 1""")
    cols = st.columns(len(fs) if len(fs) else 1)
    for i, r in fs.iterrows():
        age = r["AGE_MIN"]
        if pd.isna(age):
            tag, colr, txt = "No data", "#c0563f", "never loaded"
        else:
            age = int(age)
            limit = 30 if str(r["SOURCE"]).startswith("A") else 26 * 60
            txt = f"{age} min ago" if age < 120 else (f"{age // 60} h ago" if age < 48 * 60 else f"{age // 1440} days ago")
            tag, colr = ("Fresh", GREEN) if age <= limit else (("Late", "#d9a13b") if age <= 4 * 1440 else ("Stale", "#c0563f"))
        cols[i].markdown(f'<div class="db-fresh"><div class="nm">{r["SOURCE"]}</div><div class="ag">{txt} · {int(r["ROWS"]):,} rows</div>'
                         f'<span class="db-tag" style="background:{colr}">{tag}</span></div>', unsafe_allow_html=True)
    st.caption("Fresh = within the expected rhythm (card stream: 30 min, daily sources: 26 h). Late or stale sources warn the owner; the reports keep their last good data.")

    a, b = st.columns([1.2, 1])
    with a:
        st.subheader("Quarantined messages")
        dq = q("""SELECT reject_reason AS "REASON", COUNT(*) AS "N" FROM DATABANK.MARTS.DQ_REJECTED_AUTHORIZATIONS
                  GROUP BY 1 ORDER BY 2 DESC""")
        if dq.empty:
            st.success("No message in quarantine.")
        else:
            base = alt.Chart(dq).encode(y=alt.Y("REASON:N", sort="-x", title=None), x=alt.X("N:Q", title="messages", scale=alt.Scale(domain=[0, float(dq["N"].max()) * 1.15])))
            chart = base.mark_bar(cornerRadiusEnd=8, color=MID, size=24) + base.mark_text(align="left", dx=6, color=DARK, fontWeight="bold", font=FONT).encode(text="N:Q")
            st.altair_chart(style_chart(chart.properties(height=max(160, 44 * len(dq)))), use_container_width=True)
    with b:
        st.subheader("Ingestion speed · last hour")
        lt = q("""SELECT COUNT(*) AS "N", ROUND(AVG(ingest_latency_ms)) AS "AVG", MAX(ingest_latency_ms) AS "MAX"
                  FROM DATABANK.MARTS.FCT_CARD_TRANSACTIONS WHERE ingested_at > DATEADD(hour, -1, SYSDATE())""")
        n = int(lt["N"][0])
        k1, k2 = st.columns(2)
        kpi(k1, "bolt", "Payments received", f"{n:,}", "in the last hour", highlight=n > 0)
        kpi(k2, "clock", "Average delay", f"{float(lt['AVG'][0]) / 1000:.1f} s" if n else "–",
            f"max {float(lt['MAX'][0]) / 1000:.1f} s" if n else "start the card stream to see it live")

st.markdown('<div class="db-foot">Databank is a fictive bank built for a data engineering course · reads Gold (MARTS) and OPS only · personal data masked by policy</div>',
            unsafe_allow_html=True)
