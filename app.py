import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

st.set_page_config(page_title="Approche TPM – Meubles inc.", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#0d1117;color:#e6edf3;}
[data-testid="stSidebar"]{background:#111318;border-right:1px solid #1e2430;}
[data-testid="stSidebar"] .stMarkdown h1{font-family:'Rajdhani';font-size:1.4rem;font-weight:700;color:#58a6ff;letter-spacing:3px;margin:0;}
[data-testid="stSidebar"] .stButton button{background:#161b22;border:1px solid #21262d;border-radius:8px;color:#8b949e;font-size:0.8rem;font-weight:500;padding:9px 14px;width:100%;transition:all 0.15s;margin:1px 0;}
[data-testid="stSidebar"] .stButton button:hover{background:#1f2937;color:#e6edf3;border-color:#30363d;}
.stButton button[kind="primary"]{background:linear-gradient(135deg,#1f3a5f,#1a3a6e)!important;color:#58a6ff!important;border:1px solid #1f6feb!important;font-weight:700!important;}
.stButton button[kind="secondary"]{background:#161b22!important;color:#484f58!important;border:1px solid #21262d!important;}
.kcard{background:linear-gradient(135deg,#161b22,#1c2128);border:1px solid #30363d;border-radius:12px;padding:16px 18px;position:relative;overflow:hidden;min-height:100px;box-shadow:0 2px 10px rgba(0,0,0,0.3);}
.kcard::before{content:'';position:absolute;top:0;left:0;width:4px;height:100%;border-radius:3px 0 0 3px;}
.kcard.blue::before{background:linear-gradient(180deg,#58a6ff,#1f6feb);}
.kcard.green::before{background:linear-gradient(180deg,#3fb950,#1a7f37);}
.kcard.orange::before{background:linear-gradient(180deg,#d29922,#b07d0a);}
.kcard.red::before{background:linear-gradient(180deg,#f85149,#b91c1c);}
.kcard.purple::before{background:linear-gradient(180deg,#a371f7,#7c3aed);}
.kcard.teal::before{background:linear-gradient(180deg,#39d353,#1a7f37);}
.kcard-label{font-size:0.62rem;color:#8b949e;text-transform:uppercase;letter-spacing:1.8px;font-weight:600;margin-bottom:5px;}
.kcard-val{font-family:'Rajdhani';font-size:2rem;font-weight:700;line-height:1;margin-bottom:3px;}
.kcard-sub{font-size:0.67rem;color:#8b949e;}
.sh{font-family:'Rajdhani';font-size:0.95rem;font-weight:700;color:#e6edf3;border-bottom:1px solid #21262d;padding-bottom:5px;margin-bottom:10px;letter-spacing:1.5px;display:flex;align-items:center;gap:8px;}
.sh::before{content:'';display:inline-block;width:3px;height:14px;border-radius:2px;background:linear-gradient(180deg,#58a6ff,#a371f7);flex-shrink:0;}
.infobox{background:#161b22;border-left:3px solid #f0883e;border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:10px;font-size:0.78rem;color:#c9d1d9;line-height:1.7;}
.tranche-label{font-size:0.62rem;color:#484f58;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px;}
.formula-box{background:#0d1f2d;border:1px solid #1f6feb;border-radius:10px;padding:14px 18px;margin:10px 0 16px;text-align:center;}
.cause-table{width:100%;border-collapse:collapse;font-size:0.78rem;margin-top:8px;}
.cause-table th{background:#161b22;color:#8b949e;padding:6px 10px;text-align:left;font-weight:600;font-size:0.68rem;text-transform:uppercase;letter-spacing:1px;}
.cause-table td{padding:7px 10px;border-bottom:1px solid #1e2430;color:#c9d1d9;vertical-align:top;}
.prog-bg{background:#1c2128;border-radius:4px;height:6px;margin:6px 0 4px;}
.prog-fill{height:6px;border-radius:4px;}
div[data-testid="stHorizontalBlock"]{gap:8px;}
.stSelectbox>div>div{background:#161b22!important;border-color:#21262d!important;}
.stSelectbox label{color:#8b949e!important;font-size:0.74rem!important;}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
DEPT_COLORS = {"Découpe":"#58a6ff","Usinage":"#3fb950","Peinture":"#d29922"}
DEPT_FILL   = {"Découpe":"rgba(88,166,255,0.12)","Usinage":"rgba(63,185,80,0.12)","Peinture":"rgba(210,153,34,0.12)"}
TEXT,MUTED,BG = "#e6edf3","#8b949e","#0d1117"
THRESHOLDS  = {"TRS":85,"TD":90,"TP":95,"TQ":98}
THRESH_C    = {"TRS":"#f85149","TD":"#f0883e","TP":"#d29922","TQ":"#3fb950"}
KPI_C       = {"TRS":"#58a6ff","TD":"#3fb950","TQ":"#d29922","TP":"#a371f7"}
FILL_C      = {"TRS":"rgba(88,166,255,0.08)","TD":"rgba(63,185,80,0.08)","TQ":"rgba(210,153,34,0.08)","TP":"rgba(163,113,247,0.08)"}
PROD_C      = {"P1":"#58a6ff","P2":"#3fb950","P3":"#d29922","P4":"#a371f7"}
TARGETS     = {"Découpe":{"TD":90,"TP":88,"TQ":98,"TRS":75},"Usinage":{"TD":92,"TP":88,"TQ":98,"TRS":79},"Peinture":{"TD":90,"TP":88,"TQ":95,"TRS":75}}
EXTRA_PROD  = {"Découpe":380,"Usinage":520,"Peinture":290}
# BL WITHOUT legend to avoid conflicts — legend added separately per chart
BL = dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color=TEXT,family="Inter"),margin=dict(l=10,r=10,t=35,b=10))
LEG = dict(bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED,size=11))  # reuse as legend=LEG

PDEF = {"Pannes":("Panne","TD","#f85149"),"Remplacement préventif":("Remplacement_préventif","TD","#c9362e"),
        "Arrêts mineurs":("Arrêts_mineurs","TP","#d29922"),"Nettoyage":("Nettoyage","TP","#e3b341"),
        "Réglage dérive":("Réglage_dérive","TP","#f0c040"),"Inspection":("Inspection","TP","#ffd166"),
        "Changement outil":("Changement_outil","TP","#ffb347"),"Déplacement":("Déplacement","TP","#f4845f"),
        "Lubrification":("Lubrification","TP","#c77dff"),"Rejet démarrage":("Rejet_Démarrage","TQ","#3fb950"),
        "Rejet qualité":("Rejet_qualité","TQ","#56d364")}

SOLUTIONS = {
    "Découpe":{"trs_act":"46.3%","trs_obj":"75%",
        "TD":{"act":63.9,"obj":90.0,"actions":["Mettre en place un plan de maintenance préventive hebdomadaire","Constituer un stock de pièces de rechange critiques (lames, courroies)","Réduire le temps de changement d'outil par SMED (objectif < 15 min)","Former les opérateurs à la détection précoce des pannes","Créer des fiches de lubrification et d'inspection quotidienne"]},
        "TP":{"act":75.4,"obj":88.0,"actions":["Réduire les déplacements inutiles par 5S et organisation du poste","Éliminer les micro-arrêts par une check-list de démarrage","Standardiser les réglages de dérive machine (fiche standard)","Optimiser le flux pièce entre scie et zone de stockage"]},
        "TQ":{"act":96.5,"obj":98.0,"actions":["Contrôle dimensionnel systématique des bandes en début de série","Réduire les rejets de démarrage par un protocole de lancement","Calibrage régulier de la scie à panneaux (tolérance ±1 mm)"]}},
    "Usinage":{"trs_act":"33.8%","trs_obj":"79%",
        "TD":{"act":84.3,"obj":92.0,"actions":["Planifier l'inspection machine chaque 50 heures de fonctionnement","Réduire le temps de nettoyage par aspiration intégrée","Anticiper les changements d'outil avant rupture"]},
        "TP":{"act":41.9,"obj":88.0,"actions":["Révision complète des paramètres de coupe des 2 broches — PRIORITÉ 1","Maintenance corrective immédiate des broches dégradées","Réduire les réglages de dérive (objectif < 10 min/réglage)","Équilibrer la charge entre les 2 broches simultanées","Installer un système de détection vibration (usure précoce)"]},
        "TQ":{"act":96.0,"obj":98.0,"actions":["Contrôle géométrique des trous et motifs en cours de série","Fiche de réglage standardisée par modèle (P1 à P4)","Réduire les rebuts de démarrage par essai à vide"]}},
    "Peinture":{"trs_act":"37.0%","trs_obj":"75%",
        "TD":{"act":73.3,"obj":90.0,"actions":["Maintenance préventive compresseur (filtres, huile, courroies)","Réduire les 115 min/j de déplacement par réorganisation du flux","Nettoyage planifié des pistolets (hors production)"]},
        "TP":{"act":60.4,"obj":88.0,"actions":["Révision du compresseur pour débit nominal constant","Réduire les arrêts mineurs par maintenance 1er niveau opérateurs","Standardiser le temps de séchage inter-couches"]},
        "TQ":{"act":82.7,"obj":95.0,"actions":["Contrôle épaisseur de peinture à chaque démarrage de couleur — PRIORITÉ 1","Formation opérateurs aux réglages pistolets (pression, débit)","Nettoyage pistolets entre chaque série (protocole strict)","Réduire les rejets qualité par un contrôle visuel en ligne","Calibrage compresseur pour pression homogène sur 5 pistolets"]}}
}

# ── Axis / chart helpers ───────────────────────────────────────────────────────
def ax(pct=False,title="",angle=0):
    d=dict(gridcolor="#1e2430",zerolinecolor="#1e2430",tickfont=dict(color=MUTED,size=10))
    if pct:   d["ticksuffix"]="%"
    if title: d["title"]=dict(text=title,font=dict(color=MUTED,size=10))
    if angle: d["tickangle"]=angle
    return d

def txax(vals):
    sv=sorted([int(v) for v in vals])
    return {**ax(),"tickmode":"array","tickvals":sv,"ticktext":[f"T{v}" for v in sv],"title":dict(text="Tranche",font=dict(color=MUTED,size=10))}

def bl(legend=True,**extra):
    """Return layout dict, optionally including legend."""
    d={**BL,**extra}
    if legend: d["legend"]=LEG
    return d

def add_thresh(fig,kpis):
    for k in kpis:
        if k in THRESHOLDS:
            fig.add_hline(y=THRESHOLDS[k],line_dash="dash",line_color=THRESH_C[k],line_width=1.4,
                          annotation_text=f"Seuil {k} {THRESHOLDS[k]}%",annotation_position="top right",
                          annotation_font=dict(color=THRESH_C[k],size=8))

# ── Data ───────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    base=os.path.dirname(os.path.abspath(__file__))
    xl=os.path.join(base,"Fichier_Données_Projet_TRS.xlsx")
    if not os.path.exists(xl): st.error(f"Fichier introuvable: {xl}"); st.stop()
    COLS=["Journée","Produit","Quantité","Rejet_Démarrage","Rejet_qualité","Panne","Arrêts_mineurs","Nettoyage","Réglage_dérive","Inspection","Changement_outil","Déplacement","Remplacement_préventif","Lubrification","Pause","TO","TR","tfb","tn","tu","TD","TQ","TP","TRS"]
    dfs={}
    for s in ["Découpe","Usinage","Peinture"]:
        df=pd.read_excel(xl,sheet_name=s,header=0); df.columns=COLS
        df=df.dropna(subset=["Journée"]); df["Journée"]=pd.to_numeric(df["Journée"],errors="coerce").astype("Int64")
        df=df.dropna(subset=["Journée"]); df["Journée"]=df["Journée"].astype(int)
        df["Tranche"]=((df["Journée"]-1)//25+1).clip(1,10); df["Département"]=s; dfs[s]=df.reset_index(drop=True)
    return dfs

dfs=load_data()
ALL_T=list(range(1,11))

# ── UI helpers ─────────────────────────────────────────────────────────────────
def kcard(label,value,color="blue",sub=""):
    cm={"blue":"#58a6ff","green":"#3fb950","orange":"#d29922","red":"#f85149","purple":"#a371f7","teal":"#39d353"}
    c=cm.get(color,"#58a6ff")
    return f'<div class="kcard {color}"><div class="kcard-label">{label}</div><div class="kcard-val" style="color:{c}">{value}</div><div class="kcard-sub">{sub}</div></div>'

def gauge(val,title,color="#58a6ff",thresh=85):
    fig=go.Figure(go.Indicator(mode="gauge+number",value=val,number={"suffix":"%","font":{"color":TEXT,"size":22,"family":"Rajdhani"}},
        title={"text":title,"font":{"color":MUTED,"size":10}},
        gauge={"axis":{"range":[0,100],"tickfont":{"color":MUTED,"size":8}},"bar":{"color":color},"bgcolor":"#161b22","borderwidth":0,
               "steps":[{"range":[0,60],"color":"#1c2128"},{"range":[60,thresh],"color":"#1e2820"},{"range":[thresh,100],"color":"#1a2c1a"}],
               "threshold":{"line":{"color":"#f85149","width":2},"thickness":0.75,"value":thresh}}))
    fig.update_layout(height=175,**bl(legend=False)); return fig

def flag(v,t): return "✅" if v>=t else "⚠️"

def pbar_cfg():
    return {"TRS %":st.column_config.ProgressColumn("TRS %",min_value=0,max_value=100,format="%.2f%%"),
            "TD %": st.column_config.ProgressColumn("TD %", min_value=0,max_value=100,format="%.2f%%"),
            "TQ %": st.column_config.ProgressColumn("TQ %", min_value=0,max_value=100,format="%.2f%%"),
            "TP %": st.column_config.ProgressColumn("TP %", min_value=0,max_value=100,format="%.2f%%")}

def recap_table(df_in):
    rows=[]
    for t in sorted(df_in["Tranche"].unique()):
        s=df_in[df_in["Tranche"]==t]
        rows.append({"Tranche":f"T{int(t)}","Jours":f"{(int(t)-1)*25+1}–{int(t)*25}","TRS %":round(s["TRS"].mean()*100,2),"TD %":round(s["TD"].mean()*100,2),"TQ %":round(s["TQ"].mean()*100,2),"TP %":round(s["TP"].mean()*100,2)})
    return pd.DataFrame(rows)

def tranche_toggle(key_prefix):
    st.markdown("<p class='tranche-label'>Sélection des Tranches</p>",unsafe_allow_html=True)
    for i in range(1,11):
        if f"{key_prefix}_{i}" not in st.session_state: st.session_state[f"{key_prefix}_{i}"]=True
    rc1,rc2,_=st.columns([1.2,1.2,9])
    with rc1:
        if st.button(" Tout",key=f"all_{key_prefix}",use_container_width=True):
            for i in range(1,11): st.session_state[f"{key_prefix}_{i}"]=True
            st.rerun()
    with rc2:
        if st.button(" Aucun",key=f"none_{key_prefix}",use_container_width=True):
            for i in range(1,11): st.session_state[f"{key_prefix}_{i}"]=False
            st.rerun()
    cols=st.columns(10)
    for i,col in enumerate(cols,1):
        with col:
            active=st.session_state[f"{key_prefix}_{i}"]
            if st.button(f"T{i}",key=f"tog_{key_prefix}_{i}",use_container_width=True,type="primary" if active else "secondary"):
                st.session_state[f"{key_prefix}_{i}"]=not active; st.rerun()
    return [i for i in range(1,11) if st.session_state[f"{key_prefix}_{i}"]]

def tab_bar(tabs, state_key):
    """Render tab buttons — NO title shown below (title suppressed)."""
    if state_key not in st.session_state: st.session_state[state_key]=tabs[0]
    cols=st.columns(len(tabs))
    for col,tab in zip(cols,tabs):
        with col:
            active=st.session_state[state_key]==tab
            if st.button(tab,key=f"__tab_{state_key}_{tab}",use_container_width=True,type="primary" if active else "secondary"):
                st.session_state[state_key]=tab; st.rerun()
    return st.session_state[state_key]

def page_header(title,subtitle):
    st.markdown(f"""<div style='margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid #21262d'>
<h1 style='font-family:Rajdhani;font-size:2rem;color:#e6edf3;letter-spacing:2px;margin:0;font-weight:700'> {title}</h1>
<p style='color:#8b949e;font-size:0.78rem;margin:4px 0 0'>{subtitle}</p></div>""",unsafe_allow_html=True)

def kpi_row(trs_m,td_m,tq_m,tp_m):
    k1,k2,k3,k4=st.columns(4)
    with k1: st.markdown(kcard("TRS",f"{trs_m:.1f}%","blue" if trs_m>=85 else "red",f"{flag(trs_m,85)} Seuil 85%"),unsafe_allow_html=True)
    with k2: st.markdown(kcard("TD — Disponibilité",f"{td_m:.1f}%","green" if td_m>=90 else "red",f"{flag(td_m,90)} Seuil 90%"),unsafe_allow_html=True)
    with k3: st.markdown(kcard("TQ — Qualité",f"{tq_m:.1f}%","teal" if tq_m>=98 else "red",f"{flag(tq_m,98)} Seuil 98%"),unsafe_allow_html=True)
    with k4: st.markdown(kcard("TP — Performance",f"{tp_m:.1f}%","orange" if tp_m>=95 else "red",f"{flag(tp_m,95)} Seuil 95%"),unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# Approche TPM")
    st.markdown("<p style='color:#484f58;font-size:0.68rem;letter-spacing:2px;margin-top:-4px'>MEUBLES INC.</p>",unsafe_allow_html=True)
    st.markdown("---")
    PAGES={" Dashboard Global":"global","  Dép. Découpe":"decoupe"," Dép. Usinage":"usinage","  Dép. Peinture":"peinture"," Source des Pertes":"pertes","  Dashboard Final":"final"}
    if "page" not in st.session_state: st.session_state.page="global"
    for label,key in PAGES.items():
        if st.session_state.page==key:
            st.markdown(f"<div style='background:linear-gradient(90deg,#1f3a5f,#1a2a4a);border:1px solid #1f6feb;border-radius:8px;padding:9px 14px;margin:1px 0;color:#58a6ff;font-size:0.8rem;font-weight:600'>{label}</div>",unsafe_allow_html=True)
        else:
            if st.button(label,key=f"nav_{key}",use_container_width=True): st.session_state.page=key; st.rerun()
    st.markdown("---")
    st.markdown("<p style='color:#484f58;font-size:0.6rem;text-transform:uppercase;letter-spacing:2px'>Seuils TPM</p>",unsafe_allow_html=True)
    for k,v in THRESHOLDS.items():
        st.markdown(f"<p style='color:{THRESH_C[k]};font-size:0.74rem;margin:2px 0'>● {k} ≥ {v}%</p>",unsafe_allow_html=True)

page=st.session_state.page

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL
# ══════════════════════════════════════════════════════════════════════════════
if page=="global":
    page_header("DASHBOARD GLOBAL","Vue d'ensemble — 10 tranches × 25 jours · 3 départements · 4 produits")
    sel_tab=tab_bar([" Journalier"," Par Tranche"],"tab_global")
    fc1,fc2=st.columns(2)
    with fc1: sel_prod=st.selectbox("Produit",["Tous","P1","P2","P3","P4"],key="g_prod")
    with fc2: sel_dept=st.selectbox("Département",["Tous"]+list(DEPT_COLORS.keys()),key="g_dept")
    if sel_tab==" Par Tranche":
        sel_t=tranche_toggle("g")
        if not sel_t: st.warning("Sélectionnez au moins une tranche."); st.stop()
    else:
        sel_t=ALL_T
    combined=pd.concat(dfs.values(),ignore_index=True)
    df=combined[combined["Tranche"].isin(sel_t)].copy()
    if sel_prod!="Tous": df=df[df["Produit"]==sel_prod]
    if sel_dept!="Tous": df=df[df["Département"]==sel_dept]
    if df.empty: st.warning("Aucune donnée."); st.stop()
    trs_m=df["TRS"].mean()*100; td_m=df["TD"].mean()*100; tq_m=df["TQ"].mean()*100; tp_m=df["TP"].mean()*100
    st.markdown("---")
    kpi_row(trs_m,td_m,tq_m,tp_m)
    if sel_tab==" Par Tranche":
        by_t=df.groupby("Tranche")[["TRS","TD","TQ","TP"]].mean().reset_index().sort_values("Tranche")
        st.markdown("<div class='sh'>Évolution TRS · TD · TQ · TP par Tranche</div>",unsafe_allow_html=True)
        fig_ev=go.Figure()
        for kpi,c in KPI_C.items(): fig_ev.add_trace(go.Scatter(x=by_t["Tranche"],y=by_t[kpi]*100,name=kpi,line=dict(color=c,width=2.5),mode="lines+markers",marker=dict(size=7)))
        add_thresh(fig_ev,["TRS","TD","TQ","TP"]); fig_ev.update_layout(height=290,**bl(),xaxis=txax(by_t["Tranche"]),yaxis=ax(pct=True)); fig_ev.update_yaxes(range=[0,110])
        st.plotly_chart(fig_ev,use_container_width=True)
        cl,cr=st.columns(2)
        with cl:
            by_dt=df.groupby(["Tranche","Département"])["TRS"].mean().reset_index().sort_values("Tranche")
            fig_dt=go.Figure()
            for dept,c in DEPT_COLORS.items():
                sub=by_dt[by_dt["Département"]==dept]
                if not sub.empty: fig_dt.add_trace(go.Scatter(x=sub["Tranche"],y=sub["TRS"]*100,name=dept,line=dict(color=c,width=2),mode="lines+markers",marker=dict(size=6)))
            fig_dt.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.2)
            fig_dt.update_layout(height=240,**bl(),xaxis=txax(by_dt["Tranche"]),yaxis=ax(pct=True)); fig_dt.update_yaxes(range=[0,110])
            st.plotly_chart(fig_dt,use_container_width=True)
        with cr:
            by_pt=df.groupby(["Tranche","Produit"])["TRS"].mean().reset_index().sort_values("Tranche")
            fig_pt=go.Figure()
            for p,c in PROD_C.items():
                sub=by_pt[by_pt["Produit"]==p]
                if not sub.empty: fig_pt.add_trace(go.Scatter(x=sub["Tranche"],y=sub["TRS"]*100,name=p,line=dict(color=c,width=2),mode="lines+markers",marker=dict(size=6)))
            fig_pt.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.2)
            fig_pt.update_layout(height=240,**bl(),xaxis=txax(by_pt["Tranche"]),yaxis=ax(pct=True)); fig_pt.update_yaxes(range=[0,110])
            st.plotly_chart(fig_pt,use_container_width=True)
        piv=(df.groupby(["Département","Tranche"])["TRS"].mean().unstack().sort_index()*100).round(1); piv=piv.reindex(sorted(piv.columns),axis=1)
        fig_hm=go.Figure(go.Heatmap(z=piv.values,x=[f"T{int(c)}" for c in sorted(piv.columns)],y=piv.index.tolist(),colorscale=[[0,"#1c2128"],[0.5,"#d29922"],[1,"#3fb950"]],zmin=0,zmax=100,text=piv.values.astype(str),texttemplate="%{text}%",textfont=dict(size=10,color="white"),colorbar=dict(ticksuffix="%",tickfont=dict(color=MUTED))))
        fig_hm.update_layout(height=185,**bl(legend=False),xaxis=ax(),yaxis=ax()); st.plotly_chart(fig_hm,use_container_width=True)
        st.dataframe(recap_table(df),use_container_width=True,hide_index=True,column_config=pbar_cfg())
    else:
        comb_all=pd.concat(dfs.values(),ignore_index=True)
        if sel_prod!="Tous": comb_all=comb_all[comb_all["Produit"]==sel_prod]
        fig_jg=go.Figure()
        pal_bg=["rgba(88,166,255,0.04)","rgba(63,185,80,0.04)","rgba(210,153,34,0.04)","rgba(163,113,247,0.04)","rgba(248,81,73,0.04)"]
        for t in range(1,11):
            fig_jg.add_vrect(x0=(t-1)*25+1,x1=t*25,fillcolor=pal_bg[(t-1)%5],layer="below",line_width=0)
            fig_jg.add_annotation(x=((t-1)*25+1+t*25)/2,y=107,text=f"T{t}",showarrow=False,font=dict(color=MUTED,size=8),yref="y")
        for dept,dc in DEPT_COLORS.items():
            sub_d=comb_all[comb_all["Département"]==dept].groupby("Journée")["TRS"].mean().reset_index().sort_values("Journée")
            if not sub_d.empty: fig_jg.add_trace(go.Scatter(x=sub_d["Journée"],y=sub_d["TRS"]*100,name=dept,line=dict(color=dc,width=1.5),mode="lines"))
        fig_jg.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.5,annotation_text="Seuil 85%",annotation_font=dict(color="#f85149",size=9))
        fig_jg.update_layout(height=270,**bl(),xaxis=ax(title="Journée (1–250)"),yaxis=ax(pct=True)); fig_jg.update_yaxes(range=[0,110])
        st.plotly_chart(fig_jg,use_container_width=True)
        cl2,cr2=st.columns(2)
        with cl2:
            fig_dj=go.Figure()
            for dept,dc in DEPT_COLORS.items():
                sub=comb_all[comb_all["Département"]==dept].groupby("Journée")["TRS"].mean().reset_index().sort_values("Journée")
                if not sub.empty: fig_dj.add_trace(go.Scatter(x=sub["Journée"],y=sub["TRS"]*100,name=dept,line=dict(color=dc,width=1.5),mode="lines",fill="tozeroy",fillcolor=DEPT_FILL[dept]))
            fig_dj.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.2)
            fig_dj.update_layout(height=230,**bl(),xaxis=ax(title="Journée"),yaxis=ax(pct=True)); fig_dj.update_yaxes(range=[0,110]); st.plotly_chart(fig_dj,use_container_width=True)
        with cr2:
            fig_pj=go.Figure()
            for p,pc in PROD_C.items():
                sub=comb_all[comb_all["Produit"]==p].groupby("Journée")["TRS"].mean().reset_index().sort_values("Journée")
                if not sub.empty: fig_pj.add_trace(go.Scatter(x=sub["Journée"],y=sub["TRS"]*100,name=p,line=dict(color=pc,width=1.5),mode="lines"))
            fig_pj.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.2)
            fig_pj.update_layout(height=230,**bl(),xaxis=ax(title="Journée"),yaxis=ax(pct=True)); fig_pj.update_yaxes(range=[0,110]); st.plotly_chart(fig_pj,use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# DEPT PAGE
# ══════════════════════════════════════════════════════════════════════════════
def dept_page(dept_name):
    dc=DEPT_COLORS[dept_name]; icons={"Découpe","Usinage","Peinture"}
    page_header(icons[dept_name],f"DÉPARTEMENT {dept_name.upper()}","Filtrage interactif — seuils TPM")

    # ── 1. TAB BAR (top) ──
    sel_tab=tab_bar([" Visualisation"," Analyse Détaillée"," Solutions & Gains"],f"tab_dept_{dept_name}")

    # ── 2. COMMON FILTER: Produit only ──
    sel_prod=st.selectbox("Produit",["Tous","P1","P2","P3","P4"],key=f"p_{dept_name}")

    # ── 3. Determine tranche selection (only shown in Visualisation Par Tranche and Analyse) ──
    # For Analyse and Solutions we use ALL tranches unless we gather from a stored key
    all_sel_t=ALL_T

    # Preload df with all tranches (used in Analyse & Solutions)
    df_all=dfs[dept_name].copy()
    if sel_prod!="Tous": df_all=df_all[df_all["Produit"]==sel_prod]

    trs_m=df_all["TRS"].mean()*100; td_m=df_all["TD"].mean()*100; tq_m=df_all["TQ"].mean()*100; tp_m=df_all["TP"].mean()*100

    # ── 4. KPI ROW (always visible, below tabs & product filter) ──
    st.markdown("---")
    kpi_row(trs_m,td_m,tq_m,tp_m)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB: VISUALISATION
    # ══════════════════════════════════════════════════════════════════════════
    if sel_tab==" Visualisation":
        # Sub toggle Journalier / Par Tranche BELOW kpi row
        sub_key=f"visu_sub_{dept_name}"
        if sub_key not in st.session_state: st.session_state[sub_key]=" Journalier"
        sv1,sv2,_=st.columns([1.4,1.4,8])
        with sv1:
            if st.button(" Journalier",key=f"vj_{dept_name}",use_container_width=True,type="primary" if st.session_state[sub_key]==" Journalier" else "secondary"):
                st.session_state[sub_key]=" Journalier"; st.rerun()
        with sv2:
            if st.button(" Par Tranche",key=f"vt_{dept_name}",use_container_width=True,type="primary" if st.session_state[sub_key]==" Par Tranche" else "secondary"):
                st.session_state[sub_key]=" Par Tranche"; st.rerun()
        vm=st.session_state[sub_key]
        st.markdown("<br>",unsafe_allow_html=True)

        # Tranche filter ONLY inside Par Tranche
        if vm==" Par Tranche":
            sel_t=tranche_toggle(f"vis_{dept_name}")
            if not sel_t: st.warning("Sélectionnez au moins une tranche."); return
            df_v=dfs[dept_name][dfs[dept_name]["Tranche"].isin(sel_t)].copy()
        else:
            sel_t=ALL_T
            df_v=dfs[dept_name].copy()
        if sel_prod!="Tous": df_v=df_v[df_v["Produit"]==sel_prod]

        # Gauges
        trs_v=df_v["TRS"].mean()*100; td_v=df_v["TD"].mean()*100; tq_v=df_v["TQ"].mean()*100; tp_v=df_v["TP"].mean()*100
        cg1,cg2,cg3,cg4=st.columns(4)
        with cg1: st.plotly_chart(gauge(trs_v,"TRS",dc,85),use_container_width=True,key=f"g1_{dept_name}")
        with cg2: st.plotly_chart(gauge(td_v,"TD","#58a6ff",90),use_container_width=True,key=f"g2_{dept_name}")
        with cg3: st.plotly_chart(gauge(tq_v,"TQ","#3fb950",98),use_container_width=True,key=f"g3_{dept_name}")
        with cg4: st.plotly_chart(gauge(tp_v,"TP","#d29922",95),use_container_width=True,key=f"g4_{dept_name}")

        if vm==" Par Tranche":
            by_t=df_v.groupby("Tranche")[["TRS","TD","TQ","TP"]].mean().reset_index().sort_values("Tranche")
            xvals=by_t["Tranche"]; xlabels=[f"T{int(v)}" for v in xvals]; xax_cfg=txax(xvals)
            st.markdown("<div class='sh'>Évolution TRS · TD · TQ · TP par Tranche</div>",unsafe_allow_html=True)
            fig_t=go.Figure()
            for kpi,c in KPI_C.items(): fig_t.add_trace(go.Scatter(x=xvals,y=by_t[kpi]*100,name=kpi,line=dict(color=c,width=2.5),mode="lines+markers",marker=dict(size=7)))
            add_thresh(fig_t,["TRS","TD","TQ","TP"]); fig_t.update_layout(height=285,**bl(),xaxis=xax_cfg,yaxis=ax(pct=True)); fig_t.update_yaxes(range=[0,110])
            st.plotly_chart(fig_t,use_container_width=True)
            st.markdown("<div class='sh'>Évolution individuelle</div>",unsafe_allow_html=True)
            cA,cB,cC,cD=st.columns(4)
            for col_,kpi,thresh in [(cA,"TRS",85),(cB,"TD",90),(cC,"TQ",98),(cD,"TP",95)]:
                with col_:
                    fk=go.Figure(); fk.add_trace(go.Scatter(x=xvals,y=by_t[kpi]*100,name=kpi,line=dict(color=KPI_C[kpi],width=2),mode="lines+markers",marker=dict(size=6),fill="tozeroy",fillcolor=FILL_C[kpi]))
                    fk.add_hline(y=thresh,line_dash="dash",line_color=THRESH_C[kpi],line_width=1.5,annotation_text=f"Seuil {thresh}%",annotation_font=dict(color=THRESH_C[kpi],size=8))
                    fk.update_layout(height=185,**bl(legend=False),xaxis=xax_cfg,yaxis=ax(pct=True),title=dict(text=f"Évolution {kpi}",font=dict(color=TEXT,size=10))); fk.update_yaxes(range=[0,110])
                    st.plotly_chart(fk,use_container_width=True,key=f"ind_{kpi}_{dept_name}")
            fig_j=go.Figure()
            for kpi,c in KPI_C.items():
                yv=by_t[kpi]*100
                fig_j.add_trace(go.Bar(name=kpi,x=xlabels,y=yv,marker_color=c,marker_line_color="rgba(0,0,0,0)",text=[f"{v:.1f}%" for v in yv],textposition="outside",textfont=dict(color=TEXT,size=8)))
            for kpi in ["TRS","TD","TQ","TP"]: fig_j.add_hline(y=THRESHOLDS[kpi],line_dash="dash",line_color=THRESH_C[kpi],line_width=1.2)
            fig_j.update_layout(barmode="group",height=290,**bl(),xaxis=ax(title="Tranche"),yaxis=ax(pct=True)); fig_j.update_yaxes(range=[0,115]); st.plotly_chart(fig_j,use_container_width=True)
            st.dataframe(recap_table(df_v),use_container_width=True,hide_index=True,column_config=pbar_cfg())
        else:
            # Journalier
            fig_jd=go.Figure()
            pal_bg=["rgba(88,166,255,0.04)","rgba(63,185,80,0.04)","rgba(210,153,34,0.04)","rgba(163,113,247,0.04)","rgba(248,81,73,0.04)"]
            for t in range(1,11):
                fig_jd.add_vrect(x0=(t-1)*25+1,x1=t*25,fillcolor=pal_bg[(t-1)%5],layer="below",line_width=0)
                fig_jd.add_annotation(x=((t-1)*25+1+t*25)/2,y=107,text=f"T{t}",showarrow=False,font=dict(color=MUTED,size=8),yref="y")
            sub_j=dfs[dept_name].copy()
            if sel_prod!="Tous": sub_j=sub_j[sub_j["Produit"]==sel_prod]
            for kpi,c in KPI_C.items():
                gj=sub_j.groupby("Journée")[kpi].mean().reset_index().sort_values("Journée")
                fig_jd.add_trace(go.Scatter(x=gj["Journée"],y=gj[kpi]*100,name=kpi,line=dict(color=c,width=1.5),mode="lines"))
            fig_jd.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.5)
            fig_jd.update_layout(height=280,**bl(),xaxis=ax(title="Journée (1–250)"),yaxis=ax(pct=True)); fig_jd.update_yaxes(range=[0,110]); st.plotly_chart(fig_jd,use_container_width=True)
            cl2,cr2=st.columns(2)
            with cl2:
                fig_fill=go.Figure()
                gj_trs=sub_j.groupby("Journée")["TRS"].mean().reset_index().sort_values("Journée")
                fig_fill.add_trace(go.Scatter(x=gj_trs["Journée"],y=gj_trs["TRS"]*100,line=dict(color=dc,width=2),mode="lines",fill="tozeroy",fillcolor=DEPT_FILL[dept_name]))
                fig_fill.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.5)
                fig_fill.update_layout(height=220,**bl(legend=False),xaxis=ax(title="Journée"),yaxis=ax(pct=True),title=dict(text="TRS journalier",font=dict(color=MUTED,size=10))); fig_fill.update_yaxes(range=[0,110]); st.plotly_chart(fig_fill,use_container_width=True)
            with cr2:
                by_t2=sub_j.groupby("Tranche")[["TRS","TD","TQ","TP"]].mean().reset_index().sort_values("Tranche")
                fig_mini=go.Figure()
                for kpi,c in KPI_C.items(): fig_mini.add_trace(go.Scatter(x=by_t2["Tranche"],y=by_t2[kpi]*100,name=kpi,line=dict(color=c,width=2),mode="lines+markers",marker=dict(size=5)))
                fig_mini.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1)
                fig_mini.update_layout(height=220,**bl(),xaxis=txax(by_t2["Tranche"]),yaxis=ax(pct=True),title=dict(text="KPIs moyens par Tranche",font=dict(color=MUTED,size=10))); fig_mini.update_yaxes(range=[0,110]); st.plotly_chart(fig_mini,use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB: ANALYSE DÉTAILLÉE
    # ══════════════════════════════════════════════════════════════════════════
    elif sel_tab==" Analyse Détaillée":
        df=df_all
        pv={l:df[c].fillna(0).sum() for l,(c,_,_) in PDEF.items()}
        td_l=pv["Pannes"]+pv["Remplacement préventif"]
        tp_l=sum(pv[l] for l,(_,f,_) in PDEF.items() if f=="TP")
        tq_l=pv["Rejet démarrage"]+pv["Rejet qualité"]
        total_all=max(td_l+tp_l+tq_l,1)

        # TRS formula banner
        st.markdown("""<div class='formula-box'>
<p style='color:#8b949e;font-size:0.72rem;text-transform:uppercase;letter-spacing:2px;margin:0 0 6px'>Identité fondamentale TPM</p>
<p style='font-family:Rajdhani;font-size:2rem;font-weight:700;color:#58a6ff;margin:0;letter-spacing:3px'>TRS = TD × TP × TQ</p>
<p style='color:#8b949e;font-size:0.75rem;margin:6px 0 0'>La démarche TPM structure l'analyse de l'inefficacité autour de cette identité. Chaque facteur est dégradé par des familles de pertes issues des données de production.</p>
</div>""",unsafe_allow_html=True)

        # Pertes KPI cards
        a1,a2,a3,a4=st.columns(4)
        with a1: st.markdown(kcard("PERTES TD",f"{td_l:,.0f} min","red",f"🔴 {td_l/total_all*100:.0f}% du total"),unsafe_allow_html=True)
        with a2: st.markdown(kcard("PERTES TP",f"{tp_l:,.0f} min","orange",f"🟡 {tp_l/total_all*100:.0f}% du total"),unsafe_allow_html=True)
        with a3: st.markdown(kcard("PERTES TQ",f"{tq_l:,.0f} pcs","teal",f"🟢 {tq_l/total_all*100:.0f}% du total"),unsafe_allow_html=True)
        with a4: st.markdown(kcard("TOTAL",f"{total_all:,.0f}","purple","11 sources"),unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)

        # ── TD ──
        st.markdown("""<div style='background:#1a1010;border:1px solid #f85149;border-radius:8px;padding:14px 18px;margin:8px 0 12px'>
<p style='color:#f85149;font-family:Rajdhani;font-size:1.1rem;font-weight:700;margin:0 0 6px'>🔴 PERTES DE DISPONIBILITÉ — réduisent TD</p>
<div style='background:#0d1f2d;border:1px solid #1f6feb;border-radius:8px;padding:10px 14px;margin:0 0 10px'>
<code style='color:#58a6ff;font-size:0.9rem'>TD = TFB / TR</code>
<span style='color:#8b949e;font-size:0.76rem'>&nbsp;&nbsp;où TR = TO − arrêts planifiés </span></div>
<p style='color:#c9d1d9;font-size:0.78rem;margin:0 0 10px'>Tout événement qui immobilise la machine sans produire détériore TD.</p>
<table class='cause-table'><tr><th>Source</th><th>Colonne</th><th>Impact</th></tr>
<tr><td><strong style='color:#f85149'>Pannes</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px;color:#f0883e'>Panne</code></td><td>Arrêt non planifié — cause principale de dégradation du TD dans les 3 départements</td></tr>
<tr><td><strong style='color:#c9362e'>Remplacement préventif</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px;color:#f0883e'>Remplacement_préventif</code></td><td>Intervention planifiée qui retire néanmoins la machine du flux de production</td></tr>
</table></div>""",unsafe_allow_html=True)
        td1,td2,td3=st.columns(3)
        with td1: st.markdown(kcard("TD MOYEN",f"{td_m:.1f}%","green" if td_m>=90 else "red",f"Seuil ≥ 90% {'✅' if td_m>=90 else '⚠️ -'+str(round(90-td_m,1))+'pts'}"),unsafe_allow_html=True)
        with td2: st.markdown(kcard("PANNES",f"{pv['Pannes']:,.0f} min","red",f"{pv['Pannes']/max(td_l,1)*100:.0f}% des pertes TD"),unsafe_allow_html=True)
        with td3: st.markdown(kcard("MAINT. PRÉVENTIVE",f"{pv['Remplacement préventif']:,.0f} min","orange",f"{pv['Remplacement préventif']/max(td_l,1)*100:.0f}% des pertes TD"),unsafe_allow_html=True)
        by_td=df.groupby("Tranche").agg(Pannes=("Panne","sum"),Remplac=("Remplacement_préventif",lambda x:x.fillna(0).sum())).reset_index().sort_values("Tranche")
        fig_td=go.Figure()
        fig_td.add_trace(go.Bar(name="Pannes",x=[f"T{int(t)}" for t in by_td["Tranche"]],y=by_td["Pannes"],marker_color="#f85149",marker_line_color="rgba(0,0,0,0)"))
        fig_td.add_trace(go.Bar(name="Remplacement",x=[f"T{int(t)}" for t in by_td["Tranche"]],y=by_td["Remplac"],marker_color="#c9362e",marker_line_color="rgba(0,0,0,0)"))
        fig_td.update_layout(barmode="stack",height=200,**bl(),xaxis=ax(title="Tranche"),yaxis=ax(title="Min perdues"),title=dict(text="Pertes TD par Tranche",font=dict(color=MUTED,size=10)))
        st.plotly_chart(fig_td,use_container_width=True)

        # ── TP ──
        st.markdown("""<div style='background:#1a1a0a;border:1px solid #d29922;border-radius:8px;padding:14px 18px;margin:8px 0 12px'>
<p style='color:#d29922;font-family:Rajdhani;font-size:1.1rem;font-weight:700;margin:0 0 6px'>🟡 PERTES DE PERFORMANCE — réduisent TP</p>
<div style='background:#0d1f2d;border:1px solid #1f6feb;border-radius:8px;padding:10px 14px;margin:0 0 10px'>
<code style='color:#58a6ff;font-size:0.9rem'>TP = tn / tfb</code>
<span style='color:#8b949e;font-size:0.76rem'>&nbsp;&nbsp;où tfb = TR − (Arrêts + Nettoyage + Réglage + Inspection + Changement outil + Déplacement + Lubrification)</span></div>
<p style='color:#c9d1d9;font-size:0.78rem;margin:0 0 10px'>Tout événement qui ralentit la production sans l'arrêter complètement dégrade TP.</p>
<table class='cause-table'><tr><th>Source</th><th>Colonne</th><th>Impact</th></tr>
<tr><td><strong style='color:#d29922'>Arrêts mineurs</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px;color:#f0883e'>Arrêts_mineurs</code></td><td>Micro-arrêts &lt;5 min, non comptés comme pannes, mais qui freinent la cadence réelle</td></tr>
<tr><td><strong style='color:#e3b341'>Nettoyage</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px;color:#f0883e'>Nettoyage</code></td><td>Temps improductif récurrent — à optimiser via la démarche 5S</td></tr>
<tr><td><strong style='color:#f0c040'>Réglage dérive</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px;color:#f0883e'>Réglage_dérive</code></td><td>Correction d'une dérive machine — indicateur d'instabilité processus</td></tr>
<tr><td><strong style='color:#ffd166'>Inspection</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px;color:#f0883e'>Inspection</code></td><td>Contrôle réalisé pendant le temps machine — à intégrer dans les standards opératoires</td></tr>
<tr><td><strong style='color:#ffb347'>Changement d'outil</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px;color:#f0883e'>Changement_outil</code></td><td>Levier SMED : réduire ces temps améliore directement TP</td></tr>
<tr><td><strong style='color:#f4845f'>Déplacement</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px;color:#f0883e'>Déplacement</code></td><td>Gaspillage transport Lean — signe de flux ou d'implantation non optimisés</td></tr>
<tr><td><strong style='color:#c77dff'>Lubrification</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px;color:#f0883e'>Lubrification</code></td><td>Maintenance de base à intégrer dans la maintenance autonome (pilier TPM)</td></tr>
</table></div>""",unsafe_allow_html=True)
        tp1,tp2,tp3,tp4=st.columns(4)
        for ci,lbl in enumerate(["Arrêts mineurs","Nettoyage","Réglage dérive","Changement outil"]):
            v=pv.get(lbl,0)
            with [tp1,tp2,tp3,tp4][ci]: st.markdown(kcard(lbl.upper(),f"{v:,.0f} min","orange",f"{v/max(tp_l,1)*100:.0f}% TP"),unsafe_allow_html=True)
        by_tp2=df.groupby("Tranche").agg(Arrêts=("Arrêts_mineurs","sum"),Nettoyage=("Nettoyage","sum"),Réglage=("Réglage_dérive","sum"),Inspection=("Inspection","sum"),Outil=("Changement_outil","sum"),Déplacement=("Déplacement",lambda x:x.fillna(0).sum()),Lubrification=("Lubrification","sum")).reset_index().sort_values("Tranche")
        tlbl=[f"T{int(t)}" for t in by_tp2["Tranche"]]
        fig_tp2=go.Figure()
        for cn,lbl_,c_ in [("Arrêts","Arrêts mineurs","#d29922"),("Nettoyage","Nettoyage","#e3b341"),("Réglage","Réglage dérive","#f0c040"),("Inspection","Inspection","#ffd166"),("Outil","Changement outil","#ffb347"),("Déplacement","Déplacement","#f4845f"),("Lubrification","Lubrification","#c77dff")]:
            fig_tp2.add_trace(go.Bar(name=lbl_,x=tlbl,y=by_tp2[cn],marker_color=c_,marker_line_color="rgba(0,0,0,0)"))
        fig_tp2.update_layout(barmode="stack",height=210,**bl(),xaxis=ax(title="Tranche"),yaxis=ax(title="Min perdues"),title=dict(text="Pertes TP — 7 sources",font=dict(color=MUTED,size=10)))
        st.plotly_chart(fig_tp2,use_container_width=True)

        # ── TQ ──
        st.markdown("""<div style='background:#0a1a0a;border:1px solid #3fb950;border-radius:8px;padding:14px 18px;margin:8px 0 12px'>
<p style='color:#3fb950;font-family:Rajdhani;font-size:1.1rem;font-weight:700;margin:0 0 6px'>🟢 PERTES DE QUALITÉ — réduisent TQ</p>
<div style='background:#0d1f2d;border:1px solid #1f6feb;border-radius:8px;padding:10px 14px;margin:0 0 10px'>
<code style='color:#58a6ff;font-size:0.9rem'>TQ = (Quantité − Rejets) / Quantité</code>
<span style='color:#8b949e;font-size:0.76rem'>&nbsp;&nbsp;où Rejets = Rejet_Démarrage + Rejet_qualité</span></div>
<p style='color:#c9d1d9;font-size:0.78rem;margin:0 0 10px'>Tout défaut — détecté en démarrage ou en production — dégrade TQ.</p>
<table class='cause-table'><tr><th>Source</th><th>Colonne</th><th>Impact</th></tr>
<tr><td><strong style='color:#3fb950'>Rejet démarrage</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px;color:#f0883e'>Rejet_Démarrage</code></td><td>Pièces non conformes lors de la mise en régime — liées à la répétabilité des réglages</td></tr>
<tr><td><strong style='color:#56d364'>Rejet qualité</strong></td><td><code style='background:#1c2128;padding:1px 5px;border-radius:3px;color:#f0883e'>Rejet_qualité</code></td><td>Défauts détectés en cours de production — indicateur de la capabilité processus</td></tr>
</table></div>""",unsafe_allow_html=True)
        tq1,tq2,tq3=st.columns(3)
        with tq1: st.markdown(kcard("TQ MOYEN",f"{tq_m:.1f}%","green" if tq_m>=98 else "red",f"Seuil ≥ 98% {'✅' if tq_m>=98 else '⚠️ -'+str(round(98-tq_m,1))+'pts'}"),unsafe_allow_html=True)
        with tq2: st.markdown(kcard("REJET DÉMARRAGE",f"{pv['Rejet démarrage']:,.0f} pcs","green",f"{pv['Rejet démarrage']/max(tq_l,1)*100:.0f}% rejets"),unsafe_allow_html=True)
        with tq3: st.markdown(kcard("REJET QUALITÉ",f"{pv['Rejet qualité']:,.0f} pcs","teal",f"{pv['Rejet qualité']/max(tq_l,1)*100:.0f}% rejets"),unsafe_allow_html=True)
        by_tq=df.groupby("Tranche").agg(RQ=("Rejet_qualité","sum"),RD=("Rejet_Démarrage",lambda x:x.fillna(0).sum())).reset_index().sort_values("Tranche")
        fig_tq=go.Figure()
        fig_tq.add_trace(go.Bar(name="Rejet qualité",x=[f"T{int(t)}" for t in by_tq["Tranche"]],y=by_tq["RQ"],marker_color="#3fb950",marker_line_color="rgba(0,0,0,0)"))
        fig_tq.add_trace(go.Bar(name="Rejet démarrage",x=[f"T{int(t)}" for t in by_tq["Tranche"]],y=by_tq["RD"],marker_color="#56d364",marker_line_color="rgba(0,0,0,0)"))
        fig_tq.update_layout(barmode="stack",height=195,**bl(),xaxis=ax(title="Tranche"),yaxis=ax(title="Pièces rejetées"),title=dict(text="Pertes TQ par Tranche",font=dict(color=MUTED,size=10)))
        st.plotly_chart(fig_tq,use_container_width=True)

        # Pareto + Donut
        cl2,cr2=st.columns(2)
        with cl2:
            st.markdown("<div class='sh'>Pareto — Règle 80/20</div>",unsafe_allow_html=True)
            sp=dict(sorted(pv.items(),key=lambda x:x[1],reverse=True)); labels=list(sp.keys()); vals_=list(sp.values())
            cumul=np.cumsum(vals_)/max(sum(vals_),1)*100; bar_c=[PDEF[l][2] for l in labels]
            fig_par=make_subplots(specs=[[{"secondary_y":True}]])
            fig_par.add_trace(go.Bar(x=labels,y=vals_,name="Total",marker_color=bar_c,marker_line_color="rgba(0,0,0,0)"),secondary_y=False)
            fig_par.add_trace(go.Scatter(x=labels,y=cumul,name="Cumulé %",line=dict(color="#f0883e",width=2),mode="lines+markers"),secondary_y=True)
            fig_par.add_hline(y=80,line_dash="dot",line_color="#8b949e",line_width=1,annotation_text="80%",annotation_font=dict(color=MUTED,size=9),secondary_y=True)
            fig_par.update_layout(height=290,**bl(),xaxis=ax(angle=30),yaxis=ax(),yaxis2=dict(ticksuffix="%",tickfont=dict(color=MUTED,size=10),gridcolor="#1e2430"))
            st.plotly_chart(fig_par,use_container_width=True)
        with cr2:
            st.markdown("<div class='sh'>Anneau — 6 Grandes Pertes TPM</div>",unsafe_allow_html=True)
            dv=[pv.get("Arrêts mineurs",0),pv["Pannes"],tq_l,pv.get("Nettoyage",0)+pv.get("Réglage dérive",0)+pv.get("Changement outil",0),pv.get("Rejet démarrage",0),pv.get("Lubrification",0)+pv.get("Déplacement",0)+pv.get("Inspection",0)]
            dl_=["Vitesse réduite (TP)","Pannes (TD)","Rejets qualité (TQ)","Arrêts mineurs (TP)","Démarrages (TQ)","Nettoyage/Réglage (TP)"]
            dc_=["#58a6ff","#f85149","#3fb950","#d29922","#a371f7","#39d353"]
            total_d=max(sum(dv),1)
            fig_do=go.Figure(go.Pie(labels=[f"{l} {v/total_d*100:.1f}%" for l,v in zip(dl_,dv)],values=dv,hole=0.52,marker=dict(colors=dc_,line=dict(color=BG,width=2)),textfont=dict(color="white",size=10),textposition="inside",textinfo="percent"))
            fig_do.update_layout(height=290,**bl(),showlegend=True)  # legend via bl() only
            st.plotly_chart(fig_do,use_container_width=True)

        # Analyse par Produit
        st.markdown("<div class='sh'>Analyse par Produit — KPIs & Pertes</div>",unsafe_allow_html=True)
        by_p=df.groupby("Produit").agg(TRS=("TRS","mean"),TD=("TD","mean"),TQ=("TQ","mean"),TP=("TP","mean"),Panne=("Panne","sum"),Rejet_qualité=("Rejet_qualité","sum"),Rejet_Démarrage=("Rejet_Démarrage",lambda x:x.fillna(0).sum())).reset_index()
        prods=[p for p in ["P1","P2","P3","P4"] if p in by_p["Produit"].values]
        cl_p,cr_p=st.columns(2)
        with cl_p:
            fig_pg=go.Figure()
            for kpi,c in KPI_C.items():
                vals=[float(by_p[by_p["Produit"]==p][kpi].values[0])*100 if p in by_p["Produit"].values else 0 for p in prods]
                fig_pg.add_trace(go.Bar(name=kpi,x=prods,y=vals,marker_color=c,marker_line_color="rgba(0,0,0,0)",text=[f"{v:.1f}%" for v in vals],textposition="outside",textfont=dict(color=TEXT,size=9)))
            for kpi in ["TRS","TD","TQ","TP"]: fig_pg.add_hline(y=THRESHOLDS[kpi],line_dash="dash",line_color=THRESH_C[kpi],line_width=1)
            fig_pg.update_layout(barmode="group",height=270,**bl(),title=dict(text="KPIs par Produit",font=dict(color=TEXT,size=11)),xaxis=ax(title="Produit"),yaxis=ax(pct=True)); fig_pg.update_yaxes(range=[0,115]); st.plotly_chart(fig_pg,use_container_width=True)
        with cr_p:
            scores=[]
            for p in prods:
                row=by_p[by_p["Produit"]==p]; trs_p=float(row["TRS"].values[0])*100; td_p=float(row["TD"].values[0])*100; tq_p=float(row["TQ"].values[0])*100; tp_p=float(row["TP"].values[0])*100
                gap=max(0,85-trs_p)+max(0,90-td_p)+max(0,98-tq_p)+max(0,95-tp_p)
                scores.append({"Produit":p,"TRS %":round(trs_p,1),"TD %":round(td_p,1),"TQ %":round(tq_p,1),"TP %":round(tp_p,1),"Écart":round(gap,1)})
            sdf=pd.DataFrame(scores).sort_values("Écart",ascending=False)
            if not sdf.empty:
                w=sdf.iloc[0]; b=sdf.iloc[-1]
                st.markdown(f"<div style='background:#1a1010;border:1px solid #f85149;border-radius:8px;padding:10px 14px;margin-bottom:8px'><p style='color:#f85149;font-weight:700;margin:0 0 2px;font-family:Rajdhani'>⚠️ Plus critique : {w['Produit']} — Écart : {w['Écart']}%</p><p style='color:#c9d1d9;font-size:0.76rem;margin:0'>TRS={w['TRS %']}% · TD={w['TD %']}% · TQ={w['TQ %']}% · TP={w['TP %']}%</p></div>",unsafe_allow_html=True)
                st.markdown(f"<div style='background:#0d1a0d;border:1px solid #3fb950;border-radius:8px;padding:10px 14px;margin-bottom:8px'><p style='color:#3fb950;font-weight:700;margin:0 0 2px;font-family:Rajdhani'>✅ Meilleur : {b['Produit']} — Écart : {b['Écart']}%</p><p style='color:#c9d1d9;font-size:0.76rem;margin:0'>TRS={b['TRS %']}% · TD={b['TD %']}% · TQ={b['TQ %']}% · TP={b['TP %']}%</p></div>",unsafe_allow_html=True)
            pbar4={"TRS %":st.column_config.ProgressColumn("TRS %",min_value=0,max_value=100,format="%.1f%%"),"TD %":st.column_config.ProgressColumn("TD %",min_value=0,max_value=100,format="%.1f%%"),"TQ %":st.column_config.ProgressColumn("TQ %",min_value=0,max_value=100,format="%.1f%%"),"TP %":st.column_config.ProgressColumn("TP %",min_value=0,max_value=100,format="%.1f%%")}
            st.dataframe(sdf,use_container_width=True,hide_index=True,column_config=pbar4)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB: SOLUTIONS & GAINS
    # ══════════════════════════════════════════════════════════════════════════
    elif sel_tab==" Solutions & Gains":
        sol=SOLUTIONS[dept_name]; tgt=TARGETS[dept_name]
        act={"TD":td_m,"TP":tp_m,"TQ":tq_m,"TRS":trs_m}
        trs_act=sol["trs_act"]; trs_obj=sol["trs_obj"]
        st.markdown(f"""<div style='background:linear-gradient(135deg,#0d1f0d,#1a2c1a);border:1px solid #3fb950;border-radius:10px;padding:14px 20px;margin-bottom:20px'>
<p style='color:#3fb950;font-family:Rajdhani;font-size:1.1rem;font-weight:700;margin:0'>Résultat attendu : TRS {trs_act} → {trs_obj} après 10 mois</p>
<p style='color:#8b949e;font-size:0.76rem;margin:4px 0 0'>Actions à appliquer par ordre de priorité sur 10 tranches.</p>
</div>""",unsafe_allow_html=True)
        cols=st.columns(3)
        kpi_labels=[("TD","Amélioration TD","#1565c0"),("TP","Amélioration TP","#1565c0"),("TQ","Amélioration TQ","#1565c0")]
        for col_,(kpi,titre,_) in zip(cols,kpi_labels):
            with col_:
                s=sol[kpi]; a_v=s["act"]; c_v=s["obj"]; delta=c_v-a_v; prog=min(a_v/max(c_v,1)*100,100)
                st.markdown(f"""<h3 style='font-family:Rajdhani;font-size:1.4rem;font-weight:700;color:#e6edf3;margin:0 0 4px'>{titre}</h3>
<p style='color:#8b949e;font-size:0.82rem;font-weight:600;margin:0 0 8px'>
<strong style='color:#e6edf3'>{a_v}%</strong> → <strong style='color:{dc}'>{c_v}%</strong>
<span style='color:#3fb950'> (+{delta:.1f} pts)</span></p>
<div class='prog-bg'><div class='prog-fill' style='background:{dc};width:{prog:.0f}%'></div></div>
<br>""",unsafe_allow_html=True)
                for action in s["actions"]:
                    st.markdown(f"<p style='color:#c9d1d9;font-size:0.8rem;margin:0 0 10px;line-height:1.6'>→ {action}</p>",unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#21262d;margin:20px 0'>",unsafe_allow_html=True)
        st.markdown(f"""<h3 style='font-family:Rajdhani;font-size:1.4rem;font-weight:700;color:#3fb950;margin:0 0 16px'>
Résultat attendu : TRS {trs_act} → {trs_obj} après 10 mois</h3>""",unsafe_allow_html=True)
        kpis_list=["TD","TP","TQ","TRS"]
        fig_ab=go.Figure()
        fig_ab.add_trace(go.Bar(name="Actuel",x=kpis_list,y=[act[k] for k in kpis_list],marker_color="#4a5568",marker_line_color="rgba(0,0,0,0)",text=[f"{act[k]:.1f}%" for k in kpis_list],textposition="outside",textfont=dict(color=TEXT,size=11)))
        fig_ab.add_trace(go.Bar(name="Objectif",x=kpis_list,y=[tgt[k] for k in kpis_list],marker_color=dc,marker_line_color="rgba(0,0,0,0)",text=[f"{tgt[k]:.1f}%" for k in kpis_list],textposition="outside",textfont=dict(color=TEXT,size=11)))
        for kpi in kpis_list: fig_ab.add_hline(y=THRESHOLDS[kpi],line_dash="dot",line_color=THRESH_C[kpi],line_width=1)
        fig_ab.update_layout(barmode="group",height=290,**bl(),title=dict(text=f"Gains estimés — {dept_name}",font=dict(color=MUTED,size=11)),xaxis=ax(),yaxis=ax(pct=True)); fig_ab.update_yaxes(range=[0,115]); st.plotly_chart(fig_ab,use_container_width=True)
        ep_val=EXTRA_PROD[dept_name]; p1,p2,_=st.columns([1,1,2])
        with p1:
            st.markdown(f"""<div style='background:#161b22;border:1px solid #21262d;border-radius:10px;padding:14px 18px;border-left:3px solid {dc}'>
<div style='color:#8b949e;font-size:0.62rem;text-transform:uppercase;margin-bottom:3px'>Unités / jour gagnées</div>
<div style='color:#3fb950;font-family:Rajdhani;font-size:2rem;font-weight:700'>+{ep_val}</div>
<div style='color:#8b949e;font-size:0.7rem'>{dept_name}</div></div>""",unsafe_allow_html=True)
        with p2:
            st.markdown(f"""<div style='background:linear-gradient(135deg,#0d1f0d,#1a2c1a);border:1px solid #3fb950;border-radius:10px;padding:14px 18px'>
<div style='color:#8b949e;font-size:0.62rem;text-transform:uppercase;margin-bottom:3px'>Gain annuel estimé</div>
<div style='color:#3fb950;font-family:Rajdhani;font-size:2rem;font-weight:700'>+{ep_val*250:,}</div>
<div style='color:#8b949e;font-size:0.7rem'>unités sur 250 jours</div></div>""",unsafe_allow_html=True)

if page=="decoupe":  dept_page("Découpe")
elif page=="usinage": dept_page("Usinage")
elif page=="peinture":dept_page("Peinture")

# ══════════════════════════════════════════════════════════════════════════════
# SOURCE DES PERTES
# ══════════════════════════════════════════════════════════════════════════════
elif page=="pertes":
    page_header("SOURCE DES PERTES","Analyse comparative — 3 départements · 11 sources · Pareto · Anneau TPM")
    sel_prod_p=st.selectbox("Produit",["Tous","P1","P2","P3","P4"],key="p_pertes_g")
    sel_t_p=tranche_toggle("p_pertes")
    combined=pd.concat(dfs.values(),ignore_index=True)
    df_all=combined[combined["Tranche"].isin(sel_t_p)].copy()
    if sel_prod_p!="Tous": df_all=df_all[df_all["Produit"]==sel_prod_p]
    if df_all.empty: st.warning("Aucune donnée."); st.stop()
    pv_all={l:df_all[c].fillna(0).sum() for l,(c,_,_) in PDEF.items()}
    td_g=pv_all["Pannes"]+pv_all["Remplacement préventif"]
    tp_g=sum(pv_all[l] for l,(_,f,_) in PDEF.items() if f=="TP")
    tq_g=pv_all["Rejet démarrage"]+pv_all["Rejet qualité"]
    tot_g=max(td_g+tp_g+tq_g,1)
    st.markdown("<br>",unsafe_allow_html=True)
    a1,a2,a3,a4=st.columns(4)
    with a1: st.markdown(kcard("PERTES TD GLOBAL",f"{td_g:,.0f} min","red",f"🔴 {td_g/tot_g*100:.0f}% total"),unsafe_allow_html=True)
    with a2: st.markdown(kcard("PERTES TP GLOBAL",f"{tp_g:,.0f} min","orange",f"🟡 {tp_g/tot_g*100:.0f}% total"),unsafe_allow_html=True)
    with a3: st.markdown(kcard("PERTES TQ GLOBAL",f"{tq_g:,.0f} pcs","teal",f"🟢 {tq_g/tot_g*100:.0f}% total"),unsafe_allow_html=True)
    with a4: st.markdown(kcard("TOTAL PERTES",f"{tot_g:,.0f}","purple","3 depts cumulés"),unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown("<div class='sh'>📊 Volume de Pertes par Département — Comparaison</div>",unsafe_allow_html=True)
    loss_show=["Pannes","Arrêts mineurs","Réglage dérive","Changement outil","Nettoyage","Rejet qualité","Rejet démarrage","Remplacement préventif","Lubrification","Déplacement","Inspection"]
    fig_comp=go.Figure()
    for lbl in loss_show:
        col_name=PDEF[lbl][0]; clr=PDEF[lbl][2]
        vals_per_dept=[df_all[df_all["Département"]==dept][col_name].fillna(0).sum() for dept in ["Découpe","Usinage","Peinture"]]
        fig_comp.add_trace(go.Bar(name=lbl,x=["Découpe","Usinage","Peinture"],y=vals_per_dept,marker_color=clr,marker_line_color="rgba(0,0,0,0)"))
    fig_comp.update_layout(barmode="stack",height=320,**bl(),xaxis=ax(title="Département"),yaxis=ax(title="Total pertes (min / pcs)"),title=dict(text="Répartition des pertes par source et par département",font=dict(color=MUTED,size=11)))
    st.plotly_chart(fig_comp,use_container_width=True)
    st.markdown("<div class='sh'>🕸️ Radar — KPIs par Département vs Norme NFE</div>",unsafe_allow_html=True)
    categories=["TRS","TD","TQ","TP","TRS"]
    fig_rad=go.Figure()
    for dept,dco in DEPT_COLORS.items():
        sub=df_all[df_all["Département"]==dept]
        if sub.empty: continue
        vals_r=[sub["TRS"].mean()*100,sub["TD"].mean()*100,sub["TQ"].mean()*100,sub["TP"].mean()*100,sub["TRS"].mean()*100]
        fig_rad.add_trace(go.Scatterpolar(r=vals_r,theta=categories,fill="toself",name=dept,line=dict(color=dco,width=2),fillcolor=DEPT_FILL[dept]))
    nfe_vals=[THRESHOLDS[k] for k in ["TRS","TD","TQ","TP"]]+[THRESHOLDS["TRS"]]
    fig_rad.add_trace(go.Scatterpolar(r=nfe_vals,theta=categories,fill="toself",name="Norme NFE",line=dict(color="#8b949e",width=2,dash="dash"),fillcolor="rgba(139,148,158,0.06)"))
    fig_rad.update_layout(height=380,**bl(),polar=dict(bgcolor="#161b22",radialaxis=dict(range=[0,115],ticksuffix="%",gridcolor="#21262d",tickfont=dict(color=MUTED,size=9)),angularaxis=dict(gridcolor="#21262d",tickfont=dict(color=TEXT,size=12))))
    st.plotly_chart(fig_rad,use_container_width=True)
    cl2,cr2=st.columns(2)
    with cl2:
        st.markdown("<div class='sh'>Diagramme de Pareto Global</div>",unsafe_allow_html=True)
        st.markdown("""<div class='infobox'><strong style='color:#f0883e'>Règle 80/20 :</strong> 80% des pertes viennent de 20% des causes.</div>""",unsafe_allow_html=True)
        sp=dict(sorted(pv_all.items(),key=lambda x:x[1],reverse=True)); labels=list(sp.keys()); vals_=list(sp.values())
        cumul=np.cumsum(vals_)/max(sum(vals_),1)*100; bar_c=[PDEF[l][2] for l in labels]
        fig_par=make_subplots(specs=[[{"secondary_y":True}]])
        fig_par.add_trace(go.Bar(x=labels,y=vals_,name="Total",marker_color=bar_c,marker_line_color="rgba(0,0,0,0)"),secondary_y=False)
        fig_par.add_trace(go.Scatter(x=labels,y=cumul,name="Cumulé %",line=dict(color="#f0883e",width=2),mode="lines+markers"),secondary_y=True)
        fig_par.add_hline(y=80,line_dash="dot",line_color="#8b949e",line_width=1,annotation_text="80%",annotation_font=dict(color=MUTED,size=9),secondary_y=True)
        fig_par.update_layout(height=320,**bl(),xaxis=ax(angle=30),yaxis=ax(),yaxis2=dict(ticksuffix="%",tickfont=dict(color=MUTED,size=10),gridcolor="#1e2430"))
        st.plotly_chart(fig_par,use_container_width=True)
    with cr2:
        st.markdown("<div class='sh'>Anneau TPM — 6 Grandes Pertes</div>",unsafe_allow_html=True)
        dv=[pv_all.get("Arrêts mineurs",0),pv_all["Pannes"],tq_g,pv_all.get("Nettoyage",0)+pv_all.get("Réglage dérive",0)+pv_all.get("Changement outil",0),pv_all.get("Rejet démarrage",0),pv_all.get("Lubrification",0)+pv_all.get("Déplacement",0)+pv_all.get("Inspection",0)]
        dl_=["Vitesse réduite (TP)","Pannes machines (TD)","Rejets qualité (TQ)","Arrêts mineurs (TP)","Démarrages (TQ)","Nettoyage/Réglage (TP)"]
        dc_=["#58a6ff","#f85149","#3fb950","#d29922","#a371f7","#39d353"]; total_d=max(sum(dv),1)
        fig_do2=go.Figure(go.Pie(labels=[f"{l} {v/total_d*100:.1f}%" for l,v in zip(dl_,dv)],values=dv,hole=0.52,marker=dict(colors=dc_,line=dict(color=BG,width=2)),textfont=dict(color="white",size=10),textposition="inside",textinfo="percent"))
        fig_do2.update_layout(height=320,**bl(),showlegend=True)  # legend via bl() only — no conflict
        st.plotly_chart(fig_do2,use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD FINAL
# ══════════════════════════════════════════════════════════════════════════════
elif page=="final":
    page_header("DASHBOARD FINAL","Plan d'Action Global · Gains · Production supplémentaire")
    sel_tab=tab_bar([" Plan d'Action","Gains & Production"],"tab_final")
    actuals={}
    for dept in ["Découpe","Usinage","Peinture"]:
        d=dfs[dept]; actuals[dept]={"TD":d["TD"].mean()*100,"TP":d["TP"].mean()*100,"TQ":d["TQ"].mean()*100,"TRS":d["TRS"].mean()*100}

    if sel_tab=="🛠️ Plan d'Action":
        st.markdown("<p style='color:#8b949e;font-size:0.78rem;margin:8px 0 4px'>Sélectionner un département</p>",unsafe_allow_html=True)
        sel_dept_f=st.selectbox("",["Découpe","Usinage","Peinture"],key="final_dept_plan",label_visibility="collapsed")
        dc=DEPT_COLORS[sel_dept_f]; sol=SOLUTIONS[sel_dept_f]; tgt=TARGETS[sel_dept_f]; act=actuals[sel_dept_f]
        trs_act_lbl=sol["trs_act"]; trs_obj_lbl=sol["trs_obj"]
        c1,c2,c3=st.columns(3)
        for col_,(kpi,titre) in zip([c1,c2,c3],[("TD","Amélioration TD"),("TP","Amélioration TP"),("TQ","Amélioration TQ")]):
            with col_:
                s=sol[kpi]; a_v=s["act"]; c_v=s["obj"]; delta=c_v-a_v; prog=min(a_v/max(c_v,1)*100,100)
                st.markdown(f"""<h3 style='font-family:Rajdhani;font-size:1.5rem;font-weight:700;color:#e6edf3;margin:16px 0 4px'>{titre}</h3>
<p style='color:#8b949e;font-size:0.85rem;font-weight:600;margin:0 0 10px'>
<strong style='color:#e6edf3'>{a_v}%</strong> → <strong style='color:{dc}'>{c_v}%</strong>
<span style='color:#3fb950'> (+{delta:.1f} pts)</span></p>
<div style='background:#e0e0e022;border-radius:4px;height:5px;margin-bottom:16px'>
  <div style='background:{dc};height:5px;border-radius:4px;width:{prog:.0f}%'></div></div>""",unsafe_allow_html=True)
                for action in s["actions"]:
                    st.markdown(f"<p style='color:#c9d1d9;font-size:0.79rem;margin:0 0 10px;line-height:1.6'>→ {action}</p>",unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#21262d;margin:20px 0'>",unsafe_allow_html=True)
        st.markdown(f"""<h3 style='font-family:Rajdhani;font-size:1.5rem;font-weight:700;color:#3fb950;margin:0'>Résultat attendu : TRS {trs_act_lbl} → {trs_obj_lbl} après 10 mois</h3>""",unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown("<div class='sh'> Roadmap — Horizon 10 Tranches</div>",unsafe_allow_html=True)
        rm={"Action":["Maintenance Préventive","SMED Outils","5S Nettoyage","Poka-Yoke Démarrage","AMDEC Processus","SPC/Capabilité","Maintenance Autonome","Optimisation flux"],"Famille":["TD","TP","TP","TQ","TQ","TQ","TD","TP"],"Début":[1,1,2,1,2,3,3,4],"Fin":[4,3,10,4,5,10,10,10],"Impact":["+5%","+4%","+2%","+3%","+2%","+2%","+3%","+2%"]}
        rdf2=pd.DataFrame(rm); fam_c={"TD":"#f85149","TP":"#d29922","TQ":"#3fb950"}
        fig_rm=go.Figure(); shown=set()
        for _,row in rdf2.iterrows():
            c=fam_c.get(row["Famille"],"#58a6ff"); sl=row["Famille"] not in shown; shown.add(row["Famille"])
            fig_rm.add_trace(go.Bar(x=[row["Fin"]-row["Début"]+1],y=[row["Action"]],base=[row["Début"]-1],orientation="h",marker_color=c,marker_line_color="rgba(0,0,0,0)",name=row["Famille"],showlegend=sl,text=f" {row['Impact']}",textposition="inside",textfont=dict(color="white",size=10)))
        fig_rm.update_layout(height=270,**bl(),barmode="overlay",xaxis=dict(**ax(),tickmode="array",tickvals=list(range(1,11)),ticktext=[f"T{i}" for i in range(1,11)]),yaxis=ax())
        st.plotly_chart(fig_rm,use_container_width=True)

    elif sel_tab==" Gains & Production":
        sel_dept_g=st.selectbox(" Département",["Tous"]+list(DEPT_COLORS.keys()),key="final_dept_gains")
        depts_show=["Découpe","Usinage","Peinture"] if sel_dept_g=="Tous" else [sel_dept_g]
        icons={"Découpe","Usinage","Peinture"}
        for dept in depts_show:
            dco=DEPT_COLORS[dept]; act=actuals[dept]; tgt=TARGETS[dept]; kpis=["TD","TP","TQ","TRS"]
            st.markdown(f"<div class='sh' style='color:{dco}'>{icons[dept]} {dept}</div>",unsafe_allow_html=True)
            ann_cols=st.columns(4)
            for i,kpi in enumerate(kpis):
                a=act[kpi]; t=tgt[kpi]; delta=t-a
                with ann_cols[i]:
                    st.markdown(f"""<div style='text-align:center;padding:4px 0'>
<div style='color:#8b949e;font-size:0.82rem'>{a:.1f}%</div>
<div style='color:{dco};font-size:0.9rem;font-weight:700'>↑ +{delta:.1f}pts</div>
<div style='color:#3fb950;font-family:Rajdhani;font-size:1.2rem;font-weight:700'>{t:.1f}%</div>
<div style='color:#8b949e;font-size:0.7rem;text-transform:uppercase'>{kpi}</div></div>""",unsafe_allow_html=True)
            n_t=10
            trs_ev=[act["TRS"]+(tgt["TRS"]-act["TRS"])*i/(n_t-1) for i in range(n_t)]
            td_ev=[act["TD"]+(tgt["TD"]-act["TD"])*i/(n_t-1) for i in range(n_t)]
            tq_ev=[act["TQ"]+(tgt["TQ"]-act["TQ"])*i/(n_t-1) for i in range(n_t)]
            tp_ev=[act["TP"]+(tgt["TP"]-act["TP"])*i/(n_t-1) for i in range(n_t)]
            tranches=[f"T{i+1}" for i in range(n_t)]
            fig_evol=go.Figure()
            for kpi_,vals_,c_ in [("TRS",trs_ev,KPI_C["TRS"]),("TD",td_ev,KPI_C["TD"]),("TQ",tq_ev,KPI_C["TQ"]),("TP",tp_ev,KPI_C["TP"])]:
                fig_evol.add_trace(go.Scatter(x=tranches,y=vals_,name=kpi_,line=dict(color=c_,width=2.5),mode="lines+markers",marker=dict(size=7)))
            for kpi in kpis: fig_evol.add_hline(y=THRESHOLDS[kpi],line_dash="dot",line_color=THRESH_C[kpi],line_width=1,annotation_text=f"Cible {THRESHOLDS[kpi]}%",annotation_font=dict(color=THRESH_C[kpi],size=8))
            fig_evol.update_layout(height=265,**bl(),title=dict(text=f"Progression estimée T1→T10 — {dept}",font=dict(color=MUTED,size=11)),xaxis=ax(title="Tranche"),yaxis=ax(pct=True)); fig_evol.update_yaxes(range=[0,115]); st.plotly_chart(fig_evol,use_container_width=True)
            fig_ab=go.Figure()
            fig_ab.add_trace(go.Bar(name="Actuel",x=kpis,y=[act[k] for k in kpis],marker_color="#4a5568",marker_line_color="rgba(0,0,0,0)",text=[f"{act[k]:.1f}%" for k in kpis],textposition="outside",textfont=dict(color=TEXT,size=10)))
            fig_ab.add_trace(go.Bar(name="Objectif",x=kpis,y=[tgt[k] for k in kpis],marker_color=dco,marker_line_color="rgba(0,0,0,0)",text=[f"{tgt[k]:.1f}%" for k in kpis],textposition="outside",textfont=dict(color=TEXT,size=10)))
            for kpi in kpis: fig_ab.add_hline(y=THRESHOLDS[kpi],line_dash="dot",line_color=THRESH_C[kpi],line_width=1)
            fig_ab.update_layout(barmode="group",height=250,**bl(),title=dict(text=f"Actuel vs Objectif — {dept}",font=dict(color=MUTED,size=11)),xaxis=ax(),yaxis=ax(pct=True)); fig_ab.update_yaxes(range=[0,115]); st.plotly_chart(fig_ab,use_container_width=True)
            st.markdown("<hr style='border-color:#1e2430;margin:10px 0'>",unsafe_allow_html=True)
        st.markdown("<div class='sh'>Production Supplémentaire Estimée</div>",unsafe_allow_html=True)
        prod_cols=st.columns(len(depts_show)+1)
        for col_,dept in zip(prod_cols,depts_show):
            with col_:
                st.markdown(f"""<div style='background:#161b22;border:1px solid #21262d;border-radius:10px;padding:14px 18px;border-left:3px solid {DEPT_COLORS[dept]}'>
<div style='color:#8b949e;font-size:0.62rem;text-transform:uppercase;margin-bottom:3px'>Unités/jour — {dept}</div>
<div style='color:#3fb950;font-family:Rajdhani;font-size:2rem;font-weight:700'>+{EXTRA_PROD[dept]}</div></div>""",unsafe_allow_html=True)
        with prod_cols[-1]:
            total_u=sum(EXTRA_PROD[d] for d in depts_show)
            st.markdown(f"""<div style='background:linear-gradient(135deg,#0d1f0d,#1a2c1a);border:1px solid #3fb950;border-radius:10px;padding:14px 18px'>
<div style='color:#8b949e;font-size:0.62rem;text-transform:uppercase;margin-bottom:3px'>Total / jour</div>
<div style='color:#3fb950;font-family:Rajdhani;font-size:2rem;font-weight:700'>+{total_u}</div>
<div style='color:#8b949e;font-size:0.7rem'>soit +{total_u*250:,} / an</div></div>""",unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown("""<div style='background:linear-gradient(135deg,#161b22,#1c2128);border:1px solid #1f6feb;border-radius:10px;padding:14px 20px'>
<p style='color:#58a6ff;font-weight:700;margin:0 0 6px;font-family:Rajdhani;font-size:1rem'> Synthèse Globale des Gains</p>
<p style='color:#8b949e;font-size:0.78rem;margin:0;line-height:1.8'>
Actions priorité 1 et 2 → gain cumulé estimé <span style='color:#3fb950;font-weight:700'>+15% à +45%</span>.
<strong style='color:#58a6ff'>Découpe</strong> : maintenance préventive (TD = 63.9%).
<strong style='color:#3fb950'>Usinage</strong> : SMED + révision broches (TP = 41.9%).
<strong style='color:#d29922'>Peinture</strong> : contrôle qualité démarrage (TQ = 82.7%).
</p></div>""",unsafe_allow_html=True)
