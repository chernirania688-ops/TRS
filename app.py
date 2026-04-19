import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

st.set_page_config(page_title="TRS – Meubles inc.", layout="wide", initial_sidebar_state="expanded")

# ═══════════════════ CSS ═══════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#0d1117;color:#e6edf3;}

/* ── Sidebar ── */
[data-testid="stSidebar"]{background:#111318;border-right:1px solid #1e2430;}
[data-testid="stSidebar"] .stMarkdown h1{font-family:'Rajdhani';font-size:1.4rem;font-weight:700;color:#58a6ff;letter-spacing:3px;margin:0;}

/* ── Nav buttons custom ── */
[data-testid="stSidebar"] .stButton button{
    background:#161b22;border:1px solid #21262d;border-radius:8px;
    color:#8b949e;font-size:0.8rem;font-weight:500;text-align:left;
    padding:9px 14px;width:100%;transition:all 0.15s;margin:1px 0;
}
[data-testid="stSidebar"] .stButton button:hover{background:#1f2937;color:#e6edf3;border-color:#30363d;}

/* ── Tranche toggle buttons ── */
.stButton button[kind="primary"]{
    background:linear-gradient(135deg,#1f3a5f,#1a3a6e)!important;
    color:#58a6ff!important;border:1px solid #1f6feb!important;
    font-weight:700!important;font-size:0.8rem!important;
}
.stButton button[kind="secondary"]{
    background:#161b22!important;color:#484f58!important;
    border:1px solid #21262d!important;font-size:0.8rem!important;
}

/* ── KPI cards ── */
.kcard{background:linear-gradient(135deg,#161b22,#1c2128);border:1px solid #30363d;
    border-radius:14px;padding:18px 20px;position:relative;overflow:hidden;min-height:108px;
    box-shadow:0 2px 12px rgba(0,0,0,0.4);}
.kcard::before{content:'';position:absolute;top:0;left:0;width:4px;height:100%;border-radius:3px 0 0 3px;}
.kcard.blue::before{background:linear-gradient(180deg,#58a6ff,#1f6feb);}
.kcard.green::before{background:linear-gradient(180deg,#3fb950,#1a7f37);}
.kcard.orange::before{background:linear-gradient(180deg,#d29922,#b07d0a);}
.kcard.red::before{background:linear-gradient(180deg,#f85149,#b91c1c);}
.kcard.purple::before{background:linear-gradient(180deg,#a371f7,#7c3aed);}
.kcard.teal::before{background:linear-gradient(180deg,#39d353,#1a7f37);}
.kcard-label{font-size:0.62rem;color:#8b949e;text-transform:uppercase;letter-spacing:1.8px;font-weight:600;margin-bottom:6px;}
.kcard-val{font-family:'Rajdhani';font-size:2.1rem;font-weight:700;line-height:1;margin-bottom:4px;}
.kcard-sub{font-size:0.68rem;color:#8b949e;}

/* ── Section headers ── */
.sh{font-family:'Rajdhani';font-size:1rem;font-weight:700;color:#e6edf3;
    border-bottom:1px solid #21262d;padding-bottom:6px;margin-bottom:12px;letter-spacing:1.5px;
    display:flex;align-items:center;gap:8px;}
.sh::before{content:'';display:inline-block;width:3px;height:16px;border-radius:2px;
    background:linear-gradient(180deg,#58a6ff,#a371f7);flex-shrink:0;}

/* ── Solution cards ── */
.sol-card{background:#161b22;border:1px solid #21262d;border-radius:10px;
    padding:12px 16px;margin-bottom:8px;transition:border-color 0.15s;}
.sol-card:hover{border-color:#30363d;}

/* ── Badge ── */
.badge{display:inline-block;border-radius:5px;padding:2px 8px;font-size:0.64rem;font-weight:700;letter-spacing:0.5px;}

/* ── Info box ── */
.infobox{background:#161b22;border-left:3px solid #f0883e;border-radius:0 8px 8px 0;
    padding:10px 14px;margin-bottom:10px;font-size:0.78rem;color:#c9d1d9;line-height:1.7;}

/* ── Misc ── */
.tranche-label{font-size:0.62rem;color:#484f58;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px;}
div[data-testid="stHorizontalBlock"]{gap:8px;}
.stSelectbox>div>div{background:#161b22!important;border-color:#21262d!important;}
.stSelectbox label{color:#8b949e!important;font-size:0.74rem!important;}
[data-testid="stDataFrame"]{border:1px solid #21262d;border-radius:8px;overflow:hidden;}
</style>
""", unsafe_allow_html=True)

# ═══════════════════ CONSTANTS ═════════════════════════════════════════════════
DEPT_COLORS   = {"Découpe":"#58a6ff","Usinage":"#3fb950","Peinture":"#d29922"}
TEXT,MUTED,BG = "#e6edf3","#8b949e","#0d1117"
THRESHOLDS    = {"TRS":85,"TD":90,"TP":95,"TQ":98}
THRESH_COLORS = {"TRS":"#f85149","TD":"#f0883e","TP":"#d29922","TQ":"#3fb950"}
KPI_COLORS    = {"TRS":"#58a6ff","TD":"#3fb950","TQ":"#d29922","TP":"#a371f7"}
FILL_COLORS   = {"TRS":"rgba(88,166,255,0.08)","TD":"rgba(63,185,80,0.08)",
                 "TQ":"rgba(210,153,34,0.08)","TP":"rgba(163,113,247,0.08)"}
PROD_COLORS   = {"P1":"#58a6ff","P2":"#3fb950","P3":"#d29922","P4":"#a371f7"}
TARGETS = {"Découpe":{"TD":90,"TP":88,"TQ":98,"TRS":75},
           "Usinage": {"TD":92,"TP":88,"TQ":98,"TRS":79},
           "Peinture":{"TD":90,"TP":88,"TQ":95,"TRS":75}}
EXTRA_PROD = {"Découpe":380,"Usinage":520,"Peinture":290}

BL = dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
          font=dict(color=TEXT,family="Inter"),margin=dict(l=10,r=10,t=35,b=10),
          legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED,size=11)))

# ═══════════════════ AXIS HELPERS ══════════════════════════════════════════════
def ax(pct=False,title="",angle=0,dtick=None):
    d=dict(gridcolor="#1e2430",zerolinecolor="#1e2430",tickfont=dict(color=MUTED,size=10))
    if pct:   d["ticksuffix"]="%"
    if title: d["title"]=dict(text=title,font=dict(color=MUTED,size=10))
    if angle: d["tickangle"]=angle
    if dtick: d["dtick"]=dtick
    return d

def txax(vals):
    sv=sorted([int(v) for v in vals])
    return {**ax(),"tickmode":"array","tickvals":sv,"ticktext":[f"T{v}" for v in sv],
            "title":dict(text="Tranche",font=dict(color=MUTED,size=10))}

# ═══════════════════ DATA ══════════════════════════════════════════════════════
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

# ═══════════════════ UI HELPERS ════════════════════════════════════════════════
def kpi_card(label,value,color="blue",sub=""):
    cm={"blue":"#58a6ff","green":"#3fb950","orange":"#d29922",
        "red":"#f85149","purple":"#a371f7","teal":"#39d353"}
    c=cm.get(color,"#58a6ff")
    return (f'<div class="kcard {color}"><div class="kcard-label">{label}</div>'
            f'<div class="kcard-val" style="color:{c}">{value}</div>'
            f'<div class="kcard-sub">{sub}</div></div>')

def gauge(val,title,color="#58a6ff",thresh=85):
    fig=go.Figure(go.Indicator(mode="gauge+number",value=val,
        number={"suffix":"%","font":{"color":TEXT,"size":24,"family":"Rajdhani"}},
        title={"text":title,"font":{"color":MUTED,"size":11}},
        gauge={"axis":{"range":[0,100],"tickfont":{"color":MUTED,"size":8}},
               "bar":{"color":color},"bgcolor":"#161b22","borderwidth":0,
               "steps":[{"range":[0,60],"color":"#1c2128"},{"range":[60,thresh],"color":"#1e2820"},
                        {"range":[thresh,100],"color":"#1a2c1a"}],
               "threshold":{"line":{"color":"#f85149","width":2},"thickness":0.75,"value":thresh}}))
    fig.update_layout(height=180,**BL); return fig

def add_thresh(fig,kpis):
    for k in kpis:
        if k in THRESHOLDS:
            fig.add_hline(y=THRESHOLDS[k],line_dash="dash",line_color=THRESH_COLORS[k],line_width=1.4,
                          annotation_text=f"Seuil {k} {THRESHOLDS[k]}%",
                          annotation_position="top right",
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

def pbar_cfg():
    return {"TRS %":st.column_config.ProgressColumn("TRS %",min_value=0,max_value=100,format="%.2f%%"),
            "TD %": st.column_config.ProgressColumn("TD %", min_value=0,max_value=100,format="%.2f%%"),
            "TQ %": st.column_config.ProgressColumn("TQ %", min_value=0,max_value=100,format="%.2f%%"),
            "TP %": st.column_config.ProgressColumn("TP %", min_value=0,max_value=100,format="%.2f%%")}

# ═══════════════════ TRANCHE TOGGLE ═══════════════════════════════════════════
def tranche_toggle(key_prefix):
    st.markdown("<p class='tranche-label'>Sélection des Tranches</p>",unsafe_allow_html=True)
    for i in range(1,11):
        if f"{key_prefix}_{i}" not in st.session_state:
            st.session_state[f"{key_prefix}_{i}"]=True
    rc1,rc2,_=st.columns([1.2,1.2,9])
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

# ═══════════════════ SIDEBAR ═══════════════════════════════════════════════════
with st.sidebar:
    st.markdown("# 🏭 TRS")
    st.markdown("<p style='color:#484f58;font-size:0.68rem;letter-spacing:2px;margin-top:-4px'>MEUBLES INC.</p>",unsafe_allow_html=True)
    st.markdown("---")
    PAGES={"📊  Dashboard Global":"global","🪚  Dép. Découpe":"decoupe",
           "⚙️  Dép. Usinage":"usinage","🎨  Dép. Peinture":"peinture",
           "🔍  Source des Pertes":"pertes","🏆  Dashboard Final":"final"}
    if "page" not in st.session_state: st.session_state.page="global"
    for label,key in PAGES.items():
        is_active=st.session_state.page==key
        if is_active:
            st.markdown(f"<div style='background:linear-gradient(90deg,#1f3a5f,#1a2a4a);border:1px solid #1f6feb;border-radius:8px;padding:9px 14px;margin:1px 0;color:#58a6ff;font-size:0.8rem;font-weight:600'>{label}</div>",unsafe_allow_html=True)
        else:
            if st.button(label,key=f"nav_{key}",use_container_width=True):
                st.session_state.page=key; st.rerun()
    st.markdown("---")
    st.markdown("<p style='color:#484f58;font-size:0.6rem;text-transform:uppercase;letter-spacing:2px;margin-bottom:6px'>Données</p>",unsafe_allow_html=True)
    st.markdown("<p style='color:#8b949e;font-size:0.74rem;margin:2px 0'>📅 250 jours · 10 tranches × 25 j</p>",unsafe_allow_html=True)
    st.markdown("<p style='color:#8b949e;font-size:0.74rem;margin:2px 0'>📦 P1 P2 P3 P4 · 3 départements</p>",unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<p style='color:#484f58;font-size:0.6rem;text-transform:uppercase;letter-spacing:2px;margin-bottom:6px'>Seuils TPM</p>",unsafe_allow_html=True)
    for k,v in THRESHOLDS.items():
        st.markdown(f"<p style='color:{THRESH_COLORS[k]};font-size:0.74rem;margin:2px 0'>● {k} ≥ {v}%</p>",unsafe_allow_html=True)

page=st.session_state.page

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE HEADER helper
# ═══════════════════════════════════════════════════════════════════════════════
def page_header(icon,title,subtitle):
    st.markdown(f"""<div style='margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid #21262d'>
<h1 style='font-family:Rajdhani;font-size:2.1rem;color:#e6edf3;letter-spacing:2px;margin:0;font-weight:700'>
{icon} {title}</h1>
<p style='color:#8b949e;font-size:0.8rem;margin:4px 0 0'>{subtitle}</p>
</div>""",unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if page=="global":
    page_header("📊","DASHBOARD GLOBAL","Vue d'ensemble — 10 tranches × 25 jours · 3 départements · 4 produits")

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
    with k1: st.markdown(kpi_card("TRS GLOBAL",f"{trs_m:.1f}%","blue" if trs_m>=85 else "red",f"{flag(trs_m,85)} Seuil ≥ 85%"),unsafe_allow_html=True)
    with k2: st.markdown(kpi_card("DISPONIBILITÉ TD",f"{td_m:.1f}%","green" if td_m>=90 else "red",f"{flag(td_m,90)} Seuil ≥ 90%"),unsafe_allow_html=True)
    with k3: st.markdown(kpi_card("QUALITÉ TQ",f"{tq_m:.1f}%","teal" if tq_m>=98 else "red",f"{flag(tq_m,98)} Seuil ≥ 98%"),unsafe_allow_html=True)
    with k4: st.markdown(kpi_card("PERFORMANCE TP",f"{tp_m:.1f}%","orange" if tp_m>=95 else "red",f"{flag(tp_m,95)} Seuil ≥ 95%"),unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)

    # ── Évolution KPIs par tranche ──
    st.markdown("<div class='sh'>Évolution TRS · TD · TQ · TP par Tranche</div>",unsafe_allow_html=True)
    by_t=df.groupby("Tranche")[["TRS","TD","TQ","TP"]].mean().reset_index().sort_values("Tranche")
    fig_ev=go.Figure()
    for kpi,c in KPI_COLORS.items():
        fig_ev.add_trace(go.Scatter(x=by_t["Tranche"],y=by_t[kpi]*100,name=kpi,
            line=dict(color=c,width=2.5),mode="lines+markers",marker=dict(size=7)))
    add_thresh(fig_ev,["TRS","TD","TQ","TP"])
    fig_ev.update_layout(height=300,**BL,xaxis=txax(by_t["Tranche"]),yaxis=ax(pct=True))
    fig_ev.update_yaxes(range=[0,110]); st.plotly_chart(fig_ev,use_container_width=True)

    # ── Comparaison 3 depts vs norme NFE (image 1) ──
    st.markdown("<div class='sh'>Comparaison TRS — 3 Départements vs Norme NFE</div>",unsafe_allow_html=True)
    dept_kpis={}
    comb_all=pd.concat(dfs.values(),ignore_index=True)
    comb_f=comb_all[comb_all["Tranche"].isin(sel_t)]
    if sel_prod!="Tous": comb_f=comb_f[comb_f["Produit"]==sel_prod]
    for dept in ["Découpe","Usinage","Peinture"]:
        sub=comb_f[comb_f["Département"]==dept]
        if sub.empty: dept_kpis[dept]={"TD":0,"TP":0,"TQ":0,"TRS":0}
        else: dept_kpis[dept]={k:sub[k].mean()*100 for k in ["TD","TP","TQ","TRS"]}

    # 4 mini KPI cards per dept showing TRS
    mc1,mc2,mc3=st.columns(3)
    for col_,dept in zip([mc1,mc2,mc3],["Découpe","Usinage","Peinture"]):
        with col_:
            v=dept_kpis[dept]["TRS"]; dc=DEPT_COLORS[dept]
            status="✅ Au-dessus de la norme" if v>=85 else "⚠️ Sous norme"
            sc="green" if v>=85 else "red"
            st.markdown(f"""<div style='background:#161b22;border:1px solid #21262d;border-radius:12px;padding:14px 18px;border-left:4px solid {dc}'>
<div style='font-family:Rajdhani;font-size:1.5rem;font-weight:700;color:{dc}'>{v:.1f}%</div>
<div style='font-size:0.7rem;color:#8b949e;margin:2px 0'>TRS — {dept}</div>
<div style='font-size:0.68rem;color:#8b949e'>Norme ≥ 85%</div>
<div style='font-size:0.68rem;color:{"#3fb950" if v>=85 else "#f85149"};font-weight:600;margin-top:3px'>{"✅ Conforme" if v>=85 else "⚠️ Sous norme"}</div>
</div>""",unsafe_allow_html=True)

    # Grouped bar: TD TP TQ TRS par département avec norme
    kpis_ord=["TD","TP","TQ","TRS"]
    fig_cmp=go.Figure()
    dept_bar_colors={"Découpe":"#58a6ff","Usinage":"#3fb950","Peinture":"#d29922"}
    for dept,dc in dept_bar_colors.items():
        vals=[dept_kpis[dept][k] for k in kpis_ord]
        fig_cmp.add_trace(go.Bar(name=dept,x=kpis_ord,y=vals,marker_color=dc,
            marker_line_color="rgba(0,0,0,0)",
            text=[f"{v:.1f}%" for v in vals],textposition="outside",textfont=dict(color=TEXT,size=9)))
    # Norme bars (light grey reference)
    norme_vals=[THRESHOLDS[k] for k in kpis_ord]
    fig_cmp.add_trace(go.Bar(name="Norme",x=kpis_ord,y=norme_vals,
        marker_color="rgba(110,118,129,0.3)",marker_line_color="rgba(110,118,129,0.5)",
        marker_line_width=1,text=[f"{v}%" for v in norme_vals],
        textposition="outside",textfont=dict(color=MUTED,size=9)))
    fig_cmp.update_layout(barmode="group",height=320,**BL,xaxis=ax(),yaxis=ax(pct=True))
    fig_cmp.update_layout(title=dict(text="Comparaison TRS — 3 départements vs norme NFE",font=dict(color=MUTED,size=11)))
    fig_cmp.update_yaxes(range=[0,115]); st.plotly_chart(fig_cmp,use_container_width=True)

    # ── TRS journalier J1-250, 3 depts ──
    st.markdown("<div class='sh'>TRS Journalier J1→J250 — 3 Départements</div>",unsafe_allow_html=True)
    fig_jg=go.Figure()
    pal_bg=["rgba(88,166,255,0.04)","rgba(63,185,80,0.04)","rgba(210,153,34,0.04)",
            "rgba(163,113,247,0.04)","rgba(248,81,73,0.04)"]
    for t in range(1,11):
        j0=(t-1)*25+1; j1=t*25
        fig_jg.add_vrect(x0=j0,x1=j1,fillcolor=pal_bg[(t-1)%5],layer="below",line_width=0)
        fig_jg.add_annotation(x=(j0+j1)/2,y=107,text=f"T{t}",showarrow=False,font=dict(color=MUTED,size=8),yref="y")
    for dept,dc in DEPT_COLORS.items():
        sub_d=comb_f[comb_f["Département"]==dept].groupby("Journée")["TRS"].mean().reset_index().sort_values("Journée")
        if sub_d.empty: continue
        fig_jg.add_trace(go.Scatter(x=sub_d["Journée"],y=sub_d["TRS"]*100,name=dept,
            line=dict(color=dc,width=1.5),mode="lines"))
    fig_jg.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.5,
                     annotation_text="Seuil 85%",annotation_font=dict(color="#f85149",size=9))
    fig_jg.update_layout(height=260,**BL,xaxis=ax(title="Journée (1–250)"),yaxis=ax(pct=True))
    fig_jg.update_yaxes(range=[0,110]); st.plotly_chart(fig_jg,use_container_width=True)

    # ── TRS par dept + produit ──
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
        fig_dt.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.2)
        fig_dt.update_layout(height=250,**BL,xaxis=txax(by_dt["Tranche"]),yaxis=ax(pct=True))
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
        fig_pt.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.2)
        fig_pt.update_layout(height=250,**BL,xaxis=txax(by_pt["Tranche"]),yaxis=ax(pct=True))
        fig_pt.update_yaxes(range=[0,110]); st.plotly_chart(fig_pt,use_container_width=True)

    # ── Heatmap + tableau ──
    st.markdown("<div class='sh'>Heatmap TRS — Département × Tranche</div>",unsafe_allow_html=True)
    piv=(df.groupby(["Département","Tranche"])["TRS"].mean().unstack().sort_index()*100).round(1)
    piv=piv.reindex(sorted(piv.columns),axis=1)
    fig_hm=go.Figure(go.Heatmap(z=piv.values,x=[f"T{int(c)}" for c in sorted(piv.columns)],y=piv.index.tolist(),
        colorscale=[[0,"#1c2128"],[0.5,"#d29922"],[1,"#3fb950"]],zmin=0,zmax=100,
        text=piv.values.astype(str),texttemplate="%{text}%",textfont=dict(size=10,color="white"),
        colorbar=dict(ticksuffix="%",tickfont=dict(color=MUTED))))
    fig_hm.update_layout(height=185,**BL,xaxis=ax(),yaxis=ax())
    st.plotly_chart(fig_hm,use_container_width=True)

    st.markdown("<div class='sh'>📋 Tableau Récapitulatif par Tranche</div>",unsafe_allow_html=True)
    st.dataframe(recap_table(df),use_container_width=True,hide_index=True,column_config=pbar_cfg())

# ═══════════════════════════════════════════════════════════════════════════════
# DÉPARTEMENT (générique)
# ═══════════════════════════════════════════════════════════════════════════════
def dept_page(dept_name):
    color=DEPT_COLORS[dept_name]
    icons={"Découpe":"🪚","Usinage":"⚙️","Peinture":"🎨"}
    page_header(icons[dept_name],f"DÉPARTEMENT {dept_name.upper()}","10 tranches × 25 jours — filtrage interactif — seuils TPM")

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

    cg1,cg2,cg3,cg4=st.columns(4)
    with cg1: st.plotly_chart(gauge(trs_m,"TRS",color,85),use_container_width=True,key=f"g1_{dept_name}")
    with cg2: st.plotly_chart(gauge(td_m,"TD","#58a6ff",90),use_container_width=True,key=f"g2_{dept_name}")
    with cg3: st.plotly_chart(gauge(tq_m,"TQ","#3fb950",98),use_container_width=True,key=f"g3_{dept_name}")
    with cg4: st.plotly_chart(gauge(tp_m,"TP","#d29922",95),use_container_width=True,key=f"g4_{dept_name}")

    # Courbe combinée
    st.markdown("<div class='sh'>Évolution TRS · TD · TQ · TP par Tranche</div>",unsafe_allow_html=True)
    by_t=df.groupby("Tranche")[["TRS","TD","TQ","TP"]].mean().reset_index().sort_values("Tranche")
    fig_t=go.Figure()
    for kpi,c in KPI_COLORS.items():
        fig_t.add_trace(go.Scatter(x=by_t["Tranche"],y=by_t[kpi]*100,name=kpi,
            line=dict(color=c,width=2.5),mode="lines+markers",marker=dict(size=7)))
    add_thresh(fig_t,["TRS","TD","TQ","TP"])
    fig_t.update_layout(height=295,**BL,xaxis=txax(by_t["Tranche"]),yaxis=ax(pct=True))
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
            fig_k.update_layout(height=195,**BL,xaxis=txax(by_t["Tranche"]),yaxis=ax(pct=True))
            fig_k.update_layout(title=dict(text=f"Évolution {kpi}",font=dict(color=TEXT,size=11)))
            fig_k.update_yaxes(range=[0,110])
            st.plotly_chart(fig_k,use_container_width=True,key=f"ind_{kpi}_{dept_name}")

    # Bâtonnets TRS·TD·TQ·TP par tranche
    st.markdown("<div class='sh'>TRS · TD · TQ · TP par Tranche — Vue bâtonnets</div>",unsafe_allow_html=True)
    t_labels=[f"T{int(t)}" for t in by_t["Tranche"]]
    fig_j=go.Figure()
    for kpi,c in KPI_COLORS.items():
        yvals=by_t[kpi]*100
        fig_j.add_trace(go.Bar(name=kpi,x=t_labels,y=yvals,marker_color=c,
            marker_line_color="rgba(0,0,0,0)",
            text=[f"{v:.1f}%" for v in yvals],textposition="outside",textfont=dict(color=TEXT,size=8)))
    for kpi in ["TRS","TD","TQ","TP"]:
        fig_j.add_hline(y=THRESHOLDS[kpi],line_dash="dash",line_color=THRESH_COLORS[kpi],line_width=1.2,
                        annotation_text=f"Seuil {kpi} {THRESHOLDS[kpi]}%",
                        annotation_position="top right",annotation_font=dict(color=THRESH_COLORS[kpi],size=8))
    fig_j.update_layout(barmode="group",height=300,**BL,xaxis=ax(title="Tranche"),yaxis=ax(pct=True))
    fig_j.update_yaxes(range=[0,115]); st.plotly_chart(fig_j,use_container_width=True)

    # Analyse par produit
    st.markdown("<div class='sh'>Analyse par Produit — TRS · TD · TQ · TP & Pertes</div>",unsafe_allow_html=True)
    df_all_t=dfs[dept_name][dfs[dept_name]["Tranche"].isin(sel_t)]
    by_p=df_all_t.groupby("Produit").agg(
        TRS=("TRS","mean"),TD=("TD","mean"),TQ=("TQ","mean"),TP=("TP","mean"),
        Quantité=("Quantité","sum"),Panne=("Panne","sum"),
        Arrêts_mineurs=("Arrêts_mineurs","sum"),
        Rejet_qualité=("Rejet_qualité","sum"),
        Rejet_Démarrage=("Rejet_Démarrage",lambda x:x.fillna(0).sum())
    ).reset_index()
    prods=[p for p in ["P1","P2","P3","P4"] if p in by_p["Produit"].values]

    fig_pg=go.Figure()
    for kpi,c in KPI_COLORS.items():
        vals=[float(by_p[by_p["Produit"]==p][kpi].values[0])*100 if p in by_p["Produit"].values else 0 for p in prods]
        fig_pg.add_trace(go.Bar(name=kpi,x=prods,y=vals,marker_color=c,
            text=[f"{v:.1f}%" for v in vals],textposition="outside",textfont=dict(color=TEXT,size=9)))
    for kpi in ["TRS","TD","TQ","TP"]:
        fig_pg.add_hline(y=THRESHOLDS[kpi],line_dash="dash",line_color=THRESH_COLORS[kpi],line_width=1)
    fig_pg.update_layout(barmode="group",height=290,**BL,xaxis=ax(title="Produit"),yaxis=ax(pct=True))
    fig_pg.update_layout(title=dict(text="KPIs par Produit",font=dict(color=TEXT,size=12)))
    fig_pg.update_yaxes(range=[0,115]); st.plotly_chart(fig_pg,use_container_width=True)

    cl_r,cr_r=st.columns(2)
    with cl_r:
        st.markdown("<div class='sh'>Pertes par Produit</div>",unsafe_allow_html=True)
        fig_pp=go.Figure()
        for col_n,lbl,c in [("Panne","Pannes (min)","#f85149"),("Arrêts_mineurs","Arrêts mineurs","#d29922"),
                              ("Rejet_qualité","Rejet qualité","#3fb950"),("Rejet_Démarrage","Rejet démarrage","#a371f7")]:
            vals=[float(by_p[by_p["Produit"]==p][col_n].values[0]) if p in by_p["Produit"].values else 0 for p in prods]
            fig_pp.add_trace(go.Bar(name=lbl,x=prods,y=vals,marker_color=c,
                text=[f"{int(v)}" for v in vals],textposition="outside",textfont=dict(color=TEXT,size=9)))
        fig_pp.update_layout(barmode="group",height=260,**BL,xaxis=ax(title="Produit"),yaxis=ax())
        st.plotly_chart(fig_pp,use_container_width=True)
    with cr_r:
        st.markdown("<div class='sh'>🏆 Diagnostic — Produits classés</div>",unsafe_allow_html=True)
        scores=[]
        for p in prods:
            row=by_p[by_p["Produit"]==p]
            trs_p=float(row["TRS"].values[0])*100; td_p=float(row["TD"].values[0])*100
            tq_p=float(row["TQ"].values[0])*100;   tp_p=float(row["TP"].values[0])*100
            gap=max(0,85-trs_p)+max(0,90-td_p)+max(0,98-tq_p)+max(0,95-tp_p)
            scores.append({"Produit":p,"TRS %":round(trs_p,1),"TD %":round(td_p,1),
                           "TQ %":round(tq_p,1),"TP %":round(tp_p,1),
                           "Écart seuils":round(gap,1),
                           "Pannes":int(float(row["Panne"].values[0])),
                           "Rejets":int(float(row["Rejet_qualité"].values[0])+float(row["Rejet_Démarrage"].values[0]))})
        sdf=pd.DataFrame(scores).sort_values("Écart seuils",ascending=False)
        if not sdf.empty:
            w=sdf.iloc[0]; b=sdf.iloc[-1]
            st.markdown(f"""<div style='background:#1a1010;border:1px solid #f85149;border-radius:8px;padding:10px 14px;margin-bottom:8px'>
<p style='color:#f85149;font-weight:700;margin:0 0 2px;font-family:Rajdhani;font-size:1rem'>⚠️ Plus critique : {w["Produit"]} — Écart seuils : {w["Écart seuils"]}%</p>
<p style='color:#c9d1d9;font-size:0.76rem;margin:0'>TRS={w["TRS %"]}% · TD={w["TD %"]}% · TQ={w["TQ %"]}% · TP={w["TP %"]}%</p>
</div>""",unsafe_allow_html=True)
            st.markdown(f"""<div style='background:#0d1a0d;border:1px solid #3fb950;border-radius:8px;padding:10px 14px;margin-bottom:8px'>
<p style='color:#3fb950;font-weight:700;margin:0 0 2px;font-family:Rajdhani;font-size:1rem'>✅ Meilleur : {b["Produit"]} — Écart seuils : {b["Écart seuils"]}%</p>
<p style='color:#c9d1d9;font-size:0.76rem;margin:0'>TRS={b["TRS %"]}% · TD={b["TD %"]}% · TQ={b["TQ %"]}% · TP={b["TP %"]}%</p>
</div>""",unsafe_allow_html=True)
        pbar4={"TRS %":st.column_config.ProgressColumn("TRS %",min_value=0,max_value=100,format="%.1f%%"),
               "TD %": st.column_config.ProgressColumn("TD %", min_value=0,max_value=100,format="%.1f%%"),
               "TQ %": st.column_config.ProgressColumn("TQ %", min_value=0,max_value=100,format="%.1f%%"),
               "TP %": st.column_config.ProgressColumn("TP %", min_value=0,max_value=100,format="%.1f%%")}
        st.dataframe(sdf,use_container_width=True,hide_index=True,column_config=pbar4)

    st.markdown("<div class='sh'>📋 Tableau par Tranche</div>",unsafe_allow_html=True)
    st.dataframe(recap_table(df),use_container_width=True,hide_index=True,column_config=pbar_cfg())

if page=="decoupe":  dept_page("Découpe")
elif page=="usinage": dept_page("Usinage")
elif page=="peinture":dept_page("Peinture")

# ═══════════════════════════════════════════════════════════════════════════════
# SOURCE DES PERTES
# ═══════════════════════════════════════════════════════════════════════════════
elif page=="pertes":
    page_header("🔍","SOURCE DES PERTES","Analyse causale — 3 familles · 11 sources · démarche TPM")

    with st.expander("📖 Fondement méthodologique — Démarche TPM",expanded=False):
        st.markdown("""<div style='color:#c9d1d9;font-size:0.82rem;line-height:1.9'>
<p>La démarche <strong>TPM (Total Productive Maintenance)</strong> décompose l'inefficacité selon :</p>
<p style='text-align:center;font-family:Rajdhani;font-size:1.3rem;color:#58a6ff;letter-spacing:2px'>TRS = TD × TQ × TP</p>
<p>Chaque composante est dégradée par des <strong>familles de pertes</strong> issues des enregistrements de production.</p>
<hr style='border-color:#21262d'>
<p><span style='color:#f85149'>🔴</span> <strong>Pertes DISPONIBILITÉ (TD)</strong> — Pannes · Remplacement préventif</p>
<p><span style='color:#d29922'>🟡</span> <strong>Pertes PERFORMANCE (TP)</strong> — Arrêts mineurs · Nettoyage · Réglage dérive · Inspection · Changement outil · Déplacement · Lubrification</p>
<p><span style='color:#3fb950'>🟢</span> <strong>Pertes QUALITÉ (TQ)</strong> — Rejet démarrage · Rejet qualité</p>
</div>""",unsafe_allow_html=True)

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
        st.markdown("<div class='sh'>Diagramme de Pareto des Pertes</div>",unsafe_allow_html=True)
        st.markdown("""<div class='infobox'><strong style='color:#f0883e'>À quoi sert le Pareto ?</strong>
Il applique la <strong>règle 80/20</strong> : 80% des pertes proviennent de 20% des causes.
Les sources sont triées de la plus impactante à gauche. La <strong>courbe orange</strong> montre le cumul en %.
<strong>Concentrez les actions sur les barres à gauche de la ligne 80%</strong> — c'est là que l'effort est le plus rentable.</div>""",unsafe_allow_html=True)
        sp=dict(sorted(pv.items(),key=lambda x:x[1],reverse=True))
        labels=list(sp.keys()); vals=list(sp.values())
        cumul=np.cumsum(vals)/max(sum(vals),1)*100
        bar_c=[pdef[l][2] for l in labels]
        fig_par=make_subplots(specs=[[{"secondary_y":True}]])
        fig_par.add_trace(go.Bar(x=labels,y=vals,name="Total",marker_color=bar_c,marker_line_color="rgba(0,0,0,0)"),secondary_y=False)
        fig_par.add_trace(go.Scatter(x=labels,y=cumul,name="Cumulé %",line=dict(color="#f0883e",width=2),mode="lines+markers"),secondary_y=True)
        fig_par.add_hline(y=80,line_dash="dot",line_color="#8b949e",line_width=1,
                          annotation_text="80%",annotation_font=dict(color=MUTED,size=9),secondary_y=True)
        fig_par.update_layout(height=310,**BL,xaxis=ax(angle=30),yaxis=ax(),
                              yaxis2=dict(ticksuffix="%",tickfont=dict(color=MUTED,size=10),gridcolor="#1e2430"))
        st.plotly_chart(fig_par,use_container_width=True)

    with cr2:
        st.markdown("<div class='sh'>Répartition — Anneau TPM (6 Grandes Pertes)</div>",unsafe_allow_html=True)
        # 6 grandes pertes TPM avec pourcentages (comme image 2)
        total_all=td_l+tp_l+tq_l if (td_l+tp_l+tq_l)>0 else 1
        # Group into 6 TPM categories
        vitesse_reduite=pv["Arrêts_mineurs"] if "Arrêts_mineurs" in pv else pv.get("Arrêts mineurs",0)
        pannes_machines=pv["Pannes"]
        rejets_qual=tq_l
        arrets_min=pv.get("Nettoyage",0)+pv.get("Réglage dérive",0)+pv.get("Changement outil",0)
        demarrages=pv.get("Rejet démarrage",0)
        nettoyage_reglage=pv.get("Lubrification",0)+pv.get("Déplacement",0)+pv.get("Inspection",0)

        donut_vals=[vitesse_reduite,pannes_machines,rejets_qual,arrets_min,demarrages,nettoyage_reglage]
        donut_labels=["Vitesse réduite (TP)","Pannes machines","Rejets qualité",
                      "Arrêts mineurs","Démarrages","Nettoyage/Réglage"]
        donut_colors=["#58a6ff","#f85149","#3fb950","#d29922","#a371f7","#39d353"]
        total_d=sum(donut_vals) if sum(donut_vals)>0 else 1
        pcts=[v/total_d*100 for v in donut_vals]

        fig_do=go.Figure(go.Pie(
            labels=[f"{l} {p:.0f}%" for l,p in zip(donut_labels,pcts)],
            values=donut_vals,hole=0.52,
            marker=dict(colors=donut_colors,line=dict(color=BG,width=2)),
            textfont=dict(color="white",size=11),
            textposition="inside",textinfo="percent"))
        fig_do.update_layout(height=310,**BL,showlegend=True)
        fig_do.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED,size=10),
                        orientation="v",x=1.02,y=0.5))
        st.plotly_chart(fig_do,use_container_width=True)

    # Évolution pertes par tranche
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
    fig_ep.update_layout(height=255,**BL,xaxis=txax(by_tp["Tranche"]),yaxis=ax(title="Total (min / pcs)"))
    st.plotly_chart(fig_ep,use_container_width=True)

    st.markdown("<div class='sh'>📋 Tableau par Tranche</div>",unsafe_allow_html=True)
    tbl_r=[]
    for t in sorted(df_p["Tranche"].unique()):
        s=df_p[df_p["Tranche"]==t]
        tbl_r.append({"Tranche":f"T{int(t)}","Jours":f"{(int(t)-1)*25+1}–{int(t)*25}",
                      "TRS %":round(s["TRS"].mean()*100,2),"TD %":round(s["TD"].mean()*100,2),
                      "TQ %":round(s["TQ"].mean()*100,2),"TP %":round(s["TP"].mean()*100,2),
                      "Pannes min":int(s["Panne"].sum()),"Rejet qualité":int(s["Rejet_qualité"].sum())})
    st.dataframe(pd.DataFrame(tbl_r),use_container_width=True,hide_index=True,column_config=pbar_cfg())

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD FINAL — PLAN D'ACTION + GAINS
# ═══════════════════════════════════════════════════════════════════════════════
elif page=="final":
    page_header("🏆","DASHBOARD FINAL","Plan d'Action · Gains par département · Production supplémentaire estimée")

    actuals={}
    for dept in ["Découpe","Usinage","Peinture"]:
        d=dfs[dept]
        actuals[dept]={"TD":d["TD"].mean()*100,"TP":d["TP"].mean()*100,
                       "TQ":d["TQ"].mean()*100,"TRS":d["TRS"].mean()*100}

    # ═══ 1. PLAN D'ACTION ═══════════════════════════════════════════════════
    st.markdown("<h3 style='font-family:Rajdhani;font-size:1.5rem;color:#58a6ff;letter-spacing:1px;margin-bottom:16px'>🛠️ Plan d'Action — Actions concrètes</h3>",unsafe_allow_html=True)

    def sol_block(titre,prio,desc,outil,bg,bc,pc):
        return f"""<div class='sol-card' style='border-left:3px solid {bc}'>
<div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap'>
  <span style='font-weight:600;color:#e6edf3;font-size:0.87rem'>{titre}</span>
  <span class='badge' style='background:{bg};color:{pc};border:1px solid {pc}'>{prio}</span>
  <span class='badge' style='background:#1c2128;color:#8b949e;border:1px solid #21262d'>{outil}</span>
</div>
<p style='color:#8b949e;font-size:0.78rem;margin:0;line-height:1.6'>{desc}</p>
</div>"""

    ca,cb,cc=st.columns(3)
    with ca:
        st.markdown("<div class='sh' style='color:#f85149'>🔴 TD — Disponibilité ≥ 90%</div>",unsafe_allow_html=True)
        for t,p,d,o in [
            ("Maintenance Préventive","Priorité 1","Plan basé sur les fréquences de pannes (MTBF). Remplacement avant défaillance. Objectif : -40% pannes.","GMAO"),
            ("Analyse MTBF / MTTR","Priorité 1","Calculer le temps moyen entre pannes et de réparation. Prioriser les équipements critiques.","Analyse"),
            ("Maintenance Autonome","Priorité 2","Former les opérateurs aux contrôles de base : nettoyage, lubrification, inspection visuelle.","5S / TPM"),
            ("Standard Redémarrage","Priorité 3","Fiches standardisées. Viser MTTR < 30 min pour les pannes courantes.","Standard Work"),
        ]:
            pc_="#f85149" if "1" in p else "#d29922" if "2" in p else "#8b949e"
            st.markdown(sol_block(t,p,d,o,"#2d1515","#f85149",pc_),unsafe_allow_html=True)
    with cb:
        st.markdown("<div class='sh' style='color:#d29922'>🟡 TP — Performance ≥ 95%</div>",unsafe_allow_html=True)
        for t,p,d,o in [
            ("SMED — Changements outils","Priorité 1","Convertir opérations internes en externes. Objectif : -50% du temps de changement.","SMED / Lean"),
            ("Élimination Arrêts Mineurs","Priorité 1","Analyser causes racines (OPL). Capteurs de détection précoce.","OPL / Capteurs"),
            ("5S & Nettoyage Standard","Priorité 2","Standardiser les durées de nettoyage. Intégrer dans la maintenance autonome. Réduction : -30%.","5S"),
            ("Optimisation flux","Priorité 2","Spaghetti diagram des déplacements. Réorganiser l'implantation.","VSM / Layout"),
            ("SPC — Dérive machine","Priorité 3","Détecter les dérives avant réglage curatif. Objectif : -60% réglages.","SPC"),
        ]:
            pc_="#f85149" if "1" in p else "#d29922" if "2" in p else "#8b949e"
            st.markdown(sol_block(t,p,d,o,"#2d2010","#d29922",pc_),unsafe_allow_html=True)
    with cc:
        st.markdown("<div class='sh' style='color:#3fb950'>🟢 TQ — Qualité ≥ 98%</div>",unsafe_allow_html=True)
        for t,p,d,o in [
            ("Poka-Yoke Démarrage","Priorité 1","Paramètres standardisés par produit. Détrompeurs pour la répétabilité. Objectif : 0 rejet après J+3.","Poka-Yoke"),
            ("AMDEC Processus","Priorité 1","Identifier les étapes critiques par IPR. Découpe et Peinture prioritaires.","AMDEC / RPN"),
            ("Autocontrôle Opérateur","Priorité 2","Standards photo, critères visuels. Objectif : 100% détection au poste.","Autocontrôle"),
            ("Capabilité Cp/Cpk","Priorité 2","Calculer Cp et Cpk. Cpk < 1,33 → processus non capable. Réglages via SPC.","SPC"),
        ]:
            pc_="#f85149" if "1" in p else "#d29922" if "2" in p else "#8b949e"
            st.markdown(sol_block(t,p,d,o,"#0d1f0d","#3fb950",pc_),unsafe_allow_html=True)

    # Roadmap
    st.markdown("---")
    st.markdown("<div class='sh'>📅 Roadmap — Horizon 10 Tranches</div>",unsafe_allow_html=True)
    rm={"Action":["Maintenance Préventive","SMED Outils","5S Nettoyage","Poka-Yoke Démarrage",
                  "AMDEC Processus","SPC / Capabilité","Maintenance Autonome","Optimisation flux"],
        "Famille":["TD","TP","TP","TQ","TQ","TQ","TD","TP"],
        "Début":[1,1,2,1,2,3,3,4],"Fin":[4,3,10,4,5,10,10,10],
        "Impact":["+5%","+4%","+2%","+3%","+2%","+2%","+3%","+2%"]}
    rdf2=pd.DataFrame(rm); fam_c={"TD":"#f85149","TP":"#d29922","TQ":"#3fb950"}
    fig_rm=go.Figure(); shown=set()
    for _,row in rdf2.iterrows():
        c=fam_c.get(row["Famille"],"#58a6ff"); sl=row["Famille"] not in shown; shown.add(row["Famille"])
        fig_rm.add_trace(go.Bar(x=[row["Fin"]-row["Début"]+1],y=[row["Action"]],base=[row["Début"]-1],
            orientation="h",marker_color=c,marker_line_color="rgba(0,0,0,0)",name=row["Famille"],showlegend=sl,
            text=f" {row['Impact']}",textposition="inside",textfont=dict(color="white",size=10)))
    fig_rm.update_layout(height=280,**BL,barmode="overlay",
        xaxis=dict(**ax(),title=dict(text="Tranches",font=dict(color=MUTED)),
                   tickmode="array",tickvals=list(range(1,11)),ticktext=[f"T{i}" for i in range(1,11)]),
        yaxis=ax())
    fig_rm.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED,size=11)))
    st.plotly_chart(fig_rm,use_container_width=True)

    # ═══ 2. GAINS OBTENUS ═══════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("<h3 style='font-family:Rajdhani;font-size:1.5rem;color:#3fb950;letter-spacing:1px;margin-bottom:16px'>📊 Gains obtenus après application du plan d'action — par Département</h3>",unsafe_allow_html=True)

    for dept,dc in DEPT_COLORS.items():
        act=actuals[dept]; tgt=TARGETS[dept]; kpis=["TD","TP","TQ","TRS"]
        ann_cols=st.columns(4)
        for kpi in kpis:
            a=act[kpi]; t=tgt[kpi]; delta=t-a
            with ann_cols[kpis.index(kpi)]:
                st.markdown(f"""<div style='text-align:center;padding:6px 0'>
<div style='color:#8b949e;font-size:0.85rem;font-weight:500'>{a:.1f}%</div>
<div style='color:{dc};font-size:0.95rem;font-weight:700'>↑ +{delta:.1f} pts</div>
<div style='color:#3fb950;font-family:Rajdhani;font-size:1.3rem;font-weight:700'>{t:.1f}%</div>
<div style='color:#8b949e;font-size:0.72rem;text-transform:uppercase;letter-spacing:1px'>{kpi}</div>
</div>""",unsafe_allow_html=True)
        fig_ab=go.Figure()
        fig_ab.add_trace(go.Bar(name="Actuel",x=kpis,y=[act[k] for k in kpis],
            marker_color="#4a5568",marker_line_color="rgba(0,0,0,0)",
            text=[f"{act[k]:.1f}%" for k in kpis],textposition="outside",textfont=dict(color=TEXT,size=10)))
        fig_ab.add_trace(go.Bar(name="Objectif",x=kpis,y=[tgt[k] for k in kpis],
            marker_color=dc,marker_line_color="rgba(0,0,0,0)",
            text=[f"{tgt[k]:.1f}%" for k in kpis],textposition="outside",textfont=dict(color=TEXT,size=10)))
        fig_ab.add_trace(go.Scatter(x=kpis,y=[act[k] for k in kpis],mode="lines",
            line=dict(color="#f85149",width=1.5,dash="dash"),showlegend=False,
            hoverinfo="skip"))
        fig_ab.update_layout(barmode="group",height=300,**BL,
            title=dict(text=f"Gains obtenus après 10 mois d'amélioration — {dept}",font=dict(color=MUTED,size=11)),
            xaxis=ax(),yaxis=ax(pct=True))
        fig_ab.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED,size=11)))
        fig_ab.update_yaxes(range=[0,115])
        st.plotly_chart(fig_ab,use_container_width=True)
        st.markdown("<hr style='border-color:#1e2430;margin:8px 0'>",unsafe_allow_html=True)

    # Production supplémentaire
    st.markdown("<div class='sh'>Production Supplémentaire Estimée</div>",unsafe_allow_html=True)
    ep1,ep2,ep3,ep4=st.columns(4)
    for col_,dept in zip([ep1,ep2,ep3],["Découpe","Usinage","Peinture"]):
        with col_:
            st.markdown(f"""<div style='background:#161b22;border:1px solid #21262d;border-radius:10px;padding:16px 20px;border-left:3px solid {DEPT_COLORS[dept]}'>
<div style='color:#8b949e;font-size:0.64rem;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px'>Unités / jour gagnées</div>
<div style='color:#3fb950;font-family:Rajdhani;font-size:2.2rem;font-weight:700'>+{EXTRA_PROD[dept]}</div>
<div style='color:#8b949e;font-size:0.72rem'>{dept} (estimé)</div>
</div>""",unsafe_allow_html=True)
    with ep4:
        ann=min(EXTRA_PROD.values())*250
        st.markdown(f"""<div style='background:linear-gradient(135deg,#0d1f0d,#1a2c1a);border:1px solid #3fb950;border-radius:10px;padding:16px 20px'>
<div style='color:#8b949e;font-size:0.64rem;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px'>Gain annuel total</div>
<div style='color:#3fb950;font-family:Rajdhani;font-size:2.2rem;font-weight:700'>+{ann:,}</div>
<div style='color:#8b949e;font-size:0.72rem'>unités sur 250 jours</div>
</div>""",unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown("""<div style='background:linear-gradient(135deg,#161b22,#1c2128);border:1px solid #1f6feb;border-radius:10px;padding:16px 20px'>
<p style='color:#58a6ff;font-weight:700;margin:0 0 8px;font-family:Rajdhani;font-size:1.1rem'>💡 Synthèse — Gain TRS estimé si toutes les actions sont menées</p>
<p style='color:#8b949e;font-size:0.8rem;margin:0;line-height:1.8'>
En appliquant l'ensemble des actions de priorité 1 et 2, le gain cumulé estimé est de
<span style='color:#3fb950;font-weight:700'>+15% à +45%</span> selon le département.
<strong style='color:#58a6ff'>Découpe</strong> : bénéficiera le plus de la maintenance préventive (pannes fréquentes, dégradation progressive du TD).
<strong style='color:#3fb950'>Usinage</strong> : gain majeur sur TP via le SMED (TP actuel le plus faible des 3 départements).
<strong style='color:#d29922'>Peinture</strong> : amélioration TQ via Poka-Yoke (rejets qualité les plus élevés, démarrages fréquents).
</p></div>""",unsafe_allow_html=True)
