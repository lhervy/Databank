"""
Databank · client dashboard + pipeline health (Streamlit in Snowflake)

Reads only Gold (DATABANK.MARTS) and monitoring views (DATABANK.OPS).
Deploy: workspace > Add new > Streamlit App (warehouse DATABANK_WH), paste this file.
"""
import os
import re

import streamlit as st

try:   # container runtime
    session = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL")).session()
except Exception:  # warehouse runtime
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()

st.set_page_config(page_title="Databank", layout="wide")
st.title("Databank")
st.caption("Fictive bank · Snowflake on AWS (Paris) · 6 sources · dbt Bronze → Silver → Gold")


def q(sql: str):
    return session.sql(sql).to_pandas()


tab_client, tab_market, tab_ops = st.tabs(["Client view", "Markets", "Pipeline health"])

# ------------------------------------------------------------------ client
with tab_client:
    clients = q("""SELECT client_id FROM DATABANK.MARTS.ACCOUNT_LIVE_BALANCE
                   ORDER BY pending_count DESC, client_id LIMIT 300""")
    ids = list(clients["CLIENT_ID"])
    cid = st.selectbox("Client", ids, index=ids.index("C000042") if "C000042" in ids else 0)
    if not re.fullmatch(r"C\d{6}", str(cid)):
        st.stop()
    st.button("Refresh")

    bal = q(f"""SELECT available_balance_eur, pending_amount_eur, pending_count, ledger_balance_eur
                FROM DATABANK.MARTS.ACCOUNT_LIVE_BALANCE WHERE client_id = '{cid}'""")
    pf = q(f"""SELECT COALESCE(SUM(market_value_eur), 0) v, COALESCE(SUM(unrealized_pnl_eur), 0) p
               FROM DATABANK.MARTS.PORTFOLIO_VALUATION WHERE client_id = '{cid}'""")
    c1, c2, c3 = st.columns(3)
    if not bal.empty:
        c1.metric("Available balance", f"{float(bal['AVAILABLE_BALANCE_EUR'][0]):,.2f} €",
                  help="Booked ledger balance minus pending card payments")
        c2.metric("Pending card payments", f"{float(bal['PENDING_AMOUNT_EUR'][0]):,.2f} €",
                  f"{int(bal['PENDING_COUNT'][0])} payments", delta_color="off")
    c3.metric("Portfolio (real Nasdaq prices, in €)", f"{float(pf['V'][0]):,.2f} €",
              f"{float(pf['P'][0]):,.2f} € unrealized")

    st.subheader("Latest card payments")
    st.dataframe(q(f"""SELECT event_ts AS "Time (UTC)", merchant_name AS "Merchant", category AS "Category",
                              amount_eur AS "Amount (€)", status AS "Status", booking_status AS "Booking",
                              is_suspicious AS "Fraud alert"
                       FROM DATABANK.MARTS.FCT_CARD_TRANSACTIONS WHERE client_id = '{cid}'
                       ORDER BY event_ts DESC LIMIT 15"""), use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Spending by category · 30 days")
        st.bar_chart(q(f"""SELECT category, SUM(spend_eur)::FLOAT AS spend_eur FROM DATABANK.MARTS.CLIENT_DAILY_SPEND
                           WHERE client_id = '{cid}' AND event_date >= DATEADD(day, -30, CURRENT_DATE())
                           GROUP BY 1 ORDER BY 2 DESC"""), x="CATEGORY", y="SPEND_EUR")
    with right:
        st.subheader("Portfolio")
        st.dataframe(q(f"""SELECT ticker, quantity, close_usd, price_date, market_value_eur, unrealized_pnl_eur
                           FROM DATABANK.MARTS.PORTFOLIO_VALUATION WHERE client_id = '{cid}' ORDER BY market_value_eur DESC"""),
                     use_container_width=True)

# ------------------------------------------------------------------ markets
with tab_market:
    st.subheader("Stock prices of the securities our clients hold (Marketplace share · real data)")
    tick = st.selectbox("Ticker", ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "JPM", "V", "MA", "TSLA"])
    st.line_chart(q(f"""SELECT price_date, close_eur::FLOAT AS close_eur FROM DATABANK.MARTS.STOCK_PRICES_DAILY
                        WHERE ticker = '{tick}' AND price_date >= DATEADD(year, -1, CURRENT_DATE()) ORDER BY 1"""),
                  x="PRICE_DATE", y="CLOSE_EUR")
    st.subheader("EUR/USD - two independent sources (ECB API vs Marketplace)")
    st.line_chart(q("""SELECT rate_date, ecb_api_rate::FLOAT AS ecb_api, marketplace_rate::FLOAT AS marketplace
                       FROM DATABANK.MARTS.FX_RATES_DAILY WHERE currency = 'USD'
                         AND rate_date >= DATEADD(year, -1, CURRENT_DATE()) ORDER BY 1"""),
                  x="RATE_DATE", y=["ECB_API", "MARKETPLACE"])

# ------------------------------------------------------------------ ops
with tab_ops:
    st.subheader("Source freshness")
    st.dataframe(q("SELECT * FROM DATABANK.OPS.SOURCE_FRESHNESS"), use_container_width=True)
    a, b = st.columns(2)
    with a:
        st.subheader("Quarantined messages")
        st.dataframe(q("""SELECT reject_reason, COUNT(*) AS n FROM DATABANK.MARTS.DQ_REJECTED_AUTHORIZATIONS
                          GROUP BY 1 ORDER BY 2 DESC"""), use_container_width=True)
    with b:
        st.subheader("Ingestion latency (last hour)")
        st.dataframe(q("""SELECT COUNT(*) AS payments, ROUND(AVG(ingest_latency_ms)) AS avg_ms,
                                 MAX(ingest_latency_ms) AS max_ms
                          FROM DATABANK.MARTS.FCT_CARD_TRANSACTIONS
                          WHERE ingested_at > DATEADD(hour, -1, SYSDATE())"""), use_container_width=True)
