"""Slide versions of the three diagrams, in the colours of the Canva deck (greens, Poppins), with icons.

Writes slide_current.svg, slide_target.svg, slide_forecast.svg next to this file.
Render: node render.js <svg> <png> <width> <height>  (any browser screenshot works).
Icons are simple generic line icons drawn here (no brand logos); tool names are written as text.
"""
import html

DARK = "#347470"; GREEN = "#35b276"; MID = "#5ec57e"; LIGHT = "#b8e28a"; PALE = "#e7ffcc"
INK = "#2f3a3a"; GREY = "#5a6470"; LINE = "#8fb79a"; WHITE = "#ffffff"; SOFT = "#f4faef"; HOT = "#1f5c58"

ICONS = {  # 24x24 line icons
    "card": '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20M6 15h4"/>',
    "db": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    "chart": '<path d="M3 21h18"/><path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "euro": '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5a4.5 4.5 0 1 0 0 7"/><path d="M7.5 11h6M7.5 13.5h6"/>',
    "file": '<path d="M6 2h8l4 4v16H6z"/><path d="M14 2v4h4M9 12h6M9 16h6"/>',
    "phone": '<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/>',
    "bolt": '<path d="M13 2L4 14h8l-1 8 9-12h-8z"/>',
    "layers": '<path d="M12 2l10 5-10 5L2 7z"/><path d="M2 12l10 5 10-5"/><path d="M2 17l10 5 10-5"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
    "shield": '<path d="M12 2l8 3v6c0 5-3.5 9-8 11-4.5-2-8-6-8-11V5z"/><path d="M9 12l2 2 4-4"/>',
    "monitor": '<rect x="2" y="4" width="20" height="13" rx="2"/><path d="M8 21h8M12 17v4"/><path d="M6 13l3-3 3 2 4-4"/>',
    "bank": '<path d="M12 2l10 5H2z"/><path d="M5 10v8M9.7 10v8M14.3 10v8M19 10v8M2 21h20"/>',
    "users": '<circle cx="9" cy="8" r="4"/><path d="M2 21c0-4 3-6 7-6s7 2 7 6"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 15c2.5.6 4 2.6 4 6"/>',
    "spark": '<path d="M12 3l2 5 5 2-5 2-2 5-2-5-5-2 5-2z"/><path d="M19 15l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z"/>',
    "bell": '<path d="M6 16v-5a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 21h4"/>',
    "cloud": '<path d="M7 19h10a4.5 4.5 0 0 0 .5-9 6 6 0 0 0-11.6 1.6A3.7 3.7 0 0 0 7 19z"/>',
    "code": '<path d="M8 6l-6 6 6 6M16 6l6 6-6 6M14 4l-4 16"/>',
    "box": '<path d="M12 2l9 5v10l-9 5-9-5V7z"/><path d="M3 7l9 5 9-5M12 12v10"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "lock": '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "eye": '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/>',
    "repeat": '<path d="M4 12a8 8 0 0 1 14-5.3L20 9"/><path d="M20 4v5h-5"/><path d="M20 12a8 8 0 0 1-14 5.3L4 15"/><path d="M4 20v-5h5"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-5-5"/>',
    "people": '<circle cx="12" cy="7" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/>',
    "flag": '<path d="M5 22V3"/><path d="M5 4h12l-2 4 2 4H5"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18"/>',
}


class SVG:
    def __init__(self, w, h):
        self.w, self.h, self.o = w, h, []
        self.a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="Poppins, Arial, sans-serif">')
        self.a('<defs>'
               f'<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker>'
               f'<marker id="ahh" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{HOT}"/></marker>'
               '</defs>')
        self.a(f'<rect width="{w}" height="{h}" fill="{WHITE}"/>')

    def a(self, s): self.o.append(s)

    def text(self, x, y, t, size=14, col=GREY, anchor="start", weight=400):
        self.a(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" fill="{col}">{html.escape(t)}</text>')

    def icon(self, name, x, y, s=24, col=DARK, bg=PALE, pad=8):
        if bg:
            self.a(f'<circle cx="{x + s / 2}" cy="{y + s / 2}" r="{s / 2 + pad}" fill="{bg}"/>')
        k = s / 24
        self.a(f'<g transform="translate({x},{y}) scale({k})" fill="none" stroke="{col}" stroke-width="{2 / max(k, .6):.2f}" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>')

    def rect(self, x, y, w, h, fill=WHITE, stroke=LIGHT, sw=2, r=14, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def card(self, x, y, w, h, title, sub=(), icon=None, fill=WHITE, stroke=LIGHT, tcol=INK, ts=16, ss=12.5, center=False, tag=None, sw=2):
        self.rect(x, y, w, h, fill, stroke, sw)
        sub = [sub] if isinstance(sub, str) else list(sub)
        lines = [title] if isinstance(title, str) else list(title)
        tot = len(lines) * (ts + 4) + len(sub) * (ss + 4)
        cy = y + h / 2 - tot / 2 + ts - 2
        if icon:
            isz = min(26, h - 30)
            self.icon(icon, x + 16, y + h / 2 - isz / 2, isz, pad=7)
            tx, anchor = x + isz + 38, "start"
        elif center:
            tx, anchor = x + w / 2, "middle"
        else:
            tx, anchor = x + 16, "start"
        for L in lines:
            self.text(tx, cy, L, ts, tcol, anchor, 600); cy += ts + 4
        for L in sub:
            self.text(tx, cy + 1, L, ss, GREY, anchor); cy += ss + 4
        if tag:
            tw = len(tag) * 7.5 + 16
            self.a(f'<rect x="{x + w - tw - 8}" y="{y + 8}" width="{tw}" height="20" rx="10" fill="{GREEN}"/>')
            self.text(x + w - tw / 2 - 8, y + 22, tag, 11, WHITE, "middle", 700)

    def num(self, x, y, n, col=GREEN, r=13):
        self.a(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{col}"/>')
        self.text(x, y + 4.5, str(n), 12.5, WHITE, "middle", 700)

    def arrow(self, x1, y1, x2, y2, col=LINE, w=2.2, mk="ah", dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.a(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}" marker-end="url(#{mk})"{d}/>')

    def poly(self, pts, col=LINE, w=2.2, mk="ah", dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        p = " ".join(f"{x},{y}" for x, y in pts)
        self.a(f'<polyline points="{p}" fill="none" stroke="{col}" stroke-width="{w}" marker-end="url(#{mk})"{d}/>')

    def label(self, x, y, t, col=DARK, anchor="start", size=14):
        self.text(x, y, t, size, col, anchor, 700)

    def save(self, path):
        self.a('</svg>')
        open(path, "w").write("\n".join(self.o))


# =====================================================================  1. CURRENT PIPELINE
def current():
    s = SVG(1840, 840)
    srcs = [("card", "Card terminals", "JSON · simulated", None), ("bank", "Core banking", "clients, accounts", None),
            ("chart", "Market data", "Marketplace prices, FX", "REAL"), ("euro", "ECB rates API", "euro reference rates", "REAL"),
            ("file", "Banque de France", "registry CSV files", None), ("phone", "Mobile app", "events · JSON lines", None)]
    ing = [("Micro-batch stream", "every 10 s"), ("CDC: streams + task", "every 15 min"), ("Secure data share", "zero copy"),
           ("REST API, incremental", "in a Docker container"), ("PUT + Snowpipe", "REST-triggered"), ("PUT + COPY INTO", "batch")]
    bronze = ["RAW card payments", "CORE_BANKING + changes", "Shared market DB", "RAW ECB rates", "RAW BdF registry", "RAW app events"]
    y0, h, g = 62, 92, 16
    s.label(20, 40, "SOURCES")
    s.rect(345, 20, 290, 6 * (h + g) + 30, SOFT, LIGHT, 2, 18, "6 6")
    s.label(362, 46, "GITHUB ACTIONS")
    s.rect(670, 20, 790, 810, "#f7fcf3", GREEN, 2.5, 22, "10 7")
    s.a(f'<rect x="935" y="6" width="270" height="30" rx="15" fill="{GREEN}"/>')
    s.icon("cloud", 950, 10, 22, WHITE, None)
    s.label(982, 27, "SNOWFLAKE · AWS PARIS", WHITE, "start", 14)
    s.label(690, 46, "BRONZE", GREY); s.label(945, 46, "SILVER", GREY); s.label(1195, 46, "GOLD", GREY)
    s.label(1500, 40, "CONSUMERS")
    for i in range(6):
        y = y0 + i * (h + g); cy = y + h / 2
        ic, t, sub, tag = srcs[i]
        s.card(20, y, 300, h, t, sub, ic, fill=(PALE if tag else WHITE), stroke=(GREEN if tag else LIGHT), tag=tag)
        s.card(362, y + 8, 258, h - 16, ing[i][0], ing[i][1], ts=14.5, ss=12, center=True)
        s.num(362, y + 8, i + 1)
        s.arrow(320, cy, 360, cy); s.arrow(620, cy, 688, cy)
        s.card(690, y + 12, 230, h - 24, bronze[i], (), ts=13.5, center=True)
        s.arrow(920, cy, 943, cy)
    s.card(945, y0 + 12, 225, 3 * (h + g) - 24, "STAGING", ["11 views", "1 per source", "typed, renamed,", "flagged"], "layers", ts=17, ss=13)
    s.card(945, y0 + 3 * (h + g) + 12, 225, 3 * (h + g) - 24, "INTERMEDIATE", ["de-duplicated", "client history", "ECB vs Marketplace", "credit status"], "repeat", ts=16, ss=13)
    gold = [("FINANCE", "transactions, clients"), ("SERVING · LIVE", "balance, app views"), ("REGULATORY", "BdF report, AML"),
            ("MARKET", "FX, prices in €"), ("DIGITAL", "app engagement"), ("DATA QUALITY", "rejected messages")]
    for i, (t, sub) in enumerate(gold):
        y = y0 + i * (h + g) + 10
        s.card(1195, y, 245, h - 20, t, sub, ts=14.5, ss=12, center=True, stroke=(GREEN if "LIVE" in t else LIGHT))
        s.arrow(1170, y + (h - 20) / 2, 1193, y + (h - 20) / 2)
    chips = [("gear", "dbt build + tests", "task graph · 15 min"), ("bolt", "Dynamic tables", "live · 1 min"), ("lock", "Governance", "roles · masking · rows")]
    for i, (ic, t, sub) in enumerate(chips):
        x = 690 + i * 255
        s.card(x, 718, 240, 90, t, sub, ic, fill=WHITE, stroke=GREEN, ts=14.5, ss=12)
    cons = [("phone", "Mobile app", ["live balance < 2 min", "own rows only"]), ("monitor", "Dashboard", ["Streamlit", "clients · advisors · ops"]),
            ("bank", "Regulators", ["Banque de France", "AML → Tracfin"]), ("users", "Analysts", ["SQL on Gold", "masked personal data"])]
    for i, (ic, t, sub) in enumerate(cons):
        y = 80 + i * 190
        s.card(1500, y, 320, 130, t, sub, ic, ts=18, ss=13)
        s.arrow(1440, y + 65, 1498, y + 65)
    s.save("slide_current.svg")


# =====================================================================  2. BEST CASE
def target():
    s = SVG(1840, 900)
    # hot path
    s.rect(330, 14, 1500, 118, "#eef6f4", HOT, 2, 18, "7 6")
    s.label(1815, 40, "HOT PATH · REAL TIME (MILLISECONDS)", HOT, "end", 13)
    hot = [("bolt", "Kafka (Amazon MSK)", "one log for payments + CDC"), ("search", "Managed Flink", "fraud score < 100 ms"),
           ("db", "Operational Postgres", "balances, pending payments"), ("bell", "Push notifications", "payment + fraud alerts")]
    for i, (ic, t, sub) in enumerate(hot):
        x = 350 + i * 365
        s.card(x, 50, 330, 70, t, sub, ic, stroke=HOT, ts=14.5, ss=12)
        if i < 3:
            s.arrow(x + 330, 85, x + 363, 85, col=HOT, mk="ahh")
    # columns
    s.label(14, 176, "SOURCES"); s.label(312, 176, "INGESTION · MANAGED")
    s.rect(600, 156, 640, 560, "#f7fcf3", GREEN, 2.5, 22, "10 7")
    s.label(620, 182, "SNOWFLAKE + ICEBERG LAKEHOUSE", DARK, "start", 13)
    s.label(1262, 176, "AI / ML"); s.label(1505, 176, "CONSUMERS")
    srcs = [("card", "Card terminals", None), ("bank", "Core banking", None), ("chart", "Market data", "REAL"), ("euro", "ECB rates", "REAL"),
            ("file", "Banque de France", None), ("phone", "Mobile app", None), ("users", "CRM & KYC", "NEW")]
    ing = ["Kafka → Snowpipe Streaming", "Log-based CDC (Debezium)", "Paid intraday share", "Openflow connector",
           "SFTP → S3 → Snowpipe", "Snowplow → Firehose", "Openflow SaaS connectors"]
    y0, h, g = 196, 66, 8
    for i in range(7):
        y = y0 + i * (h + g); cy = y + h / 2
        ic, t, tag = srcs[i]
        s.card(14, y, 272, h, t, (), ic, fill=(PALE if tag == "REAL" else WHITE), stroke=(GREEN if tag else LIGHT), ts=14, tag=tag)
        s.card(312, y + 6, 262, h - 12, ing[i], (), ts=13, center=True, stroke=GREEN if i in (0, 1, 2, 4, 5, 6) else LIGHT)
        s.arrow(286, cy, 310, cy); s.arrow(574, cy, 618, cy)
    s.poly([(580, y0 + 18), (590, y0 + 18), (590, 136)], col=HOT, mk="ahh", dash="5 4")
    s.card(620, y0 + 10, 180, 7 * (h + g) - 28, "BRONZE", ["Apache Iceberg", "on S3", "", "open format,", "any engine"], "layers", ts=16, ss=12.5)
    s.card(818, y0 + 10, 190, 250, "STAGING", ["dbt", "data contracts", "checked at entry"], ts=16, ss=12.5, center=True)
    s.card(818, y0 + 278, 190, 230, "INTERMEDIATE", ["customer 360°", "history from CDC"], ts=15, ss=12.5, center=True)
    for i, t in enumerate(["FINANCE", "SERVING", "RISK & AML", "REGULATORY", "MARKET", "DIGITAL"]):
        y = y0 + 10 + i * 82
        s.card(1026, y, 196, 70, t, (), ts=14, center=True)
        s.arrow(1008, y + 35, 1024, y + 35)
    ml = [("spark", "Feature store", "fraud, credit, churn"), ("box", "Model registry", "versioned, monitored"),
          ("search", "AI assistant", "questions in plain words"), ("file", "Document AI", "reads KYC documents")]
    for i, (ic, t, sub) in enumerate(ml):
        y = y0 + 10 + i * 126
        s.card(1262, y, 220, 108, t, sub, ic, fill=PALE, stroke=GREEN, ts=14.5, ss=12)
        s.arrow(1222, y + 54, 1260, y + 54)
    cons = [("phone", "Mobile app", "balance < 1 s"), ("monitor", "BI self-service", "certified metrics"),
            ("bank", "Regulators", "automated reports"), ("users", "Advisors' CRM", "live risk (reverse ETL)"), ("chart", "Data science", "notebooks + features")]
    for i, (ic, t, sub) in enumerate(cons):
        y = y0 + i * 104
        s.card(1505, y, 320, 90, t, sub, ic, ts=15.5, ss=12)
        s.arrow(1482, y + 45, 1503, y + 45)
    s.poly([(1730, 132), (1730, y0 - 4)], col=HOT, mk="ahh")
    # platform band
    s.label(14, 760, "PLATFORM")
    s.label(14, 780, "SERVICES", DARK)
    s.text(14, 806, "apply to every", 12.5, GREY); s.text(14, 824, "step above", 12.5, GREY)
    bands = [("clock", "Airflow", "one DAG, all tools"), ("gear", "dbt platform", "CI, dev/test/prod"), ("eye", "Observability", "contracts, anomalies"),
             ("shield", "Governance", "auto PII tags, keys"), ("code", "Terraform + Docker", "AWS + Snowflake"), ("globe", "Resilience", "Paris → Frankfurt")]
    for i, (ic, t, sub) in enumerate(bands):
        x = 170 + i * 278
        s.card(x, 740, 262, 96, t, sub, ic, fill=WHITE, stroke=GREEN, ts=14.5, ss=12)
    s.text(14, 878, "Green outline = new or upgraded compared with today  ·  Dark teal = new real-time hot path  ·  Same Bronze / Silver / Gold layers and dbt models as today", 13, GREY)
    s.save("slide_target.svg")


# =====================================================================  3. FORECAST
def forecast():
    s = SVG(1840, 860)
    cols = [("TODAY · 2026", "what we built"), ("2027", "foundations"), ("2028", "real time"), ("2029 – 2030", "governed AI")]
    x0, cw, gap = 262, 384, 10
    for i, (t, sub) in enumerate(cols):
        x = x0 + i * (cw + gap)
        s.a(f'<rect x="{x}" y="10" width="{cw}" height="52" rx="26" fill="{DARK if i == 0 else GREEN}"/>')
        s.text(x + cw / 2, 43, f"{t}  ·  {sub}", 17, WHITE, "middle", 700)
    s.arrow(x0, 78, x0 + 4 * cw + 3 * gap - 4, 78, col=LIGHT, w=4)
    lanes = [("Gartner", "signals", "flag", 96, 170), ("Data &", "streaming", "bolt", 280, 160),
             ("AI &", "agents", "spark", 454, 160), ("Governance", "& rules", "shield", 628, 170)]
    for a1, a2, ic, y, h in lanes:
        s.rect(10, y, 236, h, PALE, PALE, 0, 16)
        s.icon(ic, 30, y + h / 2 - 14, 28, DARK, WHITE, 9)
        s.text(80, y + h / 2 - 4, a1, 17, DARK, "start", 700)
        s.text(80, y + h / 2 + 18, a2, 17, DARK, "start", 700)

    def card(i, y, h, title, lines, kind):
        x = x0 + i * (cw + gap)
        fill, stroke, tcol = {"sig": ("#f1f5f4", "#c5d6d2", HOT), "now": (WHITE, DARK, DARK), "fut": (WHITE, LIGHT, INK)}[kind]
        s.rect(x, y, cw, h, fill, stroke, 2, 14)
        s.text(x + 16, y + 30, title, 16, tcol, "start", 700)
        yy = y + 58
        for L in lines:
            if L.startswith(" "):
                s.text(x + 30, yy, L.strip(), 14.5, GREY)
            else:
                s.a(f'<circle cx="{x + 21}" cy="{yy - 4.5}" r="3.5" fill="{GREEN}"/>')
                s.text(x + 30, yy, L, 14.5, GREY)
            yy += 24

    sig = [("Already true", ["40% of business apps embed AI agents", " by end of 2026 (from < 5% in 2025)", "60% of AI projects without AI-ready", " data abandoned"]),
           ("2027", ["> 40% of agentic AI projects cancelled", " (cost, unclear value, weak control)", "EU AI Act for credit scoring:", " 2 December 2027"]),
           ("2028", ["Event-driven data streaming > 60%", " of companies (from < 15% in 2025)", "15% of daily work decisions", " made by agents"]),
           ("2029 – 2030", ["Semantic layer = critical infrastructure", "50% use agents to write data contracts", "40% of companies use GraphRAG"])]
    data = [("Today", ["Micro-batches every 10 s", "6 ingestion methods", "dbt: 32 models, 43 tests"]),
            ("2027", ["Kafka + log-based CDC", "Data contracts on every source", "Terraform for every object"]),
            ("2028", ["Most flows event-driven", "Fraud score before payment", "Bronze on Apache Iceberg"]),
            ("2029 – 2030", ["Open lakehouse, several engines", "Platform serves agents", " as well as dashboards"])]
    ai = [("Today", ["Rule-based fraud score", "No AI in production"]),
          ("2027", ["AI assistant for analysts,", " on governed Gold data only", "Credit model documented"]),
          ("2028", ["Supervised agents: alert triage,", " report drafts; a human approves", "Metrics defined once"]),
          ("2029 – 2030", ["Graph-based anti-money laundering", "Agents take small, reversible", " decisions within strict limits"])]
    gov = [("Today", ["5 roles, masking, row access", "EU region only (Paris)", "Lineage: file, batch, run id"]),
           ("2027", ["Dev / test / prod environments", "EU AI Act ready (credit scoring)", "Replica in Frankfurt (DORA)"]),
           ("2028", ["Personal data tagged automatically", "Masking applied by tag", "Every automated decision logged"]),
           ("2029 – 2030", ["Decision governance in production", "Contracts drafted by agents,", " approved by humans"])]
    for i in range(4):
        card(i, 96, 170, *sig[i], "sig")
        card(i, 280, 160, *data[i], "now" if i == 0 else "fut")
        card(i, 454, 160, *ai[i], "now" if i == 0 else "fut")
        card(i, 628, 170, *gov[i], "now" if i == 0 else "fut")
    s.text(10, 836, "Grey = Gartner published predictions and the EU AI Act deadline (sources in docs/forecast.md)  ·  Dark outline = what Databank runs today  ·  Green outline = our forecast", 13, GREY)
    s.save("slide_forecast.svg")


if __name__ == "__main__":
    current(); target(); forecast()
    print("ok")
