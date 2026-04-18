import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="TRS Dashboard – Meubles inc.", layout="wide", initial_sidebar_state="expanded")

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#0d1117;color:#e6edf3;}
[data-testid="stSidebar"]{background:#161b22;border-right:1px solid #21262d;}
[data-testid="stSidebar"] .stMarkdown h1{font-family:'Rajdhani',sans-serif;font-size:1.6rem;font-weight:700;color:#58a6ff;letter-spacing:2px;}
.metric-card{background:linear-gradient(135deg,#161b22,#1c2128);border:1px solid #30363d;border-radius:12px;padding:18px 20px;position:relative;overflow:hidden;height:115px;}
.metric-card::before{content:'';position:absolute;top:0;left:0;width:3px;height:100%;border-radius:2px 0 0 2px;}
.metric-card.blue::before{background:#58a6ff;}.metric-card.green::before{background:#3fb950;}
.metric-card.orange::before{background:#d29922;}.metric-card.red::before{background:#f85149;}
.metric-card.purple::before{background:#a371f7;}.metric-card.teal::before{background:#39d353;}
.metric-label{font-size:0.68rem;color:#8b949e;text-transform:uppercase;letter-spacing:1.5px;font-weight:500;margin-bottom:6px;}
.metric-value{font-family:'Rajdhani',sans-serif;font-size:2rem;font-weight:700;line-height:1;}
.metric-sub{font-size:0.7rem;color:#8b949e;margin-top:5px;}
.section-header{font-family:'Rajdhani',sans-serif;font-size:1rem;font-weight:600;color:#e6edf3;border-bottom:1px solid #21262d;padding-bottom:6px;margin-bottom:12px;letter-spacing:1px;}
.solution-card{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:14px 18px;margin-bottom:10px;}
.solution-tag{display:inline-block;background:#1f3a5f;color:#58a6ff;border:1px solid #1f6feb;border-radius:4px;padding:2px 8px;font-size:0.7rem;font-weight:600;margin-right:6px;}
div[data-testid="stHorizontalBlock"]{gap:10px;}
.stSelectbox label,.stMultiSelect label{color:#8b949e!important;font-size:0.76rem!important;}
</style>
""", unsafe_allow_html=True)

# ─── Constants ───────────────────────────────────────────────────────────────
DEPT_COLORS   = {"Découpe":"#58a6ff","Usinage":"#3fb950","Peinture":"#d29922"}
BG,TEXT,MUTED = "#0d1117","#e6edf3","#8b949e"
THRESHOLDS    = {"TRS":85,"TD":90,"TP":95,"TQ":98}
THRESH_COLORS = {"TRS":"#f85149","TD":"#f0883e","TP":"#d29922","TQ":"#3fb950"}
KPI_COLORS    = {"TRS":"#58a6ff","TD":"#3fb950","TQ":"#d29922","TP":"#a371f7"}

BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT,family="Inter"),
    margin=dict(l=10,r=10,t=35,b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED,size=11)),
)

def ax(pct=False,title="",angle=0,dtick=None):
    """Build a clean axis dict — never duplicates tickfont."""
    d = dict(gridcolor="#21262d",zerolinecolor="#21262d",tickfont=dict(color=MUTED,size=10))
    if pct:      d["ticksuffix"]="%"
    if title:    d["title"]=dict(text=title,font=dict(color=MUTED,size=10))
    if angle:    d["tickangle"]=angle
    if dtick:    d["dtick"]=dtick
    return d

def tranche_xax(vals):
    sv = sorted([int(v) for v in vals])
    return {**ax(), "tickmode":"array","tickvals":sv,"ticktext":[f"T{v}" for v in sv],
            "title":dict(text="Tranche",font=dict(color=MUTED,size=10))}

# ─── Data ────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    base = os.path.dirname(os.path.abspath(__file__))
    xl   = os.path.join(base,"Fichier_Données_Projet_TRS.xlsx")
    if not os.path.exists(xl):
        st.error(f"Fichier Excel introuvable : {xl}"); st.stop()
    COLS=["Journée","Produit","Quantité","Rejet_Démarrage","Rejet_qualité","Panne",
          "Arrêts_mineurs","Nettoyage","Réglage_dérive","Inspection","Changement_outil",
          "Déplacement","Remplacement_préventif","Lubrification","Pause",
          "TO","TR","tfb","tn","tu","TD","TQ","TP","TRS"]
    dfs={}
    for sheet in ["Découpe","Usinage","Peinture"]:
        df=pd.read_excel(xl,sheet_name=sheet,header=0); df.columns=COLS
        df=df.dropna(subset=["Journée"])
        df["Journée"]=pd.to_numeric(df["Journée"],errors="coerce").astype("Int64")
        df=df.dropna(subset=["Journée"]); df["Journée"]=df["Journée"].astype(int)
        df["Tranche"]=((df["Journée"]-1)//25+1).clip(1,10)
        df["Jour_P"]=((df["Journée"]-1)%25)+1
        df["Département"]=sheet; dfs[sheet]=df.reset_index(drop=True)
    return dfs

dfs=load_data()
ALL_P=list(range(1,11))

# ─── UI helpers ──────────────────────────────────────────────────────────────
def kpi_card(label,value,color="blue",sub=""):
    cm={"blue":"#58a6ff","green":"#3fb950","orange":"#d29922","red":"#f85149","purple":"#a371f7","teal":"#39d353"}
    c=cm.get(color,"#58a6ff")
    return f'<div class="metric-card {color}"><div class="metric-label">{label}</div><div class="metric-value" style="color:{c}">{value}</div><div class="metric-sub">{sub}</div></div>'

def gauge(val,title,color="#58a6ff",thresh=85):
    fig=go.Figure(go.Indicator(
        mode="gauge+number",value=val,
        number={"suffix":"%","font":{"color":TEXT,"size":26,"family":"Rajdhani"}},
        title={"text":title,"font":{"color":MUTED,"size":11}},
        gauge={"axis":{"range":[0,100],"tickfont":{"color":MUTED,"size":8}},
               "bar":{"color":color},"bgcolor":"#161b22","borderwidth":0,
               "steps":[{"range":[0,60],"color":"#1c2128"},{"range":[60,thresh],"color":"#1f2820"},{"range":[thresh,100],"color":"#1a2820"}],
               "threshold":{"line":{"color":"#f85149","width":2},"thickness":0.75,"value":thresh}}))
    fig.update_layout(height=190,**BASE_LAYOUT); return fig

def add_thresholds(fig,kpis):
    for kpi in kpis:
        if kpi in THRESHOLDS:
            fig.add_hline(y=THRESHOLDS[kpi],line_dash="dash",line_color=THRESH_COLORS[kpi],line_width=1.5,
                          annotation_text=f"Seuil {kpi} {THRESHOLDS[kpi]}%",
                          annotation_position="top right",
                          annotation_font=dict(color=THRESH_COLORS[kpi],size=9))
    return fig

def flag(v,t): return "✅" if v>=t else "⚠️"

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🏭 TRS"); st.markdown("<small>MEUBLES INC.</small>",unsafe_allow_html=True); st.markdown("---")
    PAGES={"📊 Dashboard Global":"global","🪚 Dép. Découpe":"decoupe","⚙️ Dép. Usinage":"usinage",
           "🎨 Dép. Peinture":"peinture","🔍 Source des Pertes":"pertes","🏆 Dashboard Final":"final"}
    if "page" not in st.session_state: st.session_state.page="global"
    for label,key in PAGES.items():
        if st.button(label,key=f"nav_{key}",use_container_width=True):
            st.session_state.page=key; st.rerun()
    st.markdown("---"); st.caption("📅 250 jours · 10 tranches × 25 j"); st.caption("📦 P1 P2 P3 P4 · 3 départements")
    st.markdown("---")
    st.markdown("<p style='color:#484f58;font-size:0.65rem;text-transform:uppercase;letter-spacing:2px'>Seuils TPM</p>",unsafe_allow_html=True)
    for k,v in THRESHOLDS.items():
        st.markdown(f"<span style='color:{THRESH_COLORS[k]};font-size:0.78rem'>● {k} ≥ {v}%</span>",unsafe_allow_html=True)

page=st.session_state.page

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL
# ═══════════════════════════════════════════════════════════════════════════════
if page=="global":
    st.markdown("<h2 style='font-family:Rajdhani;font-size:2rem;color:#e6edf3;letter-spacing:2px'>📊 DASHBOARD GLOBAL</h2>",unsafe_allow_html=True)
    st.markdown("<p style='color:#8b949e;font-size:0.78rem'>10 tranches × 25 jours · 3 départements · 4 produits</p>",unsafe_allow_html=True)

    fc1,fc2,fc3=st.columns([2,1,1])
    with fc1: sel_t=st.multiselect("Tranches",ALL_P,default=ALL_P,key="g_t",format_func=lambda x:f"Tranche {x}  (J{(x-1)*25+1}–J{x*25})")
    with fc2: sel_prod=st.selectbox("Produit",["Tous","P1","P2","P3","P4"],key="g_prod")
    with fc3: sel_dept=st.selectbox("Département",["Tous"]+list(DEPT_COLORS.keys()),key="g_dept")
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
    with k1: st.markdown(kpi_card("TRS GLOBAL",f"{trs_m:.1f}%","blue" if trs_m>=85 else "red",f"Seuil ≥ 85%"),unsafe_allow_html=True)
    with k2: st.markdown(kpi_card("DISPONIBILITÉ TD",f"{td_m:.1f}%","green" if td_m>=90 else "red","Seuil ≥ 90%"),unsafe_allow_html=True)
    with k3: st.markdown(kpi_card("QUALITÉ TQ",f"{tq_m:.1f}%","teal" if tq_m>=98 else "red","Seuil ≥ 98%"),unsafe_allow_html=True)
    with k4: st.markdown(kpi_card("PERFORMANCE TP",f"{tp_m:.1f}%","orange" if tp_m>=95 else "red","Seuil ≥ 95%"),unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)

    # ── Courbe TRS/TD/TQ/TP par tranche ──
    st.markdown("<div class='section-header'>Évolution TRS · TD · TQ · TP par Tranche</div>",unsafe_allow_html=True)
    by_t=df.groupby("Tranche")[["TRS","TD","TQ","TP"]].mean().reset_index().sort_values("Tranche")
    fig_ev=go.Figure()
    for kpi,c in KPI_COLORS.items():
        fig_ev.add_trace(go.Scatter(x=by_t["Tranche"],y=by_t[kpi]*100,name=kpi,
            line=dict(color=c,width=2.5),mode="lines+markers",marker=dict(size=7)))
    add_thresholds(fig_ev,["TRS","TD","TQ","TP"])
    fig_ev.update_layout(height=320,**BASE_LAYOUT,xaxis=tranche_xax(by_t["Tranche"]),yaxis=ax(pct=True,title="%"))
    fig_ev.update_yaxes(range=[0,110])
    st.plotly_chart(fig_ev,use_container_width=True)

    # ── Courbe TRS par journée — 3 départements superposés ──
    st.markdown("<div class='section-header'>Évolution TRS Journalier (J1 → J250) — 3 Départements</div>",unsafe_allow_html=True)
    fig_jg=go.Figure()
    pal_bg=["rgba(88,166,255,0.04)","rgba(63,185,80,0.04)","rgba(210,153,34,0.04)",
            "rgba(163,113,247,0.04)","rgba(248,81,73,0.04)"]
    for t in range(1,11):
        j0=(t-1)*25+1; j1=t*25
        fig_jg.add_vrect(x0=j0,x1=j1,fillcolor=pal_bg[(t-1)%5],layer="below",line_width=0)
        fig_jg.add_annotation(x=(j0+j1)/2,y=106,text=f"T{t}",showarrow=False,
                               font=dict(color=MUTED,size=8),yref="y")
    # One curve per department, filtered by current sel_t
    combined_jour=pd.concat(dfs.values(),ignore_index=True)
    combined_jour=combined_jour[combined_jour["Tranche"].isin(sel_t)]
    if sel_prod!="Tous": combined_jour=combined_jour[combined_jour["Produit"]==sel_prod]
    for dept,dc in DEPT_COLORS.items():
        sub_d=combined_jour[combined_jour["Département"]==dept].groupby("Journée")["TRS"].mean().reset_index().sort_values("Journée")
        if sub_d.empty: continue
        fig_jg.add_trace(go.Scatter(x=sub_d["Journée"],y=sub_d["TRS"]*100,name=dept,
            line=dict(color=dc,width=1.5),mode="lines"))
    fig_jg.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.5,
                     annotation_text="Seuil TRS 85%",annotation_font=dict(color="#f85149",size=9))
    fig_jg.update_layout(height=280,**BASE_LAYOUT,
                         xaxis=ax(title="Journée (1–250)"),
                         yaxis=ax(pct=True))
    fig_jg.update_yaxes(range=[0,110])
    st.plotly_chart(fig_jg,use_container_width=True)

    # ── 4 courbes séparées une par KPI ──
    st.markdown("<div class='section-header'>Courbes individuelles par KPI (avec seuil)</div>",unsafe_allow_html=True)
    cols4=st.columns(2)
    kpi_pairs=[("TRS","TD"),("TQ","TP")]
    for idx,(k1_,k2_) in enumerate(kpi_pairs):
        with cols4[idx]:
            fig_k=go.Figure()
            for kpi in [k1_,k2_]:
                fig_k.add_trace(go.Scatter(x=by_t["Tranche"],y=by_t[kpi]*100,name=kpi,
                    line=dict(color=KPI_COLORS[kpi],width=2),mode="lines+markers",marker=dict(size=6)))
            add_thresholds(fig_k,[k1_,k2_])
            fig_k.update_layout(height=250,**BASE_LAYOUT,xaxis=tranche_xax(by_t["Tranche"]),yaxis=ax(pct=True))
            fig_k.update_layout(title=dict(text=f"{k1_} & {k2_} par Tranche",font=dict(color=TEXT,size=11)))
            fig_k.update_yaxes(range=[0,110])
            st.plotly_chart(fig_k,use_container_width=True)

    # ── TRS par département + produit ──
    cl,cr=st.columns(2)
    with cl:
        st.markdown("<div class='section-header'>TRS par Département × Tranche</div>",unsafe_allow_html=True)
        by_dt=df.groupby(["Tranche","Département"])["TRS"].mean().reset_index().sort_values("Tranche")
        fig_dt=go.Figure()
        for dept,c in DEPT_COLORS.items():
            sub=by_dt[by_dt["Département"]==dept]
            if sub.empty: continue
            fig_dt.add_trace(go.Scatter(x=sub["Tranche"],y=sub["TRS"]*100,name=dept,
                line=dict(color=c,width=2),mode="lines+markers",marker=dict(size=6)))
        fig_dt.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.2,
                          annotation_text="Seuil 85%",annotation_font=dict(color="#f85149",size=8))
        fig_dt.update_layout(height=270,**BASE_LAYOUT,xaxis=tranche_xax(by_dt["Tranche"]),yaxis=ax(pct=True))
        fig_dt.update_yaxes(range=[0,110]); st.plotly_chart(fig_dt,use_container_width=True)
    with cr:
        st.markdown("<div class='section-header'>TRS par Produit × Tranche</div>",unsafe_allow_html=True)
        by_pt=df.groupby(["Tranche","Produit"])["TRS"].mean().reset_index().sort_values("Tranche")
        pc={"P1":"#58a6ff","P2":"#3fb950","P3":"#d29922","P4":"#a371f7"}
        fig_pt=go.Figure()
        for p,c in pc.items():
            sub=by_pt[by_pt["Produit"]==p]
            if sub.empty: continue
            fig_pt.add_trace(go.Scatter(x=sub["Tranche"],y=sub["TRS"]*100,name=p,
                line=dict(color=c,width=2),mode="lines+markers",marker=dict(size=6)))
        fig_pt.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.2,
                          annotation_text="Seuil 85%",annotation_font=dict(color="#f85149",size=8))
        fig_pt.update_layout(height=270,**BASE_LAYOUT,xaxis=tranche_xax(by_pt["Tranche"]),yaxis=ax(pct=True))
        fig_pt.update_yaxes(range=[0,110]); st.plotly_chart(fig_pt,use_container_width=True)

    # ── Heatmap ──
    st.markdown("<div class='section-header'>Heatmap TRS — Département × Tranche</div>",unsafe_allow_html=True)
    pivot_g=(df.groupby(["Département","Tranche"])["TRS"].mean().unstack().sort_index()*100).round(1)
    pivot_g=pivot_g.reindex(sorted(pivot_g.columns),axis=1)
    fig_hm=go.Figure(go.Heatmap(
        z=pivot_g.values,x=[f"T{int(c)}" for c in sorted(pivot_g.columns)],y=pivot_g.index.tolist(),
        colorscale=[[0,"#1c2128"],[0.5,"#d29922"],[1,"#3fb950"]],zmin=0,zmax=100,
        text=pivot_g.values.astype(str),texttemplate="%{text}%",
        textfont=dict(size=11,color="white"),colorbar=dict(ticksuffix="%",tickfont=dict(color=MUTED))))
    fig_hm.update_layout(height=200,**BASE_LAYOUT,xaxis=ax(),yaxis=ax())
    st.plotly_chart(fig_hm,use_container_width=True)

    # ── Tableau simple: Tranche Jours TRS TD TQ TP ──
    st.markdown("<div class='section-header'>📋 Tableau Récapitulatif par Tranche</div>",unsafe_allow_html=True)
    recap=[]
    for t in sorted(df["Tranche"].unique()):
        sub=df[df["Tranche"]==t]
        recap.append({"Tranche":f"T{int(t)}","Jours":f"{(int(t)-1)*25+1}–{int(t)*25}",
                      "TRS %":round(sub["TRS"].mean()*100,2),"TD %":round(sub["TD"].mean()*100,2),
                      "TQ %":round(sub["TQ"].mean()*100,2),"TP %":round(sub["TP"].mean()*100,2)})
    rec_df=pd.DataFrame(recap)
    st.dataframe(rec_df,use_container_width=True,hide_index=True,
                 column_config={
                     "TRS %":st.column_config.ProgressColumn("TRS %",min_value=0,max_value=100,format="%.2f%%"),
                     "TD %": st.column_config.ProgressColumn("TD %", min_value=0,max_value=100,format="%.2f%%"),
                     "TQ %": st.column_config.ProgressColumn("TQ %", min_value=0,max_value=100,format="%.2f%%"),
                     "TP %": st.column_config.ProgressColumn("TP %", min_value=0,max_value=100,format="%.2f%%"),
                 })

# ═══════════════════════════════════════════════════════════════════════════════
# DÉPARTEMENT (générique)
# ═══════════════════════════════════════════════════════════════════════════════
def dept_page(dept_name):
    color=DEPT_COLORS[dept_name]
    icons={"Découpe":"🪚","Usinage":"⚙️","Peinture":"🎨"}
    st.markdown(f"<h2 style=\'font-family:Rajdhani;font-size:2rem;color:#e6edf3;letter-spacing:2px\'>{icons[dept_name]} DÉPARTEMENT {dept_name.upper()}</h2>",unsafe_allow_html=True)
    st.markdown("<p style=\'color:#8b949e;font-size:0.78rem\'>10 tranches × 25 jours — filtrage interactif — seuils TPM</p>",unsafe_allow_html=True)

    # ── Filtre amélioré : boutons T1…T10 ──────────────────────────────────────
    st.markdown("<p style=\'color:#8b949e;font-size:0.74rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px\'>Sélection des Tranches</p>",unsafe_allow_html=True)
    btn_cols=st.columns(10)
    key_prefix=f"btn_{dept_name}"
    for i in range(1,11):
        k=f"{key_prefix}_{i}"
        if k not in st.session_state: st.session_state[k]=True
    sel_row=st.columns([1,1,8])
    with sel_row[0]:
        if st.button("✅ Tout",key=f"all_{dept_name}",use_container_width=True):
            for i in range(1,11): st.session_state[f"{key_prefix}_{i}"]=True; st.rerun()
    with sel_row[1]:
        if st.button("❌ Aucun",key=f"none_{dept_name}",use_container_width=True):
            for i in range(1,11): st.session_state[f"{key_prefix}_{i}"]=False; st.rerun()

    # Render T1–T10 toggle buttons
    btn_cols2=st.columns(10)
    for i,col in enumerate(btn_cols2,1):
        with col:
            active=st.session_state[f"{key_prefix}_{i}"]
            label=f"T{i}"
            if st.button(label,key=f"tog_{dept_name}_{i}",use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state[f"{key_prefix}_{i}"]=not active; st.rerun()

    sel_t=[i for i in range(1,11) if st.session_state[f"{key_prefix}_{i}"]]

    # Produit filter
    sel_prod=st.selectbox("Produit",["Tous","P1","P2","P3","P4"],key=f"p_{dept_name}")

    if not sel_t:
        st.warning("Sélectionnez au moins une tranche."); return

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

    # ── Courbe TRS·TD·TQ·TP par tranche ──────────────────────────────────────
    st.markdown("<div class=\'section-header\'>Évolution TRS · TD · TQ · TP par Tranche (seuils TPM)</div>",unsafe_allow_html=True)
    by_t=df.groupby("Tranche")[["TRS","TD","TQ","TP"]].mean().reset_index().sort_values("Tranche")
    fig_t=go.Figure()
    for kpi,c in KPI_COLORS.items():
        fig_t.add_trace(go.Scatter(x=by_t["Tranche"],y=by_t[kpi]*100,name=kpi,
            line=dict(color=c,width=2.5),mode="lines+markers",marker=dict(size=7)))
    add_thresholds(fig_t,["TRS","TD","TQ","TP"])
    fig_t.update_layout(height=320,**BASE_LAYOUT,xaxis=tranche_xax(by_t["Tranche"]),yaxis=ax(pct=True))
    fig_t.update_yaxes(range=[0,110]); st.plotly_chart(fig_t,use_container_width=True)

    # ── 4 courbes individuelles ────────────────────────────────────────────────
    st.markdown("<div class=\'section-header\'>Courbes individuelles TRS · TD · TQ · TP avec seuil</div>",unsafe_allow_html=True)
    fillcolors={"TRS":"rgba(88,166,255,0.07)","TD":"rgba(63,185,80,0.07)",
                "TQ":"rgba(210,153,34,0.07)","TP":"rgba(163,113,247,0.07)"}
    cA,cB,cC,cD=st.columns(4)
    for col_,kpi,thresh in [(cA,"TRS",85),(cB,"TD",90),(cC,"TQ",98),(cD,"TP",95)]:
        with col_:
            fig_k=go.Figure()
            fig_k.add_trace(go.Scatter(x=by_t["Tranche"],y=by_t[kpi]*100,name=kpi,
                line=dict(color=KPI_COLORS[kpi],width=2),mode="lines+markers",
                marker=dict(size=6),fill="tozeroy",fillcolor=fillcolors[kpi]))
            fig_k.add_hline(y=thresh,line_dash="dash",line_color=THRESH_COLORS[kpi],line_width=1.5,
                            annotation_text=f"Seuil {thresh}%",annotation_font=dict(color=THRESH_COLORS[kpi],size=8))
            fig_k.update_layout(height=210,**BASE_LAYOUT,xaxis=tranche_xax(by_t["Tranche"]),yaxis=ax(pct=True))
            fig_k.update_layout(title=dict(text=f"Évolution {kpi}",font=dict(color=TEXT,size=11)))
            fig_k.update_yaxes(range=[0,110])
            st.plotly_chart(fig_k,use_container_width=True,key=f"ind_{kpi}_{dept_name}")

    # ── TRS journalier par tranche ─────────────────────────────────────────────
    st.markdown("<div class=\'section-header\'>TRS journalier dans chaque Tranche (J1–J25)</div>",unsafe_allow_html=True)
    palette=["#58a6ff","#3fb950","#d29922","#a371f7","#f85149","#f0883e","#39d353","#79c0ff","#e3b341","#c77dff"]
    fig_j=go.Figure()
    for i,t in enumerate(sorted(sel_t)):
        sub=df[df["Tranche"]==t].sort_values("Jour_P")
        if sub.empty: continue
        sub_p=sub.groupby("Jour_P")["TRS"].mean().reset_index()
        fig_j.add_trace(go.Scatter(x=sub_p["Jour_P"],y=sub_p["TRS"]*100,name=f"T{t}",
            line=dict(color=palette[i%10],width=1.8),mode="lines+markers",marker=dict(size=4)))
    fig_j.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.5,
                    annotation_text="Seuil 85%",annotation_font=dict(color="#f85149",size=9))
    fig_j.update_layout(height=270,**BASE_LAYOUT,
                        xaxis=ax(title="Jour dans la tranche (1–25)",dtick=1),yaxis=ax(pct=True))
    fig_j.update_yaxes(range=[0,110]); st.plotly_chart(fig_j,use_container_width=True)

    # ── Analyse par Produit : TRS TD TQ TP ────────────────────────────────────
    st.markdown("<div class=\'section-header\'>Analyse par Produit — TRS · TD · TQ · TP (quel produit est le plus problématique ?)</div>",unsafe_allow_html=True)
    by_p_full=dfs[dept_name][dfs[dept_name]["Tranche"].isin(sel_t)].groupby("Produit")[["TRS","TD","TQ","TP","Quantité",
              "Panne","Arrêts_mineurs","Rejet_qualité","Rejet_Démarrage"]].agg(
              {"TRS":"mean","TD":"mean","TQ":"mean","TP":"mean","Quantité":"sum",
               "Panne":"sum","Arrêts_mineurs":"sum","Rejet_qualité":"sum","Rejet_Démarrage":"sum"}).reset_index()

    prod_cols=["P1","P2","P3","P4"]
    pc_colors={"P1":"#58a6ff","P2":"#3fb950","P3":"#d29922","P4":"#a371f7"}

    # Grouped bar: TRS TD TQ TP par produit
    fig_pg=go.Figure()
    for kpi,c in KPI_COLORS.items():
        vals=[]
        for p in prod_cols:
            row=by_p_full[by_p_full["Produit"]==p]
            vals.append(float(row[kpi].values[0])*100 if len(row)>0 else 0)
        fig_pg.add_trace(go.Bar(name=kpi,x=prod_cols,y=vals,marker_color=c,
            text=[f"{v:.1f}%" for v in vals],textposition="outside",
            textfont=dict(color=TEXT,size=9)))
    for kpi in ["TRS","TD","TQ","TP"]:
        fig_pg.add_hline(y=THRESHOLDS[kpi],line_dash="dash",line_color=THRESH_COLORS[kpi],line_width=1,
                         annotation_text=f"Seuil {kpi} {THRESHOLDS[kpi]}%",
                         annotation_font=dict(color=THRESH_COLORS[kpi],size=8))
    fig_pg.update_layout(barmode="group",height=320,**BASE_LAYOUT,
                         xaxis=ax(title="Produit"),yaxis=ax(pct=True))
    fig_pg.update_layout(title=dict(text="KPIs TRS · TD · TQ · TP par Produit",font=dict(color=TEXT,size=12)))
    fig_pg.update_yaxes(range=[0,115])
    st.plotly_chart(fig_pg,use_container_width=True)

    # ── Radar produit ──────────────────────────────────────────────────────────
    cl_r,cr_r=st.columns(2)
    with cl_r:
        st.markdown("<div class=\'section-header\'>Radar — Profil qualité par Produit</div>",unsafe_allow_html=True)
        categories=["TRS","TD","TQ","TP"]
        fig_rad=go.Figure()
        for p in prod_cols:
            row=by_p_full[by_p_full["Produit"]==p]
            if row.empty: continue
            vals=[float(row[k].values[0])*100 for k in categories]+[float(row["TRS"].values[0])*100]
            fig_rad.add_trace(go.Scatterpolar(r=vals,theta=categories+[categories[0]],
                name=p,line=dict(color=pc_colors[p],width=2),fill="toself",
                fillcolor=pc_colors[p].replace("#","rgba(").replace("ff","255,0.06)")))
        # Add threshold circles
        for kpi,thresh in THRESHOLDS.items():
            pass  # plotly polar threshold lines are complex, skip
        fig_rad.update_layout(height=300,**BASE_LAYOUT,
            polar=dict(bgcolor="#161b22",
                radialaxis=dict(visible=True,range=[0,100],tickfont=dict(color=MUTED,size=8),
                                gridcolor="#21262d",ticksuffix="%"),
                angularaxis=dict(tickfont=dict(color=TEXT,size=11),gridcolor="#21262d")))
        st.plotly_chart(fig_rad,use_container_width=True)

    with cr_r:
        # ── Diagnostic produit le plus problématique ──
        st.markdown("<div class=\'section-header\'>🏆 Diagnostic — Produit le plus problématique</div>",unsafe_allow_html=True)
        scores=[]
        for p in prod_cols:
            row=by_p_full[by_p_full["Produit"]==p]
            if row.empty: continue
            trs_p=float(row["TRS"].values[0])*100
            td_p=float(row["TD"].values[0])*100
            tq_p=float(row["TQ"].values[0])*100
            tp_p=float(row["TP"].values[0])*100
            # Score = sum of gaps below threshold (higher = more problematic)
            gap=max(0,85-trs_p)+max(0,90-td_p)+max(0,98-tq_p)+max(0,95-tp_p)
            pannes=float(row["Panne"].values[0])
            rejets=float(row["Rejet_qualité"].values[0])+float(row["Rejet_Démarrage"].fillna(0).values[0])
            scores.append({"Produit":p,"TRS %":round(trs_p,1),"TD %":round(td_p,1),
                           "TQ %":round(tq_p,1),"TP %":round(tp_p,1),
                           "Écart seuils":round(gap,1),"Pannes (min)":int(pannes),"Rejets (pcs)":int(rejets)})
        scores_df=pd.DataFrame(scores).sort_values("Écart seuils",ascending=False)
        if not scores_df.empty:
            worst=scores_df.iloc[0]
            best=scores_df.iloc[-1]
            st.markdown(f"""<div style=\'background:#2d1515;border:1px solid #f85149;border-radius:8px;padding:12px 16px;margin-bottom:10px\'>
<p style=\'color:#f85149;font-weight:700;margin:0 0 4px;font-family:Rajdhani;font-size:1.1rem\'>⚠️ Produit le plus problématique : {worst["Produit"]}</p>
<p style=\'color:#c9d1d9;font-size:0.8rem;margin:0\'>TRS={worst["TRS %"]}% · TD={worst["TD %"]}% · TQ={worst["TQ %"]}% · TP={worst["TP %"]}%</p>
<p style=\'color:#8b949e;font-size:0.78rem;margin:4px 0 0\'>Écart total aux seuils TPM : <span style=\'color:#f85149;font-weight:600\'>{worst["Écart seuils"]}%</span> · Pannes : {worst["Pannes (min)"]} min · Rejets : {worst["Rejets (pcs)"]} pcs</p>
</div>""",unsafe_allow_html=True)
            st.markdown(f"""<div style=\'background:#0d1f0d;border:1px solid #3fb950;border-radius:8px;padding:12px 16px;margin-bottom:10px\'>
<p style=\'color:#3fb950;font-weight:700;margin:0 0 4px;font-family:Rajdhani;font-size:1.1rem\'>✅ Meilleur produit : {best["Produit"]}</p>
<p style=\'color:#c9d1d9;font-size:0.8rem;margin:0\'>TRS={best["TRS %"]}% · TD={best["TD %"]}% · TQ={best["TQ %"]}% · TP={best["TP %"]}%</p>
</div>""",unsafe_allow_html=True)
        st.dataframe(scores_df,use_container_width=True,hide_index=True,
                     column_config={
                         "TRS %":st.column_config.ProgressColumn("TRS %",min_value=0,max_value=100,format="%.1f%%"),
                         "TD %": st.column_config.ProgressColumn("TD %", min_value=0,max_value=100,format="%.1f%%"),
                         "TQ %": st.column_config.ProgressColumn("TQ %", min_value=0,max_value=100,format="%.1f%%"),
                         "TP %": st.column_config.ProgressColumn("TP %", min_value=0,max_value=100,format="%.1f%%"),
                     })

    # ── Pertes par Produit ─────────────────────────────────────────────────────
    st.markdown("<div class=\'section-header\'>Pertes par Produit — Pannes · Arrêts · Rejets</div>",unsafe_allow_html=True)
    fig_pp=go.Figure()
    perte_types=[("Panne","Pannes (min)","#f85149"),("Arrêts_mineurs","Arrêts mineurs (min)","#d29922"),
                  ("Rejet_qualité","Rejet qualité (pcs)","#3fb950"),("Rejet_Démarrage","Rejet démarrage (pcs)","#a371f7")]
    for col_name,label,c in perte_types:
        vals=[]
        for p in prod_cols:
            row=by_p_full[by_p_full["Produit"]==p]
            vals.append(float(row[col_name].fillna(0).values[0]) if len(row)>0 else 0)
        fig_pp.add_trace(go.Bar(name=label,x=prod_cols,y=vals,marker_color=c,
            text=[f"{int(v)}" for v in vals],textposition="outside",textfont=dict(color=TEXT,size=9)))
    fig_pp.update_layout(barmode="group",height=280,**BASE_LAYOUT,
                         xaxis=ax(title="Produit"),yaxis=ax(title="Cumul (min / pcs)"))
    fig_pp.update_layout(title=dict(text="Pertes cumulées par Produit (tranches sélectionnées)",font=dict(color=TEXT,size=12)))
    st.plotly_chart(fig_pp,use_container_width=True)

    # ── Tableau récap ──────────────────────────────────────────────────────────
    st.markdown("<div class=\'section-header\'>📋 Tableau Récapitulatif par Tranche</div>",unsafe_allow_html=True)
    recap2=[]
    for t in sorted(df["Tranche"].unique()):
        sub=df[df["Tranche"]==t]
        recap2.append({"Tranche":f"T{int(t)}","Jours":f"{(int(t)-1)*25+1}–{int(t)*25}",
                       "TRS %":round(sub["TRS"].mean()*100,2),"TD %":round(sub["TD"].mean()*100,2),
                       "TQ %":round(sub["TQ"].mean()*100,2),"TP %":round(sub["TP"].mean()*100,2)})
    rec2=pd.DataFrame(recap2)
    st.dataframe(rec2,use_container_width=True,hide_index=True,
                 column_config={
                     "TRS %":st.column_config.ProgressColumn("TRS %",min_value=0,max_value=100,format="%.2f%%"),
                     "TD %": st.column_config.ProgressColumn("TD %", min_value=0,max_value=100,format="%.2f%%"),
                     "TQ %": st.column_config.ProgressColumn("TQ %", min_value=0,max_value=100,format="%.2f%%"),
                     "TP %": st.column_config.ProgressColumn("TP %", min_value=0,max_value=100,format="%.2f%%"),
                 })

if page=="decoupe":  dept_page("Découpe")
elif page=="usinage": dept_page("Usinage")
elif page=="peinture":dept_page("Peinture")

# ═══════════════════════════════════════════════════════════════════════════════
# SOURCE DES PERTES
# ═══════════════════════════════════════════════════════════════════════════════
elif page=="pertes":
    st.markdown("<h2 style='font-family:Rajdhani;font-size:2rem;color:#e6edf3;letter-spacing:2px'>🔍 SOURCE DES PERTES</h2>",unsafe_allow_html=True)
    st.markdown("<p style='color:#8b949e;font-size:0.78rem'>Analyse causale selon la démarche TPM — 3 familles · 11 sources</p>",unsafe_allow_html=True)

    # ── Explication méthodologique ──
    with st.expander("📖 Fondement méthodologique — Démarche TPM et décomposition des pertes",expanded=True):
        st.markdown("""
<div style='color:#c9d1d9;font-size:0.83rem;line-height:1.9'>

<p>La démarche <strong>TPM (Total Productive Maintenance)</strong> structure l'analyse de l'inefficacité
autour de l'identité fondamentale :</p>

<p style='text-align:center;font-family:Rajdhani;font-size:1.3rem;color:#58a6ff;letter-spacing:2px'>
TRS = TD × TQ × TP
</p>

<p>Chaque facteur est dégradé par une ou plusieurs <strong>familles de pertes</strong> identifiées dans
les données de production enregistrées pour chaque département.
Les 11 sources présentées ci-dessous sont directement issues des colonnes de saisie quotidienne.</p>

<hr style='border-color:#21262d'>

<p><span style='color:#f85149;font-size:1rem'>🔴</span>
<strong>Pertes de DISPONIBILITÉ — réduisent TD</strong></p>
<p>Le taux de disponibilité compare le temps réel d'ouverture <em>(TR)</em> au temps d'ouverture théorique <em>(TO)</em>.
Tout événement qui immobilise la machine sans produire détériore TD.</p>

<table style='width:100%;border-collapse:collapse;font-size:0.82rem'>
<tr style='border-bottom:1px solid #21262d;color:#8b949e'><th align='left'>Source</th><th align='left'>Colonne</th><th align='left'>Impact</th></tr>
<tr style='border-bottom:1px solid #21262d'><td><strong>Pannes</strong></td><td><code style='background:#1c2128;padding:2px 6px;border-radius:3px'>Panne</code></td><td>Arrêt non planifié — cause principale de dégradation du TD dans les 3 départements</td></tr>
<tr><td><strong>Remplacement préventif</strong></td><td><code style='background:#1c2128;padding:2px 6px;border-radius:3px'>Remplacement_préventif</code></td><td>Intervention planifiée mais qui retire néanmoins la machine du flux de production</td></tr>
</table>

<hr style='border-color:#21262d'>

<p><span style='color:#d29922;font-size:1rem'>🟡</span>
<strong>Pertes de PERFORMANCE — réduisent TP</strong></p>
<p>Le taux de performance compare la cadence réelle à la cadence nominale.
Tout événement qui ralentit la production sans l'arrêter complètement dégrade TP.</p>

<table style='width:100%;border-collapse:collapse;font-size:0.82rem'>
<tr style='border-bottom:1px solid #21262d;color:#8b949e'><th align='left'>Source</th><th align='left'>Colonne</th><th align='left'>Impact</th></tr>
<tr style='border-bottom:1px solid #21262d'><td><strong>Arrêts mineurs</strong></td><td><code style='background:#1c2128;padding:2px 6px;border-radius:3px'>Arrêts_mineurs</code></td><td>Micro-arrêts de courte durée (&lt;5 min), non enregistrés comme pannes, mais qui freinent la cadence réelle</td></tr>
<tr style='border-bottom:1px solid #21262d'><td><strong>Nettoyage</strong></td><td><code style='background:#1c2128;padding:2px 6px;border-radius:3px'>Nettoyage</code></td><td>Temps improductif récurrent — à optimiser via la démarche 5S (standardisation des postes)</td></tr>
<tr style='border-bottom:1px solid #21262d'><td><strong>Réglage dérive</strong></td><td><code style='background:#1c2128;padding:2px 6px;border-radius:3px'>Réglage_dérive</code></td><td>Correction d'une dérive machine en cours de production — indicateur d'instabilité processus</td></tr>
<tr style='border-bottom:1px solid #21262d'><td><strong>Inspection</strong></td><td><code style='background:#1c2128;padding:2px 6px;border-radius:3px'>Inspection</code></td><td>Contrôle réalisé pendant le temps machine — à intégrer dans les standards opératoires</td></tr>
<tr style='border-bottom:1px solid #21262d'><td><strong>Changement d'outil</strong></td><td><code style='background:#1c2128;padding:2px 6px;border-radius:3px'>Changement_outil</code></td><td>Levier SMED (Single Minute Exchange of Die) : réduire ces temps améliore directement TP</td></tr>
<tr style='border-bottom:1px solid #21262d'><td><strong>Déplacement / Manutention</strong></td><td><code style='background:#1c2128;padding:2px 6px;border-radius:3px'>Déplacement</code></td><td>Gaspillage de type <em>transport</em> au sens Lean — signe de flux ou d'implantation non optimisés</td></tr>
<tr><td><strong>Lubrification</strong></td><td><code style='background:#1c2128;padding:2px 6px;border-radius:3px'>Lubrification</code></td><td>Maintenance de base à intégrer dans la maintenance autonome (pilier TPM) pour limiter son impact</td></tr>
</table>

<hr style='border-color:#21262d'>

<p><span style='color:#3fb950;font-size:1rem'>🟢</span>
<strong>Pertes de QUALITÉ — réduisent TQ</strong></p>
<p>Le taux de qualité rapporte les pièces conformes aux pièces totales fabriquées.
Tout défaut — qu'il soit détecté en démarrage ou en production — dégrade TQ.</p>

<table style='width:100%;border-collapse:collapse;font-size:0.82rem'>
<tr style='border-bottom:1px solid #21262d;color:#8b949e'><th align='left'>Source</th><th align='left'>Colonne</th><th align='left'>Impact</th></tr>
<tr style='border-bottom:1px solid #21262d'><td><strong>Rejet démarrage</strong></td><td><code style='background:#1c2128;padding:2px 6px;border-radius:3px'>Rejet_Démarrage</code></td><td>Pièces non conformes produites lors de la mise en régime — liées à la répétabilité des réglages</td></tr>
<tr><td><strong>Rejet qualité</strong></td><td><code style='background:#1c2128;padding:2px 6px;border-radius:3px'>Rejet_qualité</code></td><td>Défauts détectés en cours de production — indicateur direct de la capabilité processus</td></tr>
</table>
</div>
""",unsafe_allow_html=True)

    # Filters
    pc1,pc2,pc3=st.columns(3)
    with pc1: sel_t_p=st.multiselect("Tranches",ALL_P,default=ALL_P,key="t_pertes",format_func=lambda x:f"Tranche {x}")
    with pc2: sel_dept_p=st.selectbox("Département",["Tous"]+list(DEPT_COLORS.keys()),key="d_pertes")
    with pc3: sel_prod_p=st.selectbox("Produit",["Tous","P1","P2","P3","P4"],key="p_pertes")

    combined=pd.concat(dfs.values(),ignore_index=True)
    df_p=combined[combined["Tranche"].isin(sel_t_p)].copy()
    if sel_dept_p!="Tous": df_p=df_p[df_p["Département"]==sel_dept_p]
    if sel_prod_p!="Tous": df_p=df_p[df_p["Produit"]==sel_prod_p]
    if df_p.empty: st.warning("Aucune donnée."); st.stop()

    perte_def={
        "Pannes":                ("Panne",                  "TD","#f85149"),
        "Remplacement préventif":("Remplacement_préventif", "TD","#c9362e"),
        "Arrêts mineurs":        ("Arrêts_mineurs",         "TP","#d29922"),
        "Nettoyage":             ("Nettoyage",              "TP","#e3b341"),
        "Réglage dérive":        ("Réglage_dérive",         "TP","#f0c040"),
        "Inspection":            ("Inspection",             "TP","#ffd166"),
        "Changement outil":      ("Changement_outil",       "TP","#ffb347"),
        "Déplacement":           ("Déplacement",            "TP","#f4845f"),
        "Lubrification":         ("Lubrification",          "TP","#c77dff"),
        "Rejet démarrage":       ("Rejet_Démarrage",        "TQ","#3fb950"),
        "Rejet qualité":         ("Rejet_qualité",          "TQ","#56d364"),
    }
    pv={l:df_p[c].fillna(0).sum() for l,(c,_,_) in perte_def.items()}

    st.markdown("<br>",unsafe_allow_html=True)
    pk1,pk2,pk3=st.columns(3)
    td_l=pv["Pannes"]+pv["Remplacement préventif"]
    tp_l=sum(pv[l] for l,(_,f,_) in perte_def.items() if f=="TP")
    tq_l=pv["Rejet démarrage"]+pv["Rejet qualité"]
    with pk1: st.markdown(kpi_card("PERTES TD",f"{td_l:,.0f} min","red","Pannes + Maint. préventive"),unsafe_allow_html=True)
    with pk2: st.markdown(kpi_card("PERTES TP",f"{tp_l:,.0f} min","orange","7 sources de ralentissement"),unsafe_allow_html=True)
    with pk3: st.markdown(kpi_card("PERTES TQ",f"{tq_l:,.0f} pcs","teal","Rejets démarrage + qualité"),unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)

    cl2,cr2=st.columns(2)
    with cl2:
        st.markdown("<div class='section-header'>Pareto des Pertes (Règle 80/20)</div>",unsafe_allow_html=True)
        sp=dict(sorted(pv.items(),key=lambda x:x[1],reverse=True))
        labels=list(sp.keys()); vals=list(sp.values())
        cumul=np.cumsum(vals)/max(sum(vals),1)*100
        bar_c=[perte_def[l][2] for l in labels]
        fig_par=make_subplots(specs=[[{"secondary_y":True}]])
        fig_par.add_trace(go.Bar(x=labels,y=vals,name="Total",marker_color=bar_c,marker_line_color="rgba(0,0,0,0)"),secondary_y=False)
        fig_par.add_trace(go.Scatter(x=labels,y=cumul,name="Cumulé %",line=dict(color="#f0883e",width=2),mode="lines+markers"),secondary_y=True)
        fig_par.add_hline(y=80,line_dash="dot",line_color="#8b949e",line_width=1,
                          annotation_text="80%",annotation_font=dict(color=MUTED,size=9),secondary_y=True)
        fig_par.update_layout(height=340,**BASE_LAYOUT,
                              xaxis=ax(angle=30),
                              yaxis=ax(),
                              yaxis2=dict(ticksuffix="%",tickfont=dict(color=MUTED,size=10),gridcolor="#21262d"))
        st.plotly_chart(fig_par,use_container_width=True)
    with cr2:
        st.markdown("<div class='section-header'>Répartition Treemap</div>",unsafe_allow_html=True)
        all_n=["TD","TP","TQ"]; all_par=["","",""]; all_v=[0,0,0]; all_c=["#f85149","#d29922","#3fb950"]
        for l,(c,fam,col) in perte_def.items():
            all_n.append(l); all_par.append(fam); all_v.append(pv[l]); all_c.append(col)
        fig_tm=go.Figure(go.Treemap(labels=all_n,parents=all_par,values=all_v,
            marker=dict(colors=all_c,line=dict(color=BG,width=2)),
            textfont=dict(color="white",size=11),branchvalues="total"))
        fig_tm.update_layout(height=340,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#e6edf3",family="Inter"),legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color="#8b949e",size=11)),margin=dict(l=0,r=0,t=5,b=0))
        st.plotly_chart(fig_tm,use_container_width=True)

    # Évolution pertes par tranche
    st.markdown("<div class='section-header'>Évolution des Pertes Principales par Tranche</div>",unsafe_allow_html=True)
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
    fig_ep.update_layout(height=270,**BASE_LAYOUT,xaxis=tranche_xax(by_tp["Tranche"]),
                         yaxis=ax(title="Total (min / pièces)"))
    st.plotly_chart(fig_ep,use_container_width=True)

    # Tableau détaillé
    st.markdown("<div class='section-header'>📋 Tableau Récapitulatif par Tranche</div>",unsafe_allow_html=True)
    tbl_r=[]
    for t in sorted(df_p["Tranche"].unique()):
        sub=df_p[df_p["Tranche"]==t]
        tbl_r.append({"Tranche":f"T{int(t)}","Jours":f"{(int(t)-1)*25+1}–{int(t)*25}",
                      "TRS %":round(sub["TRS"].mean()*100,2),"TD %":round(sub["TD"].mean()*100,2),
                      "TQ %":round(sub["TQ"].mean()*100,2),"TP %":round(sub["TP"].mean()*100,2),
                      "Pannes min":int(sub["Panne"].sum()),"Rejet qualité":int(sub["Rejet_qualité"].sum())})
    tdf=pd.DataFrame(tbl_r)
    st.dataframe(tdf,use_container_width=True,hide_index=True,
                 column_config={
                     "TRS %":st.column_config.ProgressColumn("TRS %",min_value=0,max_value=100,format="%.2f%%"),
                     "TD %": st.column_config.ProgressColumn("TD %", min_value=0,max_value=100,format="%.2f%%"),
                     "TQ %": st.column_config.ProgressColumn("TQ %", min_value=0,max_value=100,format="%.2f%%"),
                     "TP %": st.column_config.ProgressColumn("TP %", min_value=0,max_value=100,format="%.2f%%"),
                 })

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD FINAL + SOLUTIONS
# ═══════════════════════════════════════════════════════════════════════════════
elif page=="final":
    st.markdown("<h2 style='font-family:Rajdhani;font-size:2rem;color:#e6edf3;letter-spacing:2px'>🏆 DASHBOARD FINAL — SYNTHÈSE & PLAN D'ACTION</h2>",unsafe_allow_html=True)
    st.markdown("<p style='color:#8b949e;font-size:0.78rem'>Synthèse TRS · Diagnostic · Solutions concrètes pour réduire les pertes</p>",unsafe_allow_html=True)

    ff1,ff2,ff3=st.columns([2,1,1])
    with ff1: sel_t_f=st.multiselect("Tranches",ALL_P,default=ALL_P,key="t_final",
                                      format_func=lambda x:f"Tranche {x}  (J{(x-1)*25+1}–J{x*25})")
    with ff2: sel_dept_f=st.selectbox("Département",list(DEPT_COLORS.keys()),key="d_final")
    with ff3: sel_prod_f=st.selectbox("Produit",["Tous","P1","P2","P3","P4"],key="p_final")
    if not sel_t_f: st.warning("Sélectionnez au moins une tranche."); st.stop()

    df_f=dfs[sel_dept_f][dfs[sel_dept_f]["Tranche"].isin(sel_t_f)].copy()
    if sel_prod_f!="Tous": df_f=df_f[df_f["Produit"]==sel_prod_f]
    if df_f.empty: st.warning("Aucune donnée."); st.stop()

    color_f=DEPT_COLORS[sel_dept_f]
    trs_f=df_f["TRS"].mean()*100; td_f=df_f["TD"].mean()*100
    tq_f=df_f["TQ"].mean()*100;   tp_f=df_f["TP"].mean()*100

    st.markdown("<br>",unsafe_allow_html=True)
    fk1,fk2,fk3,fk4=st.columns(4)
    with fk1: st.markdown(kpi_card("TRS MOYEN",f"{trs_f:.1f}%","blue" if trs_f>=85 else "red",f"{flag(trs_f,85)} Seuil 85%"),unsafe_allow_html=True)
    with fk2: st.markdown(kpi_card("DISPONIBILITÉ TD",f"{td_f:.1f}%","green" if td_f>=90 else "red",f"{flag(td_f,90)} Seuil 90%"),unsafe_allow_html=True)
    with fk3: st.markdown(kpi_card("QUALITÉ TQ",f"{tq_f:.1f}%","teal" if tq_f>=98 else "red",f"{flag(tq_f,98)} Seuil 98%"),unsafe_allow_html=True)
    with fk4: st.markdown(kpi_card("PERFORMANCE TP",f"{tp_f:.1f}%","orange" if tp_f>=95 else "red",f"{flag(tp_f,95)} Seuil 95%"),unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)

    jc1,jc2,jc3,jc4=st.columns(4)
    with jc1: st.plotly_chart(gauge(trs_f,"TRS",color_f,85),use_container_width=True,key="fg1")
    with jc2: st.plotly_chart(gauge(td_f,"TD","#58a6ff",90),use_container_width=True,key="fg2")
    with jc3: st.plotly_chart(gauge(tq_f,"TQ","#3fb950",98),use_container_width=True,key="fg3")
    with jc4: st.plotly_chart(gauge(tp_f,"TP","#d29922",95),use_container_width=True,key="fg4")

    # Courbe TRS/TD/TQ/TP par tranche
    st.markdown("<div class='section-header'>Évolution TRS · TD · TQ · TP par Tranche (seuils TPM)</div>",unsafe_allow_html=True)
    by_tf=df_f.groupby("Tranche")[["TRS","TD","TQ","TP"]].mean().reset_index().sort_values("Tranche")
    fig_ft=go.Figure()
    for kpi,c in KPI_COLORS.items():
        fig_ft.add_trace(go.Scatter(x=by_tf["Tranche"],y=by_tf[kpi]*100,name=kpi,
            line=dict(color=c,width=2.5),mode="lines+markers",marker=dict(size=7)))
    add_thresholds(fig_ft,["TRS","TD","TQ","TP"])
    fig_ft.update_layout(height=300,**BASE_LAYOUT,xaxis=tranche_xax(by_tf["Tranche"]),yaxis=ax(pct=True))
    fig_ft.update_yaxes(range=[0,110]); st.plotly_chart(fig_ft,use_container_width=True)

    # Heatmap + Waterfall
    cl_f,cr_f=st.columns(2)
    with cl_f:
        st.markdown("<div class='section-header'>Heatmap TRS — Produit × Tranche</div>",unsafe_allow_html=True)
        pivot_f=(dfs[sel_dept_f][dfs[sel_dept_f]["Tranche"].isin(sel_t_f)]
                 .groupby(["Produit","Tranche"])["TRS"].mean().unstack()*100).round(1)
        pivot_f=pivot_f.reindex(sorted(pivot_f.columns),axis=1)
        fig_hf=go.Figure(go.Heatmap(z=pivot_f.values,x=[f"T{int(c)}" for c in sorted(pivot_f.columns)],
            y=pivot_f.index.tolist(),colorscale=[[0,"#1c2128"],[0.5,"#d29922"],[1,"#3fb950"]],zmin=0,zmax=100,
            text=pivot_f.values.astype(str),texttemplate="%{text}%",
            textfont=dict(size=11,color="white"),colorbar=dict(ticksuffix="%",tickfont=dict(color=MUTED))))
        fig_hf.update_layout(height=260,**BASE_LAYOUT,xaxis=ax(),yaxis=ax())
        st.plotly_chart(fig_hf,use_container_width=True)
    with cr_f:
        st.markdown("<div class='section-header'>Waterfall — Décomposition du TRS</div>",unsafe_allow_html=True)
        loss_tq=td_f/100*(1-tq_f/100)*100; loss_tp=td_f/100*tq_f/100*(1-tp_f/100)*100
        fig_wf=go.Figure(go.Waterfall(
            x=["TD Disponibilité","− Perte Qualité","− Perte Performance","TRS Final"],
            measure=["absolute","relative","relative","total"],
            y=[td_f,-loss_tq,-loss_tp,trs_f],
            connector={"line":{"color":"#21262d"}},
            increasing={"marker":{"color":"#3fb950"}},decreasing={"marker":{"color":"#f85149"}},
            totals={"marker":{"color":color_f}},textfont=dict(color=TEXT),textposition="outside",
            text=[f"{td_f:.1f}%",f"−{loss_tq:.1f}%",f"−{loss_tp:.1f}%",f"{trs_f:.1f}%"]))
        fig_wf.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.5,
                         annotation_text="Seuil TRS 85%",annotation_font=dict(color="#f85149",size=9))
        fig_wf.update_layout(height=260,**BASE_LAYOUT,xaxis=ax(angle=10),yaxis=ax(pct=True))
        fig_wf.update_yaxes(range=[0,115]); st.plotly_chart(fig_wf,use_container_width=True)

    # Tableau final
    st.markdown("<div class='section-header'>📋 Tableau par Tranche</div>",unsafe_allow_html=True)
    recap_f=[]
    for t in sorted(df_f["Tranche"].unique()):
        sub=df_f[df_f["Tranche"]==t]
        recap_f.append({"Tranche":f"T{int(t)}","Jours":f"{(int(t)-1)*25+1}–{int(t)*25}",
                        "TRS %":round(sub["TRS"].mean()*100,2),"TD %":round(sub["TD"].mean()*100,2),
                        "TQ %":round(sub["TQ"].mean()*100,2),"TP %":round(sub["TP"].mean()*100,2)})
    rf=pd.DataFrame(recap_f)
    st.dataframe(rf,use_container_width=True,hide_index=True,
                 column_config={
                     "TRS %":st.column_config.ProgressColumn("TRS %",min_value=0,max_value=100,format="%.2f%%"),
                     "TD %": st.column_config.ProgressColumn("TD %", min_value=0,max_value=100,format="%.2f%%"),
                     "TQ %": st.column_config.ProgressColumn("TQ %", min_value=0,max_value=100,format="%.2f%%"),
                     "TP %": st.column_config.ProgressColumn("TP %", min_value=0,max_value=100,format="%.2f%%"),
                 })

    # ═══════════════════════════════════════════════════
    # PLAN D'ACTION — SOLUTIONS
    # ═══════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("<h3 style='font-family:Rajdhani;font-size:1.5rem;color:#58a6ff;letter-spacing:1px'>🛠️ PLAN D'ACTION — Solutions pour Améliorer le TRS</h3>",unsafe_allow_html=True)
    st.markdown("<p style='color:#8b949e;font-size:0.8rem'>Actions concrètes classées par famille de perte · Priorité basée sur l'analyse Pareto</p>",unsafe_allow_html=True)

    # Determine which KPIs are below threshold
    alerts=[]
    if td_f<90: alerts.append(("TD",td_f,90))
    if tq_f<98: alerts.append(("TQ",tq_f,98))
    if tp_f<95: alerts.append(("TP",tp_f,95))
    if trs_f<85: alerts.append(("TRS",trs_f,85))

    if alerts:
        st.markdown("<div style='background:#2d1515;border:1px solid #f85149;border-radius:8px;padding:12px 18px;margin-bottom:16px'>",unsafe_allow_html=True)
        st.markdown("<p style='color:#f85149;font-weight:600;margin:0 0 6px'>⚠️ KPIs en dessous du seuil TPM :</p>",unsafe_allow_html=True)
        for kpi,val,thresh in alerts:
            gap=thresh-val
            st.markdown(f"<p style='color:#c9d1d9;margin:2px 0;font-size:0.82rem'>● <strong>{kpi}</strong> = {val:.1f}%  →  écart de <span style='color:#f85149'>{gap:.1f}%</span> par rapport au seuil {thresh}%</p>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    # Solutions TD
    st.markdown("<div class='section-header' style='color:#f85149'>🔴 Actions pour améliorer TD (Disponibilité) — Seuil 90%</div>",unsafe_allow_html=True)
    sol_td=[
        ("Maintenance Préventive Systématique","Priorité 1","Établir un plan de maintenance préventive basé sur les fréquences de pannes observées par département. Remplacer les composants avant défaillance selon les historiques. Objectif : réduire les pannes de 40%.","GMAO / Planning"),
        ("Analyse MTBF / MTTR","Priorité 1","Calculer le temps moyen entre pannes (MTBF) et le temps moyen de réparation (MTTR) pour chaque machine. Prioriser les équipements les plus critiques. Les données de pannes par tranche révèlent une dégradation progressive.","Analyse données"),
        ("Maintenance Autonome (Pilier TPM)","Priorité 2","Former les opérateurs aux contrôles de base : nettoyage, lubrification, inspection visuelle quotidienne. Réduire la dépendance au service maintenance pour les interventions simples.","Formation / 5S"),
        ("Standardisation des procédures de redémarrage","Priorité 3","Créer des fiches de redémarrage standardisées pour réduire le temps de remise en production après une panne. Viser un MTTR < 30 min pour les pannes courantes.","Standard Work"),
    ]
    for titre,priorite,desc,outil in sol_td:
        col_p="#f85149" if "1" in priorite else "#d29922" if "2" in priorite else "#8b949e"
        st.markdown(f"""<div class='solution-card'>
<div style='display:flex;align-items:center;gap:10px;margin-bottom:8px'>
  <span style='font-weight:600;color:#e6edf3;font-size:0.9rem'>{titre}</span>
  <span style='background:#2d1515;color:{col_p};border:1px solid {col_p};border-radius:4px;padding:2px 8px;font-size:0.68rem;font-weight:600'>{priorite}</span>
  <span style='background:#1c2128;color:#8b949e;border-radius:4px;padding:2px 8px;font-size:0.68rem'>{outil}</span>
</div>
<p style='color:#8b949e;font-size:0.8rem;margin:0;line-height:1.6'>{desc}</p>
</div>""",unsafe_allow_html=True)

    # Solutions TP
    st.markdown("<div class='section-header' style='color:#d29922;margin-top:20px'>🟡 Actions pour améliorer TP (Performance) — Seuil 95%</div>",unsafe_allow_html=True)
    sol_tp=[
        ("Démarche SMED — Réduction des changements d'outils","Priorité 1","Appliquer la méthode SMED (Single Minute Exchange of Die) pour convertir les opérations internes en opérations externes. Objectif : réduire les temps de changement d'outil de 50%. Analyse des séquences vidéo recommandée.","SMED / Lean"),
        ("Élimination des Arrêts Mineurs — OPL","Priorité 1","Analyser les causes racines des micro-arrêts par machine (One Point Lessons). Les arrêts mineurs représentent la 2ème source de perte TP. Mettre en place des capteurs de détection précoce.","OPL / Capteurs"),
        ("Démarche 5S et standardisation du nettoyage","Priorité 2","Standardiser les temps et méthodes de nettoyage pour les rendre prévisibles et réduire leur durée. Intégrer le nettoyage dans la maintenance autonome quotidienne. Réduction visée : 30% du temps de nettoyage.","5S / Standards"),
        ("Optimisation des flux et implantation","Priorité 2","Analyser les flux de déplacement/manutention (spaghetti diagram). Réorganiser l'implantation pour minimiser les distances parcourues. Le poste Peinture présente des pertes de déplacement particulièrement élevées.","VSM / Layout"),
        ("Réduction des dérives machine — SPC","Priorité 3","Mettre en place le Contrôle Statistique des Procédés (SPC) pour détecter les dérives avant qu'elles nécessitent un réglage. Réduire les réglages de dérive de 60% par anticipation.","SPC / Capabilité"),
    ]
    for titre,priorite,desc,outil in sol_tp:
        col_p="#f85149" if "1" in priorite else "#d29922" if "2" in priorite else "#8b949e"
        st.markdown(f"""<div class='solution-card'>
<div style='display:flex;align-items:center;gap:10px;margin-bottom:8px'>
  <span style='font-weight:600;color:#e6edf3;font-size:0.9rem'>{titre}</span>
  <span style='background:#2d2010;color:{col_p};border:1px solid {col_p};border-radius:4px;padding:2px 8px;font-size:0.68rem;font-weight:600'>{priorite}</span>
  <span style='background:#1c2128;color:#8b949e;border-radius:4px;padding:2px 8px;font-size:0.68rem'>{outil}</span>
</div>
<p style='color:#8b949e;font-size:0.8rem;margin:0;line-height:1.6'>{desc}</p>
</div>""",unsafe_allow_html=True)

    # Solutions TQ
    st.markdown("<div class='section-header' style='color:#3fb950;margin-top:20px'>🟢 Actions pour améliorer TQ (Qualité) — Seuil 98%</div>",unsafe_allow_html=True)
    sol_tq=[
        ("Réduction des rejets de démarrage — Poka-Yoke","Priorité 1","Standardiser les paramètres de démarrage par produit (P1–P4) via des fiches de réglage validées. Mettre en place des détrompeurs (Poka-Yoke) pour garantir la répétabilité. Objectif : 0 pièce rejetée après J+3 de démarrage.","Poka-Yoke / SMED"),
        ("Analyse des modes de défaut — AMDEC Processus","Priorité 1","Réaliser une AMDEC Processus pour identifier les étapes critiques générant des rejets qualité. La Découpe et la Peinture présentent les taux de rejet les plus élevés. Prioriser les actions correctives par indice de criticité (IPR).","AMDEC / RPN"),
        ("Autocontrôle et contrôle en cours de production","Priorité 2","Former les opérateurs à l'autocontrôle et définir des critères d'acceptation visuels clairs (standards photo). Réduire la propagation des défauts entre postes. Objectif : détecter 100% des défauts au poste.","Autocontrôle / SPC"),
        ("Capabilité processus — Cp et Cpk","Priorité 2","Calculer les indices de capabilité (Cp, Cpk) pour les paramètres critiques de chaque département. Un Cpk < 1,33 indique un processus non centré ou non capable. Réglages correctifs basés sur les données SPC.","SPC / Capabilité"),
    ]
    for titre,priorite,desc,outil in sol_tq:
        col_p="#f85149" if "1" in priorite else "#d29922" if "2" in priorite else "#8b949e"
        st.markdown(f"""<div class='solution-card'>
<div style='display:flex;align-items:center;gap:10px;margin-bottom:8px'>
  <span style='font-weight:600;color:#e6edf3;font-size:0.9rem'>{titre}</span>
  <span style='background:#0d1f0d;color:{col_p};border:1px solid {col_p};border-radius:4px;padding:2px 8px;font-size:0.68rem;font-weight:600'>{priorite}</span>
  <span style='background:#1c2128;color:#8b949e;border-radius:4px;padding:2px 8px;font-size:0.68rem'>{outil}</span>
</div>
<p style='color:#8b949e;font-size:0.8rem;margin:0;line-height:1.6'>{desc}</p>
</div>""",unsafe_allow_html=True)

    # Roadmap visuelle
    st.markdown("---")
    st.markdown("<div class='section-header'>📅 Roadmap d'Amélioration — Horizon 6 Tranches</div>",unsafe_allow_html=True)
    roadmap_data={
        "Action": ["Maintenance Préventive","SMED Changements outils","5S Nettoyage","Poka-Yoke Démarrage",
                   "AMDEC Processus","SPC / Capabilité","Maintenance Autonome","Optimisation flux"],
        "Famille": ["TD","TP","TP","TQ","TQ","TQ","TD","TP"],
        "Début T":  [1,1,2,1,2,3,3,4],
        "Fin T":    [3,2,6,3,4,6,6,6],
        "Impact TRS estimé (%)":["+5%","+4%","+2%","+3%","+2%","+2%","+3%","+2%"],
    }
    rdf=pd.DataFrame(roadmap_data)
    fam_c={"TD":"#f85149","TP":"#d29922","TQ":"#3fb950"}
    fig_rm=go.Figure()
    for i,row in rdf.iterrows():
        c=fam_c.get(row["Famille"],"#58a6ff")
        fig_rm.add_trace(go.Bar(
            x=[row["Fin T"]-row["Début T"]+1],y=[row["Action"]],
            base=[row["Début T"]-1],orientation="h",
            marker_color=c,marker_line_color="rgba(0,0,0,0)",
            name=row["Famille"],showlegend=i<3,
            text=f" {row['Impact TRS estimé (%)']}",textposition="inside",
            textfont=dict(color="white",size=10),
            hovertemplate=f"<b>{row['Action']}</b><br>T{row['Début T']}→T{row['Fin T']}<br>Impact: {row['Impact TRS estimé (%)']}<extra></extra>"
        ))
    fig_rm.update_layout(height=300,**BASE_LAYOUT,barmode="overlay",
                         xaxis=dict(**ax(),title=dict(text="Tranches",font=dict(color=MUTED)),
                                    tickmode="array",tickvals=list(range(1,7)),ticktext=[f"T{i}" for i in range(1,7)]),
                         yaxis=ax())
    fig_rm.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED,size=11),
                                     title=dict(text="Famille",font=dict(color=MUTED,size=10))))
    st.plotly_chart(fig_rm,use_container_width=True)

    st.markdown("""<div style='background:#161b22;border:1px solid #21262d;border-radius:8px;padding:14px 18px;margin-top:8px'>
<p style='color:#58a6ff;font-weight:600;margin:0 0 8px;font-family:Rajdhani;font-size:1rem'>💡 Gain TRS estimé si toutes les actions sont menées</p>
<p style='color:#8b949e;font-size:0.82rem;margin:0;line-height:1.7'>
En appliquant l'ensemble des actions prioritaires (Priorité 1 et 2), le gain cumulé estimé sur le TRS est de
<span style='color:#3fb950;font-weight:600'>+15% à +23%</span> selon le département.
La Découpe, qui présente les pannes les plus fréquentes, bénéficiera le plus de la maintenance préventive.
La Peinture, avec les rejets qualité les plus élevés, verra son TQ s'améliorer significativement via le Poka-Yoke.
L'Usinage, pénalisé par les changements d'outils, progressera grâce au SMED.
</p>
</div>""",unsafe_allow_html=True)
