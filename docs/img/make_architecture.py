import html
W,H=1600,930
NAVY="#0F1B2D"; BLUE="#29B5E8"; DBLUE="#1E6FA8"; ORANGE="#C2611B"; GREY="#5F6673"; LIGHT="#F4F7FA"; LINE="#9AA5B1"
out=[]
def a(s): out.append(s)
def esc(t): return html.escape(t)
def box(x,y,w,h,title,sub=None,fill="#FFFFFF",stroke="#C9D2DC",tcol=NAVY,r=10,tsize=15,ssize=12.5,dash=None,bold=True):
    d=f' stroke-dasharray="{dash}"' if dash else ''
    a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"{d}/>')
    lines=[title] if isinstance(title,str) else title
    sl=[] if sub is None else ([sub] if isinstance(sub,str) else sub)
    total=len(lines)*(tsize+3)+len(sl)*(ssize+3)
    cy=y+h/2-total/2+tsize
    for L in lines:
        a(f'<text x="{x+w/2}" y="{cy}" text-anchor="middle" font-size="{tsize}" font-weight="{700 if bold else 400}" fill="{tcol}">{esc(L)}</text>'); cy+=tsize+3
    for L in sl:
        a(f'<text x="{x+w/2}" y="{cy+1}" text-anchor="middle" font-size="{ssize}" fill="{GREY}">{esc(L)}</text>'); cy+=ssize+3
def badge(x,y,letter,col=NAVY):
    a(f'<rect x="{x}" y="{y}" width="26" height="26" rx="6" fill="{col}"/><text x="{x+13}" y="{y+18}" text-anchor="middle" font-size="15" font-weight="700" fill="#fff">{letter}</text>')
def step(x,y,n,col=ORANGE):
    a(f'<circle cx="{x}" cy="{y}" r="13" fill="{col}"/><text x="{x}" y="{y+5}" text-anchor="middle" font-size="14" font-weight="700" fill="#fff">{n}</text>')
def arrow(x1,y1,x2,y2,col=LINE,w=2,dash=None):
    d=f' stroke-dasharray="{dash}"' if dash else ''
    a(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}" marker-end="url(#ah)"{d}/>')
def text(x,y,t,size=13,col=GREY,anchor="start",weight=400):
    a(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" fill="{col}">{esc(t)}</text>')

a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Arial, Helvetica, sans-serif">')
a(f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker></defs>')
a(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')
text(30,44,"Databank · data platform architecture",26,NAVY,weight=700)
text(30,70,"Single cloud: AWS (eu-west-3 Paris) · Snowflake · dbt · GitHub Actions",15,GREY)

# column headers

srcs=[("A","Card terminals (TPE)","authorizations · JSON · simulated"),
      ("B","Core banking (OLTP)","clients, accounts, positions"),
      ("C","Market data · REAL","Nasdaq prices, FX (Marketplace)"),
      ("D","ECB Data Portal API · REAL","euro reference rates"),
      ("E","Banque de France","registry extracts · CSV files"),
      ("F","Mobile app","events · JSON lines")]
ing=[("1","Micro-batch streaming","producer.py · every 10 s"),
     ("2","CDC: streams + task","inside Snowflake · every 15 min"),
     ("3","Secure data share","zero-copy · no pipeline"),
     ("4","REST API pull, incremental","watermark + MERGE · daily cron"),
     ("5","PUT + Snowpipe","REST-triggered · daily"),
     ("6","PUT + COPY INTO","batch 3x/day · S3 auto-ingest opt.")]
bronze=[("RAW.TPE_AUTHORIZATIONS",None),
        ("CORE_BANKING.*",["→ RAW.CORE_BANKING_","CHANGES"]),
        ("SNOWFLAKE_CURATED_","DATA_FREE (shared DB)"),
        ("RAW.ECB_FX_RATES",None),
        ("STG_BDF → PIPE","RAW.BDF_REGISTRY"),
        ("STG_APP_EVENTS","RAW.APP_EVENTS")]
y0=112; hh=92; gap=14
# Snowflake boundary
a(f'<rect x="600" y="82" width="640" height="790" rx="16" fill="#F2FAFE" stroke="{BLUE}" stroke-width="2" stroke-dasharray="8 6"/>')
text(920,872+0,"",12)
a(f'<text x="1240" y="74" text-anchor="end" font-size="14" font-weight="700" fill="{DBLUE}">❄ Snowflake · AWS Paris</text>')
# GitHub actions boundary
a(f'<rect x="306" y="82" width="270" height="790" rx="16" fill="#FAFAFA" stroke="#C9D2DC" stroke-width="1.5" stroke-dasharray="4 5"/>')
a(f'<text x="576" y="74" text-anchor="end" font-size="13" font-weight="700" fill="{GREY}">GitHub Actions runners</text>')
for x,t in [(30,"SOURCES"),(620,"BRONZE"),(820,"SILVER"),(1030,"GOLD"),(1290,"CONSUMERS")]:
    text(x,100,t,13,GREY,weight=700)
for i in range(6):
    y=y0+i*(hh+gap); cy=y+hh/2
    box(30,y,250,hh,srcs[i][1],srcs[i][2],fill=("#FFF6EE" if srcs[i][1].endswith("REAL") else "#FFFFFF"))
    badge(38,y+8,srcs[i][0])
    ib_fill="#FFFFFF" if i not in (1,2) else "#EEF6FB"
    box(322,y+10,238,hh-20,ing[i][1],ing[i][2],fill=ib_fill,tsize=14,ssize=12)
    step(322,y+10,ing[i][0])
    arrow(280,cy,320,cy)
    arrow(560,cy,618,cy)
    t,s=bronze[i]
    box(618,y+12,178,hh-24,t,s,fill="#FFFFFF",stroke="#A9D8EE",tsize=12.5,ssize=12)
# note: B ingestion happens inside snowflake
# Silver
box(822,y0+12,188,300,["STAGING"],["11 views","1 per source table","typed, renamed, flagged"],fill="#FFFFFF",stroke="#A9D8EE")
box(822,y0+342,188,268,["INTERMEDIATE"],["dedup · SCD2 client history","FX: ECB API vs Marketplace","latest credit status"],fill="#FFFFFF",stroke="#A9D8EE")
for i in range(6):
    cy=y0+i*(hh+gap)+hh/2
    arrow(796,cy,820,cy)
# Gold
gold=[("finance",["fct_card_transactions*","dim_clients 🔒 · daily spend"]),
      ("serving (live)",["account_live_balance*","portfolio · app_* views 🔒"]),
      ("regulatory",["BdF daily report","AML alerts · credit watchlist"]),
      ("market",["FX rates daily","stock prices in €"]),
      ("digital + dq",["app engagement","rejected messages"])]
gy=y0+12; gh=110
for i,(t,s) in enumerate(gold):
    yy=gy+i*(gh+10)
    box(1036,yy,190,gh,t.upper(),s,fill="#FFFFFF",stroke="#A9D8EE",tsize=13,ssize=11.5)
    arrow(1010,yy+gh/2,1034,yy+gh/2)
# bottom band inside snowflake
band_y=742
chips=[("7","dbt build + tests","task DAG · every 15 min"),("8","Dynamic tables *","live path · 1-min lag"),("9","Governance",["RBAC · masking","row access · time travel"])]
for i,(n,t,s) in enumerate(chips):
    x=622+i*206
    box(x,band_y,194,108,t,s,fill="#FFFFFF",stroke=BLUE,tsize=14,ssize=11.5)
    step(x,band_y,n,DBLUE)
# consumers
cons=[("Mobile app","live balance & payments < 2 min","row access: own data only"),
      ("Dashboards","Streamlit in Snowflake","clients · advisors · ops"),
      ("Regulators","Banque de France report","AML alerts → Tracfin"),
      ("Analysts & data science","SQL on Gold · masked PII","FX / market analysis")]
cy0=150
for i,(t,s1,s2) in enumerate(cons):
    yy=cy0+i*175
    box(1290,yy,280,110,t,[s1,s2],fill="#FFFFFF",stroke="#C9D2DC",tsize=16,ssize=12.5)
    arrow(1226,yy+55,1288,yy+55)
# legend
text(30,905,"Real data: C, D  ·  Simulated: A, B, E, F  ·  * dynamic table  ·  🔒 masking / row access policy  ·  Warehouses: DATABANK_INGEST_WH (ingestion) / DATABANK_WH (transform) = workload isolation",13,GREY)
a('</svg>')
open('architecture.svg','w').write("\n".join(out))
print("ok")
