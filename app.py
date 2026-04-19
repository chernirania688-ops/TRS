import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

st.set_page_config(page_title="TRS – Meubles inc.", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#0d1117;color:#e6edf3;}
[data-testid="stSidebar"]{background:#161b22;border-right:1px solid #21262d;}
[data-testid="stSidebar"] .stMarkdown h1{font-family:'Rajdhani',sans-serif;font-size:1.5rem;font-weight:700;color:#58a6ff;letter-spacing:2px;}
.metric-card{background:linear-gradient(135deg,#161b22,#1c2128);border:1px solid #30363d;border-radius:12px;padding:16px 20px;position:relative;overflow:hidden;min-height:100px;}
.metric-card::before{content:'';position:absolute;top:0;left:0;width:3px;height:100%;border-radius:2px 0 0 2px;}
.metric-card.blue::before{background:#58a6ff;}.metric-card.green::before{background:#3fb950;}
.metric-card.orange::before{background:#d29922;}.metric-card.red::before{background:#f85149;}
.metric-card.purple::before{background:#a371f7;}.metric-card.teal::before{background:#39d353;}
.metric-label{font-size:0.66rem;color:#8b949e;text-transform:uppercase;letter-spacing:1.5px;font-weight:500;margin-bottom:5px;}
.metric-value{font-family:'Rajdhani',sans-serif;font-size:1.9rem;font-weight:700;line-height:1;}
.metric-sub{font-size:0.68rem;color:#8b949e;margin-top:4px;}
.sh{font-family:'Rajdhani',sans-serif;font-size:0.95rem;font-weight:600;color:#e6edf3;border-bottom:1px solid #21262d;padding-bottom:5px;margin-bottom:10px;letter-spacing:1px;}
.sol-card{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:12px 16px;margin-bottom:8px;}
.tranche-label{font-size:0.65rem;color:#484f58;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px;}
div[data-testid="stHorizontalBlock"]{gap:8px;}
.stSelectbox label,.stMultiSelect label{color:#8b949e!important;font-size:0.76rem!important;}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
DEPT_COLORS   = {"Découpe":"#58a6ff","Usinage":"#3fb950","Peinture":"#d29922"}
TEXT,MUTED,BG = "#e6edf3","#8b949e","#0d1117"
THRESHOLDS    = {"TRS":85,"TD":90,"TP":95,"TQ":98}
THRESH_COLORS = {"TRS":"#f85149","TD":"#f0883e","TP":"#d29922","TQ":"#3fb950"}
KPI_COLORS    = {"TRS":"#58a6ff","TD":"#3fb950","TQ":"#d29922","TP":"#a371f7"}
FILL_COLORS   = {"TRS":"rgba(88,166,255,0.08)","TD":"rgba(63,185,80,0.08)",
                 "TQ":"rgba(210,153,34,0.08)","TP":"rgba(163,113,247,0.08)"}
PROD_COLORS   = {"P1":"#58a6ff","P2":"#3fb950","P3":"#d29922","P4":"#a371f7"}
# Target values after applying actions (from images)
TARGETS = {"Découpe":{"TD":90,"TP":88,"TQ":98,"TRS":75},
           "Usinage": {"TD":92,"TP":88,"TQ":98,"TRS":79},
           "Peinture":{"TD":90,"TP":88,"TQ":95,"TRS":75}}
EXTRA_PROD = {"Découpe":380,"Usinage":520,"Peinture":290}

BL = dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
          font=dict(color=TEXT,family="Inter"),margin=dict(l=10,r=10,t=35,b=10),
          legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED,size=11)))

def ax(pct=False,title="",angle=0,dtick=None):
    d=dict(gridcolor="#21262d",zerolinecolor="#21262d",tickfont=dict(color=MUTED,size=10))
    if pct:   d["ticksuffix"]="%"
    if title: d["title"]=dict(text=title,font=dict(color=MUTED,size=10))
    if angle: d["tickangle"]=angle
    if dtick: d["dtick"]=dtick
    return d

def txax(vals):
    sv=sorted([int(v) for v in vals])
    return {**ax(),"tickmode":"array","tickvals":sv,"ticktext":[f"T{v}" for v in sv],
            "title":dict(text="Tranche",font=dict(color=MUTED,size=10))}

# ── Data ────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    base=os.path.dirname(os.path.abspath(__file__))
    xl=os.path.join(base,"Fichier_Données_Projet_TRS.xlsx")
    if not os.path.exists(xl): st.error(f"Fichier introuvable: {xl}"); st.stop()
    COLS=["Journée","Produit","Quantité","Rejet_Démarrage","Rejet_qualité","Panne",
          "Arrêts_mineurs","Nettoyage","Réglage_dérive","Inspection","Changement_outil",
          "Déplacement","Remplacement_préventif","Lubrification","Pause",
          "TO","TR","tfb","tn","tu","TD","TQ","TP","TRS"]
    dfs={}
    for s in ["Découpe","Usinage","Peinture"]:
        df=pd.read_excel(xl,sheet_name=s,header=0); df.columns=COLS
        df=df.dropna(subset=["Journée"])
        df["Journée"]=pd.to_numeric(df["Journée"],errors="coerce").astype("Int64")
        df=df.dropna(subset=["Journée"]); df["Journée"]=df["Journée"].astype(int)
        df["Tranche"]=((df["Journée"]-1)//25+1).clip(1,10)
        df["Jour_P"]=((df["Journée"]-1)%25)+1
        df["Département"]=s; dfs[s]=df.reset_index(drop=True)
    return dfs

dfs=load_data()
ALL_P=list(range(1,11))

# ── UI helpers ──────────────────────────────────────────────────────────────────
def kpi_card(label,value,color="blue",sub=""):
    cm={"blue":"#58a6ff","green":"#3fb950","orange":"#d29922","red":"#f85149","purple":"#a371f7","teal":"#39d353"}
    c=cm.get(color,"#58a6ff")
    return f'<div class="metric-card {color}"><div class="metric-label">{label}</div><div class="metric-value" style="color:{c}">{value}</div><div class="metric-sub">{sub}</div></div>'

def gauge(val,title,color="#58a6ff",thresh=85):
    fig=go.Figure(go.Indicator(mode="gauge+number",value=val,
        number={"suffix":"%","font":{"color":TEXT,"size":24,"family":"Rajdhani"}},
        title={"text":title,"font":{"color":MUTED,"size":11}},
        gauge={"axis":{"range":[0,100],"tickfont":{"color":MUTED,"size":8}},
               "bar":{"color":color},"bgcolor":"#161b22","borderwidth":0,
               "steps":[{"range":[0,60],"color":"#1c2128"},{"range":[60,thresh],"color":"#1f2820"},
                        {"range":[thresh,100],"color":"#1a2820"}],
               "threshold":{"line":{"color":"#f85149","width":2},"thickness":0.75,"value":thresh}}))
    fig.update_layout(height=185,**BL); return fig

def add_thresh(fig,kpis):
    for k in kpis:
        if k in THRESHOLDS:
            fig.add_hline(y=THRESHOLDS[k],line_dash="dash",line_color=THRESH_COLORS[k],line_width=1.4,
                          annotation_text=f"Seuil {k} {THRESHOLDS[k]}%",annotation_position="top right",
                          annotation_font=dict(color=THRESH_COLORS[k],size=8))
    return fig

def flag(v,t): return "✅" if v>=t else "⚠️"

def recap_table(df_in):
    rows=[]
    for t in sorted(df_in["Tranche"].unique()):
        s=df_in[df_in["Tranche"]==t]
        rows.append({"Tranche":f"T{int(t)}","Jours":f"{(int(t)-1)*25+1}–{int(t)*25}",
                     "TRS %":round(s["TRS"].mean()*100,2),"TD %":round(s["TD"].mean()*100,2),
                     "TQ %":round(s["TQ"].mean()*100,2),"TP %":round(s["TP"].mean()*100,2)})
    return pd.DataFrame(rows)

# ── Unified toggle filter ───────────────────────────────────────────────────────
def tranche_toggle(key_prefix, label="Sélection des Tranches"):
    st.markdown(f"<p class='tranche-label'>{label}</p>",unsafe_allow_html=True)
    for i in range(1,11):
        if f"{key_prefix}_{i}" not in st.session_state:
            st.session_state[f"{key_prefix}_{i}"]=True
    rc1,rc2,_=st.columns([1,1,8])
    with rc1:
        if st.button("✅ Tout",key=f"all_{key_prefix}",use_container_width=True):
            for i in range(1,11): st.session_state[f"{key_prefix}_{i}"]=True; st.rerun()
    with rc2:
        if st.button("❌ Aucun",key=f"none_{key_prefix}",use_container_width=True):
            for i in range(1,11): st.session_state[f"{key_prefix}_{i}"]=False; st.rerun()
    cols=st.columns(10)
    for i,col in enumerate(cols,1):
        with col:
            active=st.session_state[f"{key_prefix}_{i}"]
            if st.button(f"T{i}",key=f"tog_{key_prefix}_{i}",use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state[f"{key_prefix}_{i}"]=not active; st.rerun()
    return [i for i in range(1,11) if st.session_state[f"{key_prefix}_{i}"]]

# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🏭 TRS")
    st.markdown("<small>MEUBLES INC.</small>",unsafe_allow_html=True); st.markdown("---")
    PAGES={"📊 Dashboard Global":"global","🪚 Dép. Découpe":"decoupe",
           "⚙️ Dép. Usinage":"usinage","🎨 Dép. Peinture":"peinture",
           "🔍 Source des Pertes":"pertes","🏆 Dashboard Final":"final"}
    if "page" not in st.session_state: st.session_state.page="global"
    for label,key in PAGES.items():
        if st.button(label,key=f"nav_{key}",use_container_width=True):
            st.session_state.page=key; st.rerun()
    st.markdown("---")
    st.caption("📅 250 jours · 10 tranches × 25 j"); st.caption("📦 P1 P2 P3 P4 · 3 départements")
    st.markdown("---")
    st.markdown("<p style='color:#484f58;font-size:0.62rem;text-transform:uppercase;letter-spacing:2px'>Seuils TPM</p>",unsafe_allow_html=True)
    for k,v in THRESHOLDS.items():
        st.markdown(f"<span style='color:{THRESH_COLORS[k]};font-size:0.76rem'>● {k} ≥ {v}%</span>",unsafe_allow_html=True)

page=st.session_state.page

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL
# ═══════════════════════════════════════════════════════════════════════════════
if page=="global":
    st.markdown("<h2 style='font-family:Rajdhani;font-size:2rem;color:#e6edf3;letter-spacing:2px'>📊 DASHBOARD GLOBAL</h2>",unsafe_allow_html=True)
    st.markdown("<p style='color:#8b949e;font-size:0.78rem'>10 tranches × 25 jours · 3 départements · 4 produits</p>",unsafe_allow_html=True)

    sel_t=tranche_toggle("g")
    fc1,fc2=st.columns(2)
    with fc1: sel_prod=st.selectbox("Produit",["Tous","P1","P2","P3","P4"],key="g_prod")
    with fc2: sel_dept=st.selectbox("Département",["Tous"]+list(DEPT_COLORS.keys()),key="g_dept")
    if not sel_t: st.warning("Sélectionnez au moins une tranche."); st.stop()

    combined=pd.concat(dfs.values(),ignore_index=True)
    df=combined[combined["Tranche"].isin(sel_t)].copy()
    if sel_prod!="Tous": df=df[df["Produit"]==sel_prod]
    if sel_dept!="Tous": df=df[df["Département"]==sel_dept]
    if df.empty: st.warning("Aucune donnée."); st.stop()

    trs_m=df["TRS"].mean()*100; td_m=df["TD"].mean()*100
    tq_m=df["TQ"].mean()*100;   tp_m=df["TP"].mean()*100

    st.markdown("<br>",unsafe_allow_html=True)
    k1,k2,k3,k4=st.columns(4)
    with k1: st.markdown(kpi_card("TRS GLOBAL",f"{trs_m:.1f}%","blue" if trs_m>=85 else "red","Seuil ≥ 85%"),unsafe_allow_html=True)
    with k2: st.markdown(kpi_card("DISPONIBILITÉ TD",f"{td_m:.1f}%","green" if td_m>=90 else "red","Seuil ≥ 90%"),unsafe_allow_html=True)
    with k3: st.markdown(kpi_card("QUALITÉ TQ",f"{tq_m:.1f}%","teal" if tq_m>=98 else "red","Seuil ≥ 98%"),unsafe_allow_html=True)
    with k4: st.markdown(kpi_card("PERFORMANCE TP",f"{tp_m:.1f}%","orange" if tp_m>=95 else "red","Seuil ≥ 95%"),unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)

    # Courbe TRS/TD/TQ/TP par tranche (une seule, non redondante)
    st.markdown("<div class='sh'>Évolution TRS · TD · TQ · TP par Tranche</div>",unsafe_allow_html=True)
    by_t=df.groupby("Tranche")[["TRS","TD","TQ","TP"]].mean().reset_index().sort_values("Tranche")
    fig_ev=go.Figure()
    for kpi,c in KPI_COLORS.items():
        fig_ev.add_trace(go.Scatter(x=by_t["Tranche"],y=by_t[kpi]*100,name=kpi,
            line=dict(color=c,width=2.5),mode="lines+markers",marker=dict(size=7)))
    add_thresh(fig_ev,["TRS","TD","TQ","TP"])
    fig_ev.update_layout(height=310,**BL,xaxis=txax(by_t["Tranche"]),yaxis=ax(pct=True))
    fig_ev.update_yaxes(range=[0,110]); st.plotly_chart(fig_ev,use_container_width=True)

    # TRS journalier J1-250, 3 depts
    st.markdown("<div class='sh'>TRS Journalier J1→J250 — 3 Départements</div>",unsafe_allow_html=True)
    fig_jg=go.Figure()
    pal_bg=["rgba(88,166,255,0.04)","rgba(63,185,80,0.04)","rgba(210,153,34,0.04)",
            "rgba(163,113,247,0.04)","rgba(248,81,73,0.04)"]
    for t in range(1,11):
        j0=(t-1)*25+1; j1=t*25
        fig_jg.add_vrect(x0=j0,x1=j1,fillcolor=pal_bg[(t-1)%5],layer="below",line_width=0)
        fig_jg.add_annotation(x=(j0+j1)/2,y=107,text=f"T{t}",showarrow=False,font=dict(color=MUTED,size=8),yref="y")
    comb_j=pd.concat(dfs.values(),ignore_index=True)
    comb_j=comb_j[comb_j["Tranche"].isin(sel_t)]
    if sel_prod!="Tous": comb_j=comb_j[comb_j["Produit"]==sel_prod]
    for dept,dc in DEPT_COLORS.items():
        sub_d=comb_j[comb_j["Département"]==dept].groupby("Journée")["TRS"].mean().reset_index().sort_values("Journée")
        if sub_d.empty: continue
        fig_jg.add_trace(go.Scatter(x=sub_d["Journée"],y=sub_d["TRS"]*100,name=dept,
            line=dict(color=dc,width=1.5),mode="lines"))
    fig_jg.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.5,
                     annotation_text="Seuil TRS 85%",annotation_font=dict(color="#f85149",size=9))
    fig_jg.update_layout(height=270,**BL,xaxis=ax(title="Journée (1–250)"),yaxis=ax(pct=True))
    fig_jg.update_yaxes(range=[0,110]); st.plotly_chart(fig_jg,use_container_width=True)

    # TRS par dept × tranche  +  TRS par produit × tranche
    cl,cr=st.columns(2)
    with cl:
        st.markdown("<div class='sh'>TRS par Département × Tranche</div>",unsafe_allow_html=True)
        by_dt=df.groupby(["Tranche","Département"])["TRS"].mean().reset_index().sort_values("Tranche")
        fig_dt=go.Figure()
        for dept,c in DEPT_COLORS.items():
            sub=by_dt[by_dt["Département"]==dept]
            if sub.empty: continue
            fig_dt.add_trace(go.Scatter(x=sub["Tranche"],y=sub["TRS"]*100,name=dept,
                line=dict(color=c,width=2),mode="lines+markers",marker=dict(size=6)))
        fig_dt.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.2,
                          annotation_text="Seuil 85%",annotation_font=dict(color="#f85149",size=8))
        fig_dt.update_layout(height=260,**BL,xaxis=txax(by_dt["Tranche"]),yaxis=ax(pct=True))
        fig_dt.update_yaxes(range=[0,110]); st.plotly_chart(fig_dt,use_container_width=True)
    with cr:
        st.markdown("<div class='sh'>TRS par Produit × Tranche</div>",unsafe_allow_html=True)
        by_pt=df.groupby(["Tranche","Produit"])["TRS"].mean().reset_index().sort_values("Tranche")
        fig_pt=go.Figure()
        for p,c in PROD_COLORS.items():
            sub=by_pt[by_pt["Produit"]==p]
            if sub.empty: continue
            fig_pt.add_trace(go.Scatter(x=sub["Tranche"],y=sub["TRS"]*100,name=p,
                line=dict(color=c,width=2),mode="lines+markers",marker=dict(size=6)))
        fig_pt.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.2,
                          annotation_text="Seuil 85%",annotation_font=dict(color="#f85149",size=8))
        fig_pt.update_layout(height=260,**BL,xaxis=txax(by_pt["Tranche"]),yaxis=ax(pct=True))
        fig_pt.update_yaxes(range=[0,110]); st.plotly_chart(fig_pt,use_container_width=True)

    # Heatmap + tableau
    st.markdown("<div class='sh'>Heatmap TRS — Département × Tranche</div>",unsafe_allow_html=True)
    piv=(df.groupby(["Département","Tranche"])["TRS"].mean().unstack().sort_index()*100).round(1)
    piv=piv.reindex(sorted(piv.columns),axis=1)
    fig_hm=go.Figure(go.Heatmap(z=piv.values,x=[f"T{int(c)}" for c in sorted(piv.columns)],y=piv.index.tolist(),
        colorscale=[[0,"#1c2128"],[0.5,"#d29922"],[1,"#3fb950"]],zmin=0,zmax=100,
        text=piv.values.astype(str),texttemplate="%{text}%",textfont=dict(size=10,color="white"),
        colorbar=dict(ticksuffix="%",tickfont=dict(color=MUTED))))
    fig_hm.update_layout(height=190,**BL,xaxis=ax(),yaxis=ax())
    st.plotly_chart(fig_hm,use_container_width=True)

    st.markdown("<div class='sh'>📋 Tableau Récapitulatif par Tranche</div>",unsafe_allow_html=True)
    rdf=recap_table(df)
    st.dataframe(rdf,use_container_width=True,hide_index=True,
        column_config={"TRS %":st.column_config.ProgressColumn("TRS %",min_value=0,max_value=100,format="%.2f%%"),
                       "TD %": st.column_config.ProgressColumn("TD %", min_value=0,max_value=100,format="%.2f%%"),
                       "TQ %": st.column_config.ProgressColumn("TQ %", min_value=0,max_value=100,format="%.2f%%"),
                       "TP %": st.column_config.ProgressColumn("TP %", min_value=0,max_value=100,format="%.2f%%")})

# ═══════════════════════════════════════════════════════════════════════════════
# DÉPARTEMENT (générique)
# ═══════════════════════════════════════════════════════════════════════════════
def dept_page(dept_name):
    color=DEPT_COLORS[dept_name]
    icons={"Découpe":"🪚","Usinage":"⚙️","Peinture":"🎨"}
    st.markdown(f"<h2 style='font-family:Rajdhani;font-size:2rem;color:#e6edf3;letter-spacing:2px'>{icons[dept_name]} DÉPARTEMENT {dept_name.upper()}</h2>",unsafe_allow_html=True)
    st.markdown("<p style='color:#8b949e;font-size:0.78rem'>10 tranches × 25 jours — filtrage interactif — seuils TPM</p>",unsafe_allow_html=True)

    sel_t=tranche_toggle(f"d{dept_name[:2]}")
    sel_prod=st.selectbox("Produit",["Tous","P1","P2","P3","P4"],key=f"p_{dept_name}")
    if not sel_t: st.warning("Sélectionnez au moins une tranche."); return

    df=dfs[dept_name][dfs[dept_name]["Tranche"].isin(sel_t)].copy()
    if sel_prod!="Tous": df=df[df["Produit"]==sel_prod]
    if df.empty: st.warning("Aucune donnée."); return

    trs_m=df["TRS"].mean()*100; td_m=df["TD"].mean()*100
    tq_m=df["TQ"].mean()*100;   tp_m=df["TP"].mean()*100

    st.markdown("<br>",unsafe_allow_html=True)
    k1,k2,k3,k4=st.columns(4)
    with k1: st.markdown(kpi_card("TRS MOYEN",f"{trs_m:.1f}%","blue" if trs_m>=85 else "red",f"{flag(trs_m,85)} Seuil 85%"),unsafe_allow_html=True)
    with k2: st.markdown(kpi_card("TD DISPONIBILITÉ",f"{td_m:.1f}%","green" if td_m>=90 else "red",f"{flag(td_m,90)} Seuil 90%"),unsafe_allow_html=True)
    with k3: st.markdown(kpi_card("TQ QUALITÉ",f"{tq_m:.1f}%","teal" if tq_m>=98 else "red",f"{flag(tq_m,98)} Seuil 98%"),unsafe_allow_html=True)
    with k4: st.markdown(kpi_card("TP PERFORMANCE",f"{tp_m:.1f}%","orange" if tp_m>=95 else "red",f"{flag(tp_m,95)} Seuil 95%"),unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)

    # 4 jauges
    cg1,cg2,cg3,cg4=st.columns(4)
    with cg1: st.plotly_chart(gauge(trs_m,"TRS",color,85),use_container_width=True,key=f"g1_{dept_name}")
    with cg2: st.plotly_chart(gauge(td_m,"TD","#58a6ff",90),use_container_width=True,key=f"g2_{dept_name}")
    with cg3: st.plotly_chart(gauge(tq_m,"TQ","#3fb950",98),use_container_width=True,key=f"g3_{dept_name}")
    with cg4: st.plotly_chart(gauge(tp_m,"TP","#d29922",95),use_container_width=True,key=f"g4_{dept_name}")

    # Courbe combinée TRS·TD·TQ·TP par tranche
    st.markdown("<div class='sh'>Évolution TRS · TD · TQ · TP par Tranche (seuils TPM)</div>",unsafe_allow_html=True)
    by_t=df.groupby("Tranche")[["TRS","TD","TQ","TP"]].mean().reset_index().sort_values("Tranche")
    fig_t=go.Figure()
    for kpi,c in KPI_COLORS.items():
        fig_t.add_trace(go.Scatter(x=by_t["Tranche"],y=by_t[kpi]*100,name=kpi,
            line=dict(color=c,width=2.5),mode="lines+markers",marker=dict(size=7)))
    add_thresh(fig_t,["TRS","TD","TQ","TP"])
    fig_t.update_layout(height=300,**BL,xaxis=txax(by_t["Tranche"]),yaxis=ax(pct=True))
    fig_t.update_yaxes(range=[0,110]); st.plotly_chart(fig_t,use_container_width=True)

    # 4 courbes individuelles
    st.markdown("<div class='sh'>Évolution individuelle TRS · TD · TQ · TP</div>",unsafe_allow_html=True)
    cA,cB,cC,cD=st.columns(4)
    for col_,kpi,thresh in [(cA,"TRS",85),(cB,"TD",90),(cC,"TQ",98),(cD,"TP",95)]:
        with col_:
            fig_k=go.Figure()
            fig_k.add_trace(go.Scatter(x=by_t["Tranche"],y=by_t[kpi]*100,name=kpi,
                line=dict(color=KPI_COLORS[kpi],width=2),mode="lines+markers",
                marker=dict(size=6),fill="tozeroy",fillcolor=FILL_COLORS[kpi]))
            fig_k.add_hline(y=thresh,line_dash="dash",line_color=THRESH_COLORS[kpi],line_width=1.5,
                            annotation_text=f"Seuil {thresh}%",annotation_font=dict(color=THRESH_COLORS[kpi],size=8))
            fig_k.update_layout(height=200,**BL,xaxis=txax(by_t["Tranche"]),yaxis=ax(pct=True))
            fig_k.update_layout(title=dict(text=f"Évolution {kpi}",font=dict(color=TEXT,size=11)))
            fig_k.update_yaxes(range=[0,110])
            st.plotly_chart(fig_k,use_container_width=True,key=f"ind_{kpi}_{dept_name}")

    # TRS journalier par tranche
    st.markdown("<div class='sh'>TRS journalier J1–J25 par Tranche</div>",unsafe_allow_html=True)
    palette=["#58a6ff","#3fb950","#d29922","#a371f7","#f85149","#f0883e","#39d353","#79c0ff","#e3b341","#c77dff"]
    fig_j=go.Figure()
    for i,t in enumerate(sorted(sel_t)):
        sub=df[df["Tranche"]==t].sort_values("Jour_P")
        if sub.empty: continue
        sp=sub.groupby("Jour_P")["TRS"].mean().reset_index()
        fig_j.add_trace(go.Scatter(x=sp["Jour_P"],y=sp["TRS"]*100,name=f"T{t}",
            line=dict(color=palette[i%10],width=1.8),mode="lines+markers",marker=dict(size=4)))
    fig_j.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.5,
                    annotation_text="Seuil 85%",annotation_font=dict(color="#f85149",size=9))
    fig_j.update_layout(height=260,**BL,xaxis=ax(title="Jour (1–25)",dtick=1),yaxis=ax(pct=True))
    fig_j.update_yaxes(range=[0,110]); st.plotly_chart(fig_j,use_container_width=True)

    # ── Analyse par Produit ──────────────────────────────────────────────────
    st.markdown("<div class='sh'>Analyse par Produit — KPIs & Pertes</div>",unsafe_allow_html=True)
    df_all_t=dfs[dept_name][dfs[dept_name]["Tranche"].isin(sel_t)]
    by_p=df_all_t.groupby("Produit").agg(
        TRS=("TRS","mean"),TD=("TD","mean"),TQ=("TQ","mean"),TP=("TP","mean"),
        Quantité=("Quantité","sum"),Panne=("Panne","sum"),
        Arrêts_mineurs=("Arrêts_mineurs","sum"),
        Rejet_qualité=("Rejet_qualité","sum"),
        Rejet_Démarrage=("Rejet_Démarrage",lambda x:x.fillna(0).sum())
    ).reset_index()

    prods=[p for p in ["P1","P2","P3","P4"] if p in by_p["Produit"].values]

    # Grouped bar TRS·TD·TQ·TP par produit
    fig_pg=go.Figure()
    for kpi,c in KPI_COLORS.items():
        vals=[float(by_p[by_p["Produit"]==p][kpi].values[0])*100 if p in by_p["Produit"].values else 0 for p in prods]
        fig_pg.add_trace(go.Bar(name=kpi,x=prods,y=vals,marker_color=c,
            text=[f"{v:.1f}%" for v in vals],textposition="outside",textfont=dict(color=TEXT,size=9)))
    for kpi in ["TRS","TD","TQ","TP"]:
        fig_pg.add_hline(y=THRESHOLDS[kpi],line_dash="dash",line_color=THRESH_COLORS[kpi],line_width=1,
                         annotation_text=f"Seuil {kpi} {THRESHOLDS[kpi]}%",annotation_font=dict(color=THRESH_COLORS[kpi],size=8))
    fig_pg.update_layout(barmode="group",height=300,**BL,xaxis=ax(title="Produit"),yaxis=ax(pct=True))
    fig_pg.update_layout(title=dict(text="TRS · TD · TQ · TP par Produit",font=dict(color=TEXT,size=12)))
    fig_pg.update_yaxes(range=[0,115]); st.plotly_chart(fig_pg,use_container_width=True)

    cl_r,cr_r=st.columns(2)
    with cl_r:
        # Pertes par produit
        st.markdown("<div class='sh'>Pertes par Produit</div>",unsafe_allow_html=True)
        fig_pp=go.Figure()
        for col_n,lbl,c in [("Panne","Pannes (min)","#f85149"),("Arrêts_mineurs","Arrêts mineurs","#d29922"),
                              ("Rejet_qualité","Rejet qualité","#3fb950"),("Rejet_Démarrage","Rejet démarrage","#a371f7")]:
            vals=[float(by_p[by_p["Produit"]==p][col_n].values[0]) if p in by_p["Produit"].values else 0 for p in prods]
            fig_pp.add_trace(go.Bar(name=lbl,x=prods,y=vals,marker_color=c,
                text=[f"{int(v)}" for v in vals],textposition="outside",textfont=dict(color=TEXT,size=9)))
        fig_pp.update_layout(barmode="group",height=270,**BL,xaxis=ax(title="Produit"),yaxis=ax())
        fig_pp.update_layout(title=dict(text="Pertes cumulées par Produit",font=dict(color=TEXT,size=12)))
        st.plotly_chart(fig_pp,use_container_width=True)

    with cr_r:
        # Diagnostic
        st.markdown("<div class='sh'>🏆 Diagnostic — Produit le plus problématique</div>",unsafe_allow_html=True)
        scores=[]
        for p in prods:
            row=by_p[by_p["Produit"]==p]
            trs_p=float(row["TRS"].values[0])*100; td_p=float(row["TD"].values[0])*100
            tq_p=float(row["TQ"].values[0])*100;   tp_p=float(row["TP"].values[0])*100
            gap=max(0,85-trs_p)+max(0,90-td_p)+max(0,98-tq_p)+max(0,95-tp_p)
            scores.append({"Produit":p,"TRS %":round(trs_p,1),"TD %":round(td_p,1),
                           "TQ %":round(tq_p,1),"TP %":round(tp_p,1),
                           "Écart seuils":round(gap,1),
                           "Pannes (min)":int(float(row["Panne"].values[0])),
                           "Rejets":int(float(row["Rejet_qualité"].values[0])+float(row["Rejet_Démarrage"].values[0]))})
        sdf=pd.DataFrame(scores).sort_values("Écart seuils",ascending=False)
        if not sdf.empty:
            w=sdf.iloc[0]; b=sdf.iloc[-1]
            st.markdown(f"""<div style='background:#2d1515;border:1px solid #f85149;border-radius:8px;padding:10px 14px;margin-bottom:8px'>
<p style='color:#f85149;font-weight:700;margin:0 0 2px;font-family:Rajdhani;font-size:1.05rem'>⚠️ Plus problématique : {w["Produit"]}</p>
<p style='color:#c9d1d9;font-size:0.78rem;margin:0'>TRS={w["TRS %"]}% · TD={w["TD %"]}% · TQ={w["TQ %"]}% · TP={w["TP %"]}%</p>
<p style='color:#8b949e;font-size:0.75rem;margin:3px 0 0'>Écart total seuils : <span style='color:#f85149;font-weight:600'>{w["Écart seuils"]}%</span> · Pannes : {w["Pannes (min)"]} min · Rejets : {w["Rejets"]} pcs</p>
</div>""",unsafe_allow_html=True)
            st.markdown(f"""<div style='background:#0d1f0d;border:1px solid #3fb950;border-radius:8px;padding:10px 14px;margin-bottom:8px'>
<p style='color:#3fb950;font-weight:700;margin:0 0 2px;font-family:Rajdhani;font-size:1.05rem'>✅ Meilleur : {b["Produit"]}</p>
<p style='color:#c9d1d9;font-size:0.78rem;margin:0'>TRS={b["TRS %"]}% · TD={b["TD %"]}% · TQ={b["TQ %"]}% · TP={b["TP %"]}%</p>
</div>""",unsafe_allow_html=True)
        st.dataframe(sdf,use_container_width=True,hide_index=True,
            column_config={"TRS %":st.column_config.ProgressColumn("TRS %",min_value=0,max_value=100,format="%.1f%%"),
                           "TD %": st.column_config.ProgressColumn("TD %", min_value=0,max_value=100,format="%.1f%%"),
                           "TQ %": st.column_config.ProgressColumn("TQ %", min_value=0,max_value=100,format="%.1f%%"),
                           "TP %": st.column_config.ProgressColumn("TP %", min_value=0,max_value=100,format="%.1f%%")})

    # Tableau récap
    st.markdown("<div class='sh'>📋 Tableau par Tranche</div>",unsafe_allow_html=True)
    rdf=recap_table(df)
    st.dataframe(rdf,use_container_width=True,hide_index=True,
        column_config={"TRS %":st.column_config.ProgressColumn("TRS %",min_value=0,max_value=100,format="%.2f%%"),
                       "TD %": st.column_config.ProgressColumn("TD %", min_value=0,max_value=100,format="%.2f%%"),
                       "TQ %": st.column_config.ProgressColumn("TQ %", min_value=0,max_value=100,format="%.2f%%"),
                       "TP %": st.column_config.ProgressColumn("TP %", min_value=0,max_value=100,format="%.2f%%")})

if page=="decoupe":  dept_page("Découpe")
elif page=="usinage": dept_page("Usinage")
elif page=="peinture":dept_page("Peinture")

# ═══════════════════════════════════════════════════════════════════════════════
# SOURCE DES PERTES
# ═══════════════════════════════════════════════════════════════════════════════
elif page=="pertes":
    st.markdown("<h2 style='font-family:Rajdhani;font-size:2rem;color:#e6edf3;letter-spacing:2px'>🔍 SOURCE DES PERTES</h2>",unsafe_allow_html=True)
    st.markdown("<p style='color:#8b949e;font-size:0.78rem'>Analyse causale — 3 familles · 11 sources · démarche TPM</p>",unsafe_allow_html=True)

    with st.expander("📖 Fondement méthodologique — Démarche TPM",expanded=False):
        st.markdown("""<div style='color:#c9d1d9;font-size:0.82rem;line-height:1.9'>
<p>La démarche <strong>TPM (Total Productive Maintenance)</strong> structure l'analyse de l'inefficacité autour de l'identité :</p>
<p style='text-align:center;font-family:Rajdhani;font-size:1.3rem;color:#58a6ff;letter-spacing:2px'>TRS = TD × TQ × TP</p>
<p>Chaque facteur est dégradé par des <strong>familles de pertes</strong> identifiées dans les enregistrements de production.</p>
<hr style='border-color:#21262d'>
<p><span style='color:#f85149'>🔴</span> <strong>Pertes de DISPONIBILITÉ — réduisent TD</strong></p>
<table style='width:100%;border-collapse:collapse;font-size:0.8rem'>
<tr style='color:#8b949e;border-bottom:1px solid #21262d'><th align='left'>Source</th><th align='left'>Colonne</th><th align='left'>Impact</th></tr>
<tr style='border-bottom:1px solid #21262d'><td><strong>Pannes</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px'>Panne</code></td><td>Arrêt non planifié — cause principale de dégradation du TD</td></tr>
<tr><td><strong>Remplacement préventif</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px'>Remplacement_préventif</code></td><td>Intervention planifiée qui retire la machine du flux</td></tr>
</table>
<hr style='border-color:#21262d'>
<p><span style='color:#d29922'>🟡</span> <strong>Pertes de PERFORMANCE — réduisent TP</strong></p>
<table style='width:100%;border-collapse:collapse;font-size:0.8rem'>
<tr style='color:#8b949e;border-bottom:1px solid #21262d'><th align='left'>Source</th><th align='left'>Colonne</th><th align='left'>Impact</th></tr>
<tr style='border-bottom:1px solid #21262d'><td><strong>Arrêts mineurs</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px'>Arrêts_mineurs</code></td><td>Micro-arrêts non enregistrés comme pannes — freinent la cadence</td></tr>
<tr style='border-bottom:1px solid #21262d'><td><strong>Nettoyage</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px'>Nettoyage</code></td><td>Temps improductif récurrent — à réduire via 5S</td></tr>
<tr style='border-bottom:1px solid #21262d'><td><strong>Réglage dérive</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px'>Réglage_dérive</code></td><td>Correction de dérive — indicateur d'instabilité processus</td></tr>
<tr style='border-bottom:1px solid #21262d'><td><strong>Inspection</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px'>Inspection</code></td><td>Contrôle machine pendant production — perte de performance</td></tr>
<tr style='border-bottom:1px solid #21262d'><td><strong>Changement d'outil</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px'>Changement_outil</code></td><td>Levier SMED — réduire ces temps améliore directement TP</td></tr>
<tr style='border-bottom:1px solid #21262d'><td><strong>Déplacement / Manutention</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px'>Déplacement</code></td><td>Gaspillage de transport au sens Lean — flux non optimisés</td></tr>
<tr><td><strong>Lubrification</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px'>Lubrification</code></td><td>Maintenance de base à intégrer en maintenance autonome</td></tr>
</table>
<hr style='border-color:#21262d'>
<p><span style='color:#3fb950'>🟢</span> <strong>Pertes de QUALITÉ — réduisent TQ</strong></p>
<table style='width:100%;border-collapse:collapse;font-size:0.8rem'>
<tr style='color:#8b949e;border-bottom:1px solid #21262d'><th align='left'>Source</th><th align='left'>Colonne</th><th align='left'>Impact</th></tr>
<tr style='border-bottom:1px solid #21262d'><td><strong>Rejet démarrage</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px'>Rejet_Démarrage</code></td><td>Pièces non conformes en mise en régime — liées aux réglages</td></tr>
<tr><td><strong>Rejet qualité</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px'>Rejet_qualité</code></td><td>Défauts en cours de production — indicateur direct du TQ</td></tr>
</table></div>""",unsafe_allow_html=True)

    sel_t_p=tranche_toggle("p")
    fc1,fc2=st.columns(2)
    with fc1: sel_dept_p=st.selectbox("Département",["Tous"]+list(DEPT_COLORS.keys()),key="d_pertes")
    with fc2: sel_prod_p=st.selectbox("Produit",["Tous","P1","P2","P3","P4"],key="p_pertes")

    combined=pd.concat(dfs.values(),ignore_index=True)
    df_p=combined[combined["Tranche"].isin(sel_t_p)].copy()
    if sel_dept_p!="Tous": df_p=df_p[df_p["Département"]==sel_dept_p]
    if sel_prod_p!="Tous": df_p=df_p[df_p["Produit"]==sel_prod_p]
    if df_p.empty: st.warning("Aucune donnée."); st.stop()

    pdef={"Pannes":("Panne","TD","#f85149"),"Remplacement préventif":("Remplacement_préventif","TD","#c9362e"),
          "Arrêts mineurs":("Arrêts_mineurs","TP","#d29922"),"Nettoyage":("Nettoyage","TP","#e3b341"),
          "Réglage dérive":("Réglage_dérive","TP","#f0c040"),"Inspection":("Inspection","TP","#ffd166"),
          "Changement outil":("Changement_outil","TP","#ffb347"),"Déplacement":("Déplacement","TP","#f4845f"),
          "Lubrification":("Lubrification","TP","#c77dff"),
          "Rejet démarrage":("Rejet_Démarrage","TQ","#3fb950"),"Rejet qualité":("Rejet_qualité","TQ","#56d364")}
    pv={l:df_p[c].fillna(0).sum() for l,(c,_,_) in pdef.items()}

    st.markdown("<br>",unsafe_allow_html=True)
    pk1,pk2,pk3=st.columns(3)
    td_l=pv["Pannes"]+pv["Remplacement préventif"]
    tp_l=sum(pv[l] for l,(_,f,_) in pdef.items() if f=="TP")
    tq_l=pv["Rejet démarrage"]+pv["Rejet qualité"]
    with pk1: st.markdown(kpi_card("PERTES TD",f"{td_l:,.0f} min","red","Pannes + Maint. préventive"),unsafe_allow_html=True)
    with pk2: st.markdown(kpi_card("PERTES TP",f"{tp_l:,.0f} min","orange","7 sources"),unsafe_allow_html=True)
    with pk3: st.markdown(kpi_card("PERTES TQ",f"{tq_l:,.0f} pcs","teal","Rejets démarrage + qualité"),unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)

    cl2,cr2=st.columns(2)
    with cl2:
        st.markdown("<div class='sh'>Pareto des Pertes (Règle 80/20)</div>",unsafe_allow_html=True)
        sp=dict(sorted(pv.items(),key=lambda x:x[1],reverse=True))
        labels=list(sp.keys()); vals=list(sp.values())
        cumul=np.cumsum(vals)/max(sum(vals),1)*100
        bar_c=[pdef[l][2] for l in labels]
        fig_par=make_subplots(specs=[[{"secondary_y":True}]])
        fig_par.add_trace(go.Bar(x=labels,y=vals,name="Total",marker_color=bar_c,marker_line_color="rgba(0,0,0,0)"),secondary_y=False)
        fig_par.add_trace(go.Scatter(x=labels,y=cumul,name="Cumulé %",line=dict(color="#f0883e",width=2),mode="lines+markers"),secondary_y=True)
        fig_par.add_hline(y=80,line_dash="dot",line_color="#8b949e",line_width=1,
                          annotation_text="80%",annotation_font=dict(color=MUTED,size=9),secondary_y=True)
        fig_par.update_layout(height=330,**BL,xaxis=ax(angle=30),yaxis=ax(),
                              yaxis2=dict(ticksuffix="%",tickfont=dict(color=MUTED,size=10),gridcolor="#21262d"))
        st.plotly_chart(fig_par,use_container_width=True)
    with cr2:
        st.markdown("<div class='sh'>Répartition Treemap</div>",unsafe_allow_html=True)
        all_n=["TD","TP","TQ"]; all_par=["","",""]; all_v=[0,0,0]; all_c=["#f85149","#d29922","#3fb950"]
        for l,(c,fam,col) in pdef.items():
            all_n.append(l); all_par.append(fam); all_v.append(pv[l]); all_c.append(col)
        fig_tm=go.Figure(go.Treemap(labels=all_n,parents=all_par,values=all_v,
            marker=dict(colors=all_c,line=dict(color=BG,width=2)),
            textfont=dict(color="white",size=11),branchvalues="total"))
        fig_tm.update_layout(height=330,paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT,family="Inter"),margin=dict(l=0,r=0,t=5,b=0))
        st.plotly_chart(fig_tm,use_container_width=True)

    st.markdown("<div class='sh'>Évolution des Pertes par Tranche</div>",unsafe_allow_html=True)
    by_tp=df_p.groupby("Tranche").agg(
        Pannes=("Panne","sum"),Arrêts_mineurs=("Arrêts_mineurs","sum"),
        Rejet_qualité=("Rejet_qualité","sum"),
        Rejet_démarrage=("Rejet_Démarrage",lambda x:x.fillna(0).sum())
    ).reset_index().sort_values("Tranche")
    fig_ep=go.Figure()
    for col,c,n in [("Pannes","#f85149","Pannes"),("Arrêts_mineurs","#d29922","Arrêts mineurs"),
                     ("Rejet_qualité","#3fb950","Rejet qualité"),("Rejet_démarrage","#a371f7","Rejet démarrage")]:
        fig_ep.add_trace(go.Scatter(x=by_tp["Tranche"],y=by_tp[col],name=n,
            line=dict(color=c,width=2),mode="lines+markers",marker=dict(size=6)))
    fig_ep.update_layout(height=260,**BL,xaxis=txax(by_tp["Tranche"]),yaxis=ax(title="Total (min / pcs)"))
    st.plotly_chart(fig_ep,use_container_width=True)

    st.markdown("<div class='sh'>📋 Tableau par Tranche</div>",unsafe_allow_html=True)
    tbl_r=[]
    for t in sorted(df_p["Tranche"].unique()):
        s=df_p[df_p["Tranche"]==t]
        tbl_r.append({"Tranche":f"T{int(t)}","Jours":f"{(int(t)-1)*25+1}–{int(t)*25}",
                      "TRS %":round(s["TRS"].mean()*100,2),"TD %":round(s["TD"].mean()*100,2),
                      "TQ %":round(s["TQ"].mean()*100,2),"TP %":round(s["TP"].mean()*100,2),
                      "Pannes min":int(s["Panne"].sum()),"Rejet qualité":int(s["Rejet_qualité"].sum())})
    tdf=pd.DataFrame(tbl_r)
    st.dataframe(tdf,use_container_width=True,hide_index=True,
        column_config={"TRS %":st.column_config.ProgressColumn("TRS %",min_value=0,max_value=100,format="%.2f%%"),
                       "TD %": st.column_config.ProgressColumn("TD %", min_value=0,max_value=100,format="%.2f%%"),
                       "TQ %": st.column_config.ProgressColumn("TQ %", min_value=0,max_value=100,format="%.2f%%"),
                       "TP %": st.column_config.ProgressColumn("TP %", min_value=0,max_value=100,format="%.2f%%")})

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD FINAL — PLAN D'ACTION + GAINS
# ═══════════════════════════════════════════════════════════════════════════════
elif page=="final":
    st.markdown("<h2 style='font-family:Rajdhani;font-size:2rem;color:#e6edf3;letter-spacing:2px'>🏆 DASHBOARD FINAL — PLAN D'ACTION & GAINS</h2>",unsafe_allow_html=True)
    st.markdown("<p style='color:#8b949e;font-size:0.78rem'>Actions concrètes pour améliorer le TRS · Gains estimés après application · Production supplémentaire</p>",unsafe_allow_html=True)

    # Compute actuals from data
    combined=pd.concat(dfs.values(),ignore_index=True)
    actuals={}
    for dept in ["Découpe","Usinage","Peinture"]:
        d=dfs[dept]
        actuals[dept]={"TD":d["TD"].mean()*100,"TP":d["TP"].mean()*100,
                       "TQ":d["TQ"].mean()*100,"TRS":d["TRS"].mean()*100}

    # ── Graphiques Avant/Après par département (comme les images) ──────────────
    st.markdown("<div class='sh'>📊 Gains obtenus après application du plan d'action — par Département</div>",unsafe_allow_html=True)

    for dept,dc in DEPT_COLORS.items():
        act=actuals[dept]; tgt=TARGETS[dept]
        kpis=["TD","TP","TQ","TRS"]

        # Header annotations
        ann_cols=st.columns(4)
        for i,(kpi) in enumerate(kpis):
            a=act[kpi]; t=tgt[kpi]; delta=t-a
            with ann_cols[i]:
                st.markdown(f"""<div style='text-align:center;padding:4px'>
<div style='color:#8b949e;font-size:0.8rem'>{a:.1f}%</div>
<div style='color:{dc};font-size:0.9rem;font-weight:600'>↑ +{delta:.1f}pts</div>
<div style='color:#3fb950;font-size:1.1rem;font-weight:700;font-family:Rajdhani'>{t:.1f}%</div>
<div style='color:#8b949e;font-size:0.72rem'>{kpi}</div>
</div>""",unsafe_allow_html=True)

        # Grouped bar Avant / Après
        fig_ab=go.Figure()
        fig_ab.add_trace(go.Bar(name="Actuel",x=kpis,y=[act[k] for k in kpis],
            marker_color="#6e7681",marker_line_color="rgba(0,0,0,0)",
            text=[f"{act[k]:.1f}%" for k in kpis],textposition="outside",textfont=dict(color=TEXT,size=9)))
        fig_ab.add_trace(go.Bar(name="Objectif",x=kpis,y=[tgt[k] for k in kpis],
            marker_color=dc,marker_line_color="rgba(0,0,0,0)",
            text=[f"{tgt[k]:.1f}%" for k in kpis],textposition="outside",textfont=dict(color=TEXT,size=9)))
        # Dashed line connecting actuals
        fig_ab.add_trace(go.Scatter(x=kpis,y=[act[k] for k in kpis],mode="lines",
            line=dict(color="#f85149",width=1.5,dash="dash"),showlegend=False))
        fig_ab.update_layout(barmode="group",height=320,**BL,
            title=dict(text=f"Gains obtenus après 10 mois d'amélioration — {dept}",font=dict(color=MUTED,size=11)),
            xaxis=ax(),yaxis=ax(pct=True))
        fig_ab.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED,size=11)))
        fig_ab.update_yaxes(range=[0,115])
        st.plotly_chart(fig_ab,use_container_width=True)
        st.markdown("<hr style='border-color:#21262d;margin:8px 0'>",unsafe_allow_html=True)

    # ── Production supplémentaire estimée ──────────────────────────────────────
    st.markdown("<div class='sh'>Production supplémentaire estimée</div>",unsafe_allow_html=True)
    total_extra=sum(EXTRA_PROD.values())*250//len(EXTRA_PROD)
    ep1,ep2,ep3,ep4=st.columns(4)
    with ep1:
        st.markdown(f"""<div style='padding:10px 0'>
<div style='color:#8b949e;font-size:0.7rem;text-transform:uppercase'>Unités/jour gagnées</div>
<div style='color:#3fb950;font-family:Rajdhani;font-size:2rem;font-weight:700'>+{EXTRA_PROD["Découpe"]}</div>
<div style='color:#8b949e;font-size:0.72rem'>Découpe (est.)</div>
</div>""",unsafe_allow_html=True)
    with ep2:
        st.markdown(f"""<div style='padding:10px 0'>
<div style='color:#8b949e;font-size:0.7rem;text-transform:uppercase'>Unités/jour gagnées</div>
<div style='color:#3fb950;font-family:Rajdhani;font-size:2rem;font-weight:700'>+{EXTRA_PROD["Usinage"]}</div>
<div style='color:#8b949e;font-size:0.72rem'>Usinage (est.)</div>
</div>""",unsafe_allow_html=True)
    with ep3:
        st.markdown(f"""<div style='padding:10px 0'>
<div style='color:#8b949e;font-size:0.7rem;text-transform:uppercase'>Unités/jour gagnées</div>
<div style='color:#3fb950;font-family:Rajdhani;font-size:2rem;font-weight:700'>+{EXTRA_PROD["Peinture"]}</div>
<div style='color:#8b949e;font-size:0.72rem'>Peinture (est.)</div>
</div>""",unsafe_allow_html=True)
    with ep4:
        ann=min(EXTRA_PROD.values())*250
        st.markdown(f"""<div style='padding:10px 0'>
<div style='color:#8b949e;font-size:0.7rem;text-transform:uppercase'>Gain annuel total</div>
<div style='color:#3fb950;font-family:Rajdhani;font-size:2rem;font-weight:700'>+{ann:,}</div>
<div style='color:#8b949e;font-size:0.72rem'>unités sur 250 jours</div>
</div>""",unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#21262d;margin:16px 0'>",unsafe_allow_html=True)

    # ── Plan d'action détaillé ─────────────────────────────────────────────────
    st.markdown("<h3 style='font-family:Rajdhani;font-size:1.4rem;color:#58a6ff;letter-spacing:1px'>🛠️ Plan d'Action — Actions concrètes</h3>",unsafe_allow_html=True)

    def sol_block(titre,prio,desc,outil,bg="#161b22",bc="#21262d",pc="#8b949e"):
        return f"""<div class='sol-card' style='border-color:{bc}'>
<div style='display:flex;align-items:center;gap:8px;margin-bottom:6px'>
  <span style='font-weight:600;color:#e6edf3;font-size:0.87rem'>{titre}</span>
  <span style='background:{bg};color:{pc};border:1px solid {pc};border-radius:4px;padding:2px 7px;font-size:0.66rem;font-weight:600'>{prio}</span>
  <span style='background:#1c2128;color:#8b949e;border-radius:4px;padding:2px 7px;font-size:0.66rem'>{outil}</span>
</div>
<p style='color:#8b949e;font-size:0.78rem;margin:0;line-height:1.6'>{desc}</p>
</div>"""

    st.markdown("<div class='sh' style='color:#f85149'>🔴 Améliorer TD — Disponibilité (Seuil 90%)</div>",unsafe_allow_html=True)
    for t,p,d,o in [
        ("Maintenance Préventive Systématique","Priorité 1","Plan de maintenance basé sur les fréquences de pannes par département. Remplacement des composants avant défaillance selon les historiques MTBF. Objectif : -40% de pannes.","GMAO"),
        ("Analyse MTBF / MTTR","Priorité 1","Calculer le temps moyen entre pannes et le temps moyen de réparation par machine. Prioriser les équipements les plus critiques révélés par la dégradation progressive observée.","Analyse données"),
        ("Maintenance Autonome","Priorité 2","Former les opérateurs aux contrôles de base : nettoyage, lubrification, inspection visuelle. Réduire la dépendance au service maintenance pour les interventions simples.","Formation / 5S"),
        ("Standardisation redémarrage","Priorité 3","Fiches de redémarrage standardisées. Viser MTTR < 30 min pour les pannes courantes.","Standard Work"),
    ]:
        pc="#f85149" if "1" in p else "#d29922" if "2" in p else "#8b949e"
        st.markdown(sol_block(t,p,d,o,"#2d1515","#f85149",pc),unsafe_allow_html=True)

    st.markdown("<div class='sh' style='color:#d29922;margin-top:16px'>🟡 Améliorer TP — Performance (Seuil 95%)</div>",unsafe_allow_html=True)
    for t,p,d,o in [
        ("SMED — Réduction changements d'outils","Priorité 1","Convertir les opérations internes en externes. Objectif : -50% du temps de changement. Analyse par séquences vidéo recommandée.","SMED / Lean"),
        ("Élimination Arrêts Mineurs","Priorité 1","Analyser les causes racines des micro-arrêts (OPL). Capteurs de détection précoce pour éviter l'accumulation.","OPL / Capteurs"),
        ("5S et standardisation nettoyage","Priorité 2","Standardiser les durées et méthodes de nettoyage. Intégrer dans la maintenance autonome. Réduction visée : -30%.","5S / Standards"),
        ("Optimisation flux et implantation","Priorité 2","Spaghetti diagram pour les flux de déplacement/manutention. Réorganiser l'implantation, en particulier au département Peinture.","VSM / Layout"),
        ("SPC — Contrôle dérive machine","Priorité 3","Contrôle Statistique des Procédés pour détecter les dérives avant qu'elles nécessitent un réglage. Objectif : -60% des réglages curatifs.","SPC"),
    ]:
        pc="#f85149" if "1" in p else "#d29922" if "2" in p else "#8b949e"
        st.markdown(sol_block(t,p,d,o,"#2d2010","#d29922",pc),unsafe_allow_html=True)

    st.markdown("<div class='sh' style='color:#3fb950;margin-top:16px'>🟢 Améliorer TQ — Qualité (Seuil 98%)</div>",unsafe_allow_html=True)
    for t,p,d,o in [
        ("Poka-Yoke — Réduction rejets démarrage","Priorité 1","Standardiser les paramètres de démarrage par produit (P1–P4). Détrompeurs pour garantir la répétabilité. Objectif : 0 pièce rejetée après J+3.","Poka-Yoke"),
        ("AMDEC Processus","Priorité 1","Identifier les étapes critiques générant des rejets. Découpe et Peinture sont les plus concernées. Prioriser par IPR (Indice de Priorité de Risque).","AMDEC / RPN"),
        ("Autocontrôle opérateur","Priorité 2","Standards photo, critères visuels d'acceptation. Objectif : 100% détection au poste. Éviter la propagation des défauts entre départements.","Autocontrôle"),
        ("Capabilité processus Cp/Cpk","Priorité 2","Calculer Cp et Cpk pour les paramètres critiques. Un Cpk < 1,33 indique un processus non centré. Réglages basés sur les données SPC.","SPC / Capabilité"),
    ]:
        pc="#f85149" if "1" in p else "#d29922" if "2" in p else "#8b949e"
        st.markdown(sol_block(t,p,d,o,"#0d1f0d","#3fb950",pc),unsafe_allow_html=True)

    # ── Roadmap ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("<div class='sh'>📅 Roadmap d'Amélioration — Horizon 10 Tranches</div>",unsafe_allow_html=True)
    rm={
        "Action":["Maintenance Préventive","SMED Changements outils","5S Nettoyage",
                  "Poka-Yoke Démarrage","AMDEC Processus","SPC / Capabilité","Maintenance Autonome","Optimisation flux"],
        "Famille":["TD","TP","TP","TQ","TQ","TQ","TD","TP"],
        "Début":[1,1,2,1,2,3,3,4],"Fin":[4,3,10,4,5,10,10,10],
        "Impact":["+5%","+4%","+2%","+3%","+2%","+2%","+3%","+2%"],
    }
    rdf2=pd.DataFrame(rm)
    fam_c={"TD":"#f85149","TP":"#d29922","TQ":"#3fb950"}
    fig_rm=go.Figure()
    shown=set()
    for _,row in rdf2.iterrows():
        c=fam_c.get(row["Famille"],"#58a6ff")
        sl=row["Famille"] not in shown; shown.add(row["Famille"])
        fig_rm.add_trace(go.Bar(x=[row["Fin"]-row["Début"]+1],y=[row["Action"]],
            base=[row["Début"]-1],orientation="h",marker_color=c,marker_line_color="rgba(0,0,0,0)",
            name=row["Famille"],showlegend=sl,
            text=f" {row['Impact']}",textposition="inside",textfont=dict(color="white",size=10),
            hovertemplate=f"<b>{row['Action']}</b><br>T{row['Début']}→T{row['Fin']}<br>Impact: {row['Impact']}<extra></extra>"))
    fig_rm.update_layout(height=290,**BL,barmode="overlay",
                         xaxis=dict(**ax(),title=dict(text="Tranches",font=dict(color=MUTED)),
                                    tickmode="array",tickvals=list(range(1,11)),ticktext=[f"T{i}" for i in range(1,11)]),
                         yaxis=ax())
    fig_rm.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED,size=11),
                                     title=dict(text="Famille",font=dict(color=MUTED,size=10))))
    st.plotly_chart(fig_rm,use_container_width=True)

    st.markdown("""<div style='background:#161b22;border:1px solid #21262d;border-radius:8px;padding:14px 18px'>
<p style='color:#58a6ff;font-weight:600;margin:0 0 6px;font-family:Rajdhani;font-size:1rem'>💡 Gain TRS estimé — toutes actions appliquées</p>
<p style='color:#8b949e;font-size:0.8rem;margin:0;line-height:1.7'>
En appliquant l'ensemble des actions de priorité 1 et 2, le gain cumulé estimé est de
<span style='color:#3fb950;font-weight:600'>+15% à +45%</span> selon le département.
La Découpe bénéficiera le plus de la maintenance préventive (pannes fréquentes).
La Peinture progressera via le Poka-Yoke (rejets qualité élevés).
L'Usinage améliorera fortement son TP grâce au SMED (changements d'outils nombreux).
</p></div>""",unsafe_allow_html=True)
