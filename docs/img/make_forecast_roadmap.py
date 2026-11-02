"""Draws docs/img/forecast_roadmap.svg: Databank forecast 2026-2030 against Gartner signals."""
import html

W, H = 1800, 860
NAVY = "#0F1B2D"; BLUE = "#29B5E8"; DBLUE = "#1E6FA8"; GREY = "#5F6673"; LINE = "#C9D2DC"
GREEN = "#1F8A5B"; GFILL = "#EEF8F2"; RED = "#C0392B"; RFILL = "#FDF0EE"; ORANGE = "#C2611B"; OFILL = "#FFF6EE"
out = []


def a(s): out.append(s)


def esc(t): return html.escape(t)


def text(x, y, t, size=13, col=GREY, anchor="start", weight=400):
    a(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" fill="{col}">{esc(t)}</text>')


def card(x, y, w, h, title, lines, fill, stroke, tcol=NAVY):
    a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
    text(x + 12, y + 22, title, 14, tcol, weight=700)
    for i, L in enumerate(lines):
        text(x + (21 if L.startswith(" ") else 12), y + 42 + i * 17, L.strip() if L.startswith(" ") else ("• " + L), 12.5, GREY)


a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Arial, Helvetica, sans-serif">')
a(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')
text(30, 44, "Databank · forecast 2026 → 2030, based on Gartner signals", 26, NAVY, weight=700)
text(30, 70, "Top: what Gartner predicts (published figures) · Below: what we expect for Databank (our forecast)", 15, GREY)

# columns
cols = [("TODAY · 2026", "what we built"), ("2027", "foundations"), ("2028", "real time"), ("2029 – 2030", "governed AI")]
x0, cw, gap = 230, 380, 12
for i, (t, s) in enumerate(cols):
    x = x0 + i * (cw + gap)
    a(f'<rect x="{x}" y="88" width="{cw}" height="44" rx="8" fill="{NAVY if i else DBLUE}"/>')
    text(x + cw / 2, 116, f"{t}  ·  {s}", 16, "#FFFFFF", "middle", 700)
# arrow of time
a(f'<line x1="{x0}" y1="146" x2="{x0 + 4 * cw + 3 * gap}" y2="146" stroke="{LINE}" stroke-width="3"/>')

lanes = [("Gartner\nsignals", 160, 150),
         ("Data &\nstreaming", 322, 140),
         ("AI &\nagents", 474, 140),
         ("Governance\n& regulation", 626, 150)]
for name, y, h in lanes:
    a(f'<rect x="30" y="{y}" width="185" height="{h}" rx="10" fill="#F4F7FA" stroke="{LINE}"/>')
    for k, part in enumerate(name.split("\n")):
        text(122, y + h / 2 - 4 + k * 20, part, 16, NAVY, "middle", 700)

sig = [("Signals already true", ["40% of enterprise apps embed AI agents", " by end of 2026 (from < 5% in 2025)", "60% of AI projects without AI-ready data", " abandoned (through 2026)"]),
       ("2027", [">40% of agentic AI projects cancelled", " (cost, unclear value, weak risk control)", "Only ~130 genuine agentic vendors", "EU AI Act credit scoring: 2 Dec 2027"]),
       ("2028", ["Event-driven 'agentic data streaming'", " > 60% adoption (from < 15% in 2025)", "15% of daily work decisions autonomous", "33% of enterprise software agentic"]),
       ("2029 – 2030", ["Modelled decisions 5x more trusted", "Semantic layer = critical infrastructure", "50% use agents to write data contracts", "40% of enterprises used GraphRAG"])]
for i, (t, L) in enumerate(sig):
    card(x0 + i * (cw + gap), 160, cw, 150, t, L, OFILL, "#E8C29F", ORANGE)

data = [("Today", ["Micro-batches every 10 s, 1-min lag", "6 ingestion methods, Snowflake tables", "dbt: 32 models, 43 tests"]),
        ("2027", ["Kafka (MSK) + log-based CDC", " for payments and core banking", "Data contracts on every source"]),
        ("2028", ["Most flows event-driven", "Flink fraud score before payment", "Bronze on Apache Iceberg (S3)"]),
        ("2029 – 2030", ["Open lakehouse, several engines", "Platform serves agents as well", " as dashboards"])]
for i, (t, L) in enumerate(data):
    card(x0 + i * (cw + gap), 322, cw, 140, t, L, "#F2FAFE" if i == 0 else GFILL, "#A9D8EE" if i == 0 else "#9FD3B8")

ai = [("Today", ["Rule-based fraud score", "No AI in production", ""]),
      ("2027", ["AI assistant for analysts,", " on governed Gold data only", "Credit model documented"]),
      ("2028", ["Supervised agents: alert triage,", " report drafting, human approves", "Metrics defined once (semantic layer)"]),
      ("2029 – 2030", ["Graph-based AML (GraphRAG)", "Agents take small, reversible", " decisions within strict limits"])]
for i, (t, L) in enumerate(ai):
    card(x0 + i * (cw + gap), 474, cw, 140, t, [l for l in L if l], "#F2FAFE" if i == 0 else GFILL, "#A9D8EE" if i == 0 else "#9FD3B8")

gov = [("Today", ["5 roles, masking, row access policy", "EU region only (Paris)", "Lineage: file, batch, run id"]),
       ("2027", ["Terraform, dev / test / prod", "EU AI Act ready for credit scoring", "Replica in Frankfurt (DORA)"]),
       ("2028", ["Automatic personal-data tagging", "Masking applied by tag", "Every automated decision logged"]),
       ("2029 – 2030", ["Decision governance in production", "Contracts drafted by agents,", " approved by humans"])]
for i, (t, L) in enumerate(gov):
    card(x0 + i * (cw + gap), 626, cw, 150, t, L, "#F2FAFE" if i == 0 else GFILL, "#A9D8EE" if i == 0 else "#9FD3B8")

text(30, 812, "Orange = Gartner published predictions and the EU AI Act deadline (sources in docs/forecast.md)  ·  Blue = what Databank runs today  ·  Green = our forecast for Databank", 13, GREY)
text(30, 836, "Expected scenario: streaming and assistants become mainstream; financial decisions stay supervised by humans until governance and regulation allow more", 13, GREY)
a('</svg>')
open('forecast_roadmap.svg', 'w').write("\n".join(out))
print("ok")
