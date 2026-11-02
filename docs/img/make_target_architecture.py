"""Draws docs/img/target_architecture.svg: the "best case" (unlimited budget) Databank pipeline.
Same visual language as make_architecture.py. Render to PNG with any browser (see README in docs)."""
import html

W, H = 1900, 1150
NAVY = "#0F1B2D"; BLUE = "#29B5E8"; DBLUE = "#1E6FA8"; ORANGE = "#C2611B"; GREY = "#5F6673"
LINE = "#9AA5B1"; GREEN = "#1F8A5B"; GFILL = "#EEF8F2"; RED = "#C0392B"; RFILL = "#FDF0EE"
out = []


def a(s): out.append(s)


def esc(t): return html.escape(t)


def box(x, y, w, h, title, sub=None, fill="#FFFFFF", stroke="#C9D2DC", tcol=NAVY, r=10, tsize=15, ssize=12, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"{d}/>')
    lines = [title] if isinstance(title, str) else title
    sl = [] if sub is None else ([sub] if isinstance(sub, str) else sub)
    total = len(lines) * (tsize + 3) + len(sl) * (ssize + 3)
    cy = y + h / 2 - total / 2 + tsize
    for L in lines:
        a(f'<text x="{x + w / 2}" y="{cy}" text-anchor="middle" font-size="{tsize}" font-weight="700" fill="{tcol}">{esc(L)}</text>'); cy += tsize + 3
    for L in sl:
        a(f'<text x="{x + w / 2}" y="{cy + 1}" text-anchor="middle" font-size="{ssize}" fill="{GREY}">{esc(L)}</text>'); cy += ssize + 3


def badge(x, y, letter, col=NAVY):
    a(f'<rect x="{x}" y="{y}" width="26" height="26" rx="6" fill="{col}"/><text x="{x + 13}" y="{y + 18}" text-anchor="middle" font-size="15" font-weight="700" fill="#fff">{letter}</text>')


def step(x, y, n, col=ORANGE):
    a(f'<circle cx="{x}" cy="{y}" r="13" fill="{col}"/><text x="{x}" y="{y + 5}" text-anchor="middle" font-size="13" font-weight="700" fill="#fff">{n}</text>')


def arrow(x1, y1, x2, y2, col=LINE, w=2, dash=None, mk="ah"):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    a(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}" marker-end="url(#{mk})"{d}/>')


def poly(points, col=LINE, w=2, dash=None, mk="ah"):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    pts = " ".join(f"{x},{y}" for x, y in points)
    a(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{w}" marker-end="url(#{mk})"{d}/>')


def text(x, y, t, size=13, col=GREY, anchor="start", weight=400):
    a(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" fill="{col}">{esc(t)}</text>')


a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Arial, Helvetica, sans-serif">')
a('<defs>'
  f'<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker>'
  f'<marker id="ahr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{RED}"/></marker>'
  '</defs>')
a(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')
text(30, 44, "Databank · target architecture (best case: unlimited budget, best current platforms)", 26, NAVY, weight=700)
text(30, 70, "Still one cloud: AWS (Paris eu-west-3, replica in Frankfurt) · Kafka + Flink hot path · Iceberg lakehouse · Snowflake · dbt platform · Airflow · Terraform", 15, GREY)

# ---------------------------------------------------------------- hot path lane (real time)
LY, LH = 96, 112
a(f'<rect x="300" y="{LY}" width="1575" height="{LH}" rx="14" fill="{RFILL}" stroke="{RED}" stroke-width="1.5" stroke-dasharray="6 5"/>')
a(f'<text x="1860" y="{LY + 22}" text-anchor="end" font-size="13" font-weight="700" fill="{RED}">HOT PATH · real time (milliseconds)</text>')
hot = [(330, "Amazon MSK (Kafka)", ["one event log for payments", "and core banking changes"]),
       (640, "Managed Apache Flink", ["fraud score < 100 ms,", "before the payment is accepted"]),
       (950, "Snowflake Postgres", ["operational store: balances,", "pending payments (OLTP)"]),
       (1260, "Push notifications", ["\"You paid 12.40 € at…\"", "fraud alerts to the client"])]
for i, (x, t, s) in enumerate(hot):
    box(x, LY + 32, 270, 70, t, s, fill="#FFFFFF", stroke="#E3A79F", tsize=14, ssize=11.5)
    step(x, LY + 32, f"H{i + 1}", RED)
    if i < 3:
        arrow(x + 270, LY + 67, x + 308, LY + 67, col=RED, mk="ahr")
poly([(1530, LY + 67), (1742, LY + 67), (1742, 246)], col=RED, mk="ahr")
text(1750, LY + 95, "< 1 s to the app", 12, RED, weight=700)

# ---------------------------------------------------------------- columns
srcs = [("A", "Card terminals", "authorizations · real time"),
        ("B", "Core banking (OLTP)", "Oracle / Postgres database"),
        ("C", "Market data · REAL", "real-time paid feed"),
        ("D", "ECB API · REAL", "euro reference rates"),
        ("E", "Banque de France", "registry files via SFTP"),
        ("F", "Mobile app", "clickstream events"),
        ("G", "CRM, KYC, open banking", "NEW · Salesforce · ID checks · PSD2")]
ing = [("1", "Kafka producers → MSK", "Snowpipe Streaming to Bronze"),
       ("2", "Log-based CDC (Debezium)", "MSK Connect · every change, < 1 s"),
       ("3", "Marketplace share (paid)", "LSEG / FactSet · intraday"),
       ("4", "Snowflake Openflow", "managed connector · daily"),
       ("5", "SFTP → S3 → Snowpipe", "AWS Transfer Family · auto-ingest"),
       ("6", "Snowplow → Kinesis Firehose", "written as Iceberg / Parquet on S3"),
       ("7", "Openflow connectors", "SaaS APIs · incremental")]
bronze = [("RAW payments", "Iceberg · streamed"), ("RAW CDC log", "Iceberg · every change"),
          ("Shared market DB", "zero copy"), ("RAW ECB rates", "Iceberg"),
          ("RAW BdF files", "Iceberg · lineage"), ("RAW app events", "Iceberg · partitioned by day"),
          ("RAW CRM / KYC", "Iceberg")]
NEW = {"A", "B", "C", "E", "F", "G"}  # sources whose method changes vs today

y0, hh, gap = 248, 84, 10
# containers
a(f'<rect x="290" y="226" width="285" height="{7 * (hh + gap) + 18}" rx="16" fill="#FAFAFA" stroke="#C9D2DC" stroke-width="1.5" stroke-dasharray="4 5"/>')
a(f'<text x="575" y="{y0 - 28 + 0}" text-anchor="end" font-size="13" font-weight="700" fill="{GREY}"></text>')
a(f'<rect x="595" y="226" width="975" height="{7 * (hh + gap) + 18}" rx="16" fill="#F2FAFE" stroke="{BLUE}" stroke-width="2" stroke-dasharray="8 6"/>')
for x, t in [(30, "SOURCES"), (300, "INGESTION · managed on AWS"), (612, "BRONZE · open lakehouse"), (845, "SILVER"),
             (1075, "GOLD · data products"), (1400, "AI / ML"), (1615, "CONSUMERS")]:
    text(x, 244 - 4 if x in (300, 612, 845, 1075, 1400) else 240, t, 13, GREY, weight=700)
for i in range(7):
    y = y0 + i * (hh + gap); cy = y + hh / 2
    fill = "#FFF6EE" if "REAL" in srcs[i][1] else (GFILL if srcs[i][0] == "G" else "#FFFFFF")
    box(30, y, 240, hh, srcs[i][1], srcs[i][2], fill=fill, tsize=14)
    badge(38, y + 8, srcs[i][0], GREEN if srcs[i][0] == "G" else NAVY)
    box(305, y + 8, 255, hh - 16, ing[i][1], ing[i][2], fill=(GFILL if srcs[i][0] in NEW else "#FFFFFF"),
        stroke=("#9FD3B8" if srcs[i][0] in NEW else "#C9D2DC"), tsize=13.5, ssize=11.5)
    step(305, y + 8, ing[i][0])
    arrow(270, cy, 303, cy)
    arrow(560, cy, 613, cy)
    box(615, y + 12, 200, hh - 24, bronze[i][0], bronze[i][1], stroke="#A9D8EE", tsize=13, ssize=11.5)
    arrow(815, cy, 843, cy)
# A and B also feed the hot path
for i in (0, 1):
    cy = y0 + i * (hh + gap) + hh / 2 - 18
    a(f'<line x1="560" y1="{cy}" x2="568" y2="{cy}" stroke="{RED}" stroke-width="2" stroke-dasharray="5 4"/>')
poly([(568, y0 + hh + gap + hh / 2 - 18), (568, LY + LH + 2)], col=RED, mk="ahr", dash="5 4")
text(300, 221, "A and B events also feed the hot path ↑", 12, RED, weight=700)

# silver
box(845, y0 + 12, 205, 300, "STAGING", ["dbt · 1 model per source", "typed, renamed, flagged", "", "data contracts:", "schema checked at the door"],
    stroke="#A9D8EE")
box(845, y0 + 332, 205, 312, "INTERMEDIATE", ["conformed customer 360°", "(core + CRM + KYC + app)", "SCD2 history from CDC", "FX: ECB vs paid feed"], stroke="#A9D8EE")
# gold
gold = [("FINANCE", ["transactions · balances", "star schema"]), ("SERVING", ["dynamic tables", "seconds-level lag"]),
        ("RISK & AML", ["features · alerts", "graph of linked accounts"]), ("REGULATORY", ["BdF / ECB reports", "generated automatically"]),
        ("MARKET", ["intraday prices", "portfolio value"]), ("DIGITAL", ["funnels · engagement", "churn signals"])]
gh = 96
for i, (t, s) in enumerate(gold):
    yy = y0 + 12 + i * (gh + 10)
    box(1075, yy, 205, gh, t, s, stroke="#A9D8EE", tsize=13.5, ssize=11.5)
    arrow(1050, yy + gh / 2 if yy + gh / 2 < y0 + 320 else yy + gh / 2, 1073, yy + gh / 2)
# AI / ML
ml = [("Feature store", ["shared features for", "fraud, credit, churn"]), ("Model registry", ["models versioned,", "monitored for drift"]),
      ("Cortex AI agent", ["analysts ask questions", "in plain language"]), ("Document AI", ["reads KYC documents", "and contracts"])]
for i, (t, s) in enumerate(ml):
    yy = y0 + 12 + i * 160
    box(1300, yy, 250, 130, t, s, fill=GFILL, stroke="#9FD3B8", tsize=14, ssize=12)
    arrow(1280, yy + 65, 1298, yy + 65)
# consumers
cons = [("Mobile app", ["balance & payments < 1 s", "from the operational store"]), ("BI & self-service", ["Sigma / Power BI on Gold", "certified metrics layer"]),
        ("Regulators", ["Banque de France, ECB", "automated, auditable reports"]), ("Operational tools", ["reverse ETL to CRM", "advisors see live risk"]),
        ("Data science", ["notebooks on Gold", "+ feature store"])]
for i, (t, s) in enumerate(cons):
    yy = 248 + i * 132
    box(1610, yy, 265, 110, t, s, tsize=15.5, ssize=12)
    arrow(1550, yy + 55 if yy + 55 < 870 else 860, 1608, yy + 55)
a(f'<text x="1570" y="{221}" text-anchor="end" font-size="14" font-weight="700" fill="{DBLUE}">❄ Snowflake (Business Critical) + Apache Iceberg on S3 · AWS Paris</text>')


# ---------------------------------------------------------------- platform bands
by = 940
bands = [("8", "Orchestration", ["Airflow (Amazon MWAA)", "one DAG across all tools", "retries · SLAs · alerts"]),
         ("9", "dbt platform", ["Fusion engine · CI on every", "change · dev / test / prod", "column-level lineage"]),
         ("10", "Quality & observability", ["data contracts · anomaly", "detection (Monte Carlo)", "OpenLineage end to end"]),
         ("11", "Governance & security", ["Horizon catalog · auto PII tags", "tag-based masking · PrivateLink", "customer-managed keys"]),
         ("12", "DevOps", ["Terraform: AWS + Snowflake", "Docker images (ECR) · CI/CD", "secrets in AWS Secrets Mgr"]),
         ("13", "Resilience (DORA)", ["replication Paris → Frankfurt", "tested failover", "RPO minutes · RTO < 1 h"])]
bw = 252
for i, (n, t, s) in enumerate(bands):
    x = 300 + i * (bw + 11)
    box(x, by, bw, 125, t, s, fill="#FFFFFF", stroke=BLUE, tsize=14.5, ssize=11.5)
    step(x, by, n, DBLUE)
text(330, by - 20, "PLATFORM SERVICES · apply to every step above", 13, GREY, weight=700)

# legend
text(30, 1100, "Green = new or upgraded compared with today's pipeline  ·  Red = new real-time hot path  ·  Real data: C, D  ·  Letters = sources, numbers = steps", 13, GREY)
text(30, 1124, "Today: micro-batch + Snowflake tasks + 1-minute lag · Target: event streaming + stream processing + seconds-to-milliseconds, same medallion layers and dbt models", 13, GREY)
a('</svg>')
open('target_architecture.svg', 'w').write("\n".join(out))
print("ok")
