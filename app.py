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
[data-testid="stSidebar"]{background:#111318;border-right:1px solid #1e2430;}
[data-testid="stSidebar"] .stMarkdown h1{font-family:'Rajdhani';font-size:1.4rem;font-weight:700;color:#58a6ff;letter-spacing:3px;margin:0;}
[data-testid="stSidebar"] .stButton button{
    background:#161b22;border:1px solid #21262d;border-radius:8px;
    color:#8b949e;font-size:0.8rem;font-weight:500;
    padding:9px 14px;width:100%;transition:all 0.15s;margin:1px 0;}
[data-testid="stSidebar"] .stButton button:hover{background:#1f2937;color:#e6edf3;border-color:#30363d;}
.stButton button[kind="primary"]{
    background:linear-gradient(135deg,#1f3a5f,#1a3a6e)!important;
    color:#58a6ff!important;border:1px solid #1f6feb!important;font-weight:700!important;}
.stButton button[kind="secondary"]{
    background:#161b22!important;color:#484f58!important;border:1px solid #21262d!important;}
.kcard{background:linear-gradient(135deg,#161b22,#1c2128);border:1px solid #30363d;
    border-radius:12px;padding:16px 18px;position:relative;overflow:hidden;min-height:100px;
    box-shadow:0 2px 10px rgba(0,0,0,0.3);}
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
.sh{font-family:'Rajdhani';font-size:0.95rem;font-weight:700;color:#e6edf3;
    border-bottom:1px solid #21262d;padding-bottom:5px;margin-bottom:10px;letter-spacing:1.5px;
    display:flex;align-items:center;gap:8px;}
.sh::before{content:'';display:inline-block;width:3px;height:14px;border-radius:2px;
    background:linear-gradient(180deg,#58a6ff,#a371f7);flex-shrink:0;}
.sol-card{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:12px 16px;margin-bottom:8px;}
.badge{display:inline-block;border-radius:5px;padding:2px 8px;font-size:0.63rem;font-weight:700;}
.infobox{background:#161b22;border-left:3px solid #f0883e;border-radius:0 8px 8px 0;
    padding:10px 14px;margin-bottom:10px;font-size:0.78rem;color:#c9d1d9;line-height:1.7;}
.tranche-label{font-size:0.62rem;color:#484f58;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px;}
div[data-testid="stHorizontalBlock"]{gap:8px;}
.stSelectbox>div>div{background:#161b22!important;border-color:#21262d!important;}
.stSelectbox label{color:#8b949e!important;font-size:0.74rem!important;}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
DEPT_COLORS  = {"Découpe":"#58a6ff","Usinage":"#3fb950","Peinture":"#d29922"}
# rgba versions for fill (opacity 0.12)
DEPT_FILL    = {"Découpe":"rgba(88,166,255,0.12)","Usinage":"rgba(63,185,80,0.12)","Peinture":"rgba(210,153,34,0.12)"}
TEXT,MUTED,BG = "#e6edf3","#8b949e","#0d1117"
THRESHOLDS   = {"TRS":85,"TD":90,"TP":95,"TQ":98}
THRESH_COLORS= {"TRS":"#f85149","TD":"#f0883e","TP":"#d29922","TQ":"#3fb950"}
KPI_COLORS   = {"TRS":"#58a6ff","TD":"#3fb950","TQ":"#d29922","TP":"#a371f7"}
FILL_COLORS  = {"TRS":"rgba(88,166,255,0.08)","TD":"rgba(63,185,80,0.08)",
                "TQ":"rgba(210,153,34,0.08)","TP":"rgba(163,113,247,0.08)"}
PROD_COLORS  = {"P1":"#58a6ff","P2":"#3fb950","P3":"#d29922","P4":"#a371f7"}
TARGETS      = {"Découpe":{"TD":90,"TP":88,"TQ":98,"TRS":75},
                "Usinage":{"TD":92,"TP":88,"TQ":98,"TRS":79},
                "Peinture":{"TD":90,"TP":88,"TQ":95,"TRS":75}}
EXTRA_PROD   = {"Découpe":380,"Usinage":520,"Peinture":290}

BL = dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
          font=dict(color=TEXT,family="Inter"),margin=dict(l=10,r=10,t=35,b=10),
          legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED,size=11)))

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

# ── Data ───────────────────────────────────────────────────────────────────────
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

# Loss columns definition (shared)
PDEF={"Pannes":("Panne","TD","#f85149"),
      "Remplacement préventif":("Remplacement_préventif","TD","#c9362e"),
      "Arrêts mineurs":("Arrêts_mineurs","TP","#d29922"),
      "Nettoyage":("Nettoyage","TP","#e3b341"),
      "Réglage dérive":("Réglage_dérive","TP","#f0c040"),
      "Inspection":("Inspection","TP","#ffd166"),
      "Changement outil":("Changement_outil","TP","#ffb347"),
      "Déplacement":("Déplacement","TP","#f4845f"),
      "Lubrification":("Lubrification","TP","#c77dff"),
      "Rejet démarrage":("Rejet_Démarrage","TQ","#3fb950"),
      "Rejet qualité":("Rejet_qualité","TQ","#56d364")}

# ── Helpers ────────────────────────────────────────────────────────────────────
def kcard(label,value,color="blue",sub=""):
    cm={"blue":"#58a6ff","green":"#3fb950","orange":"#d29922",
        "red":"#f85149","purple":"#a371f7","teal":"#39d353"}
    c=cm.get(color,"#58a6ff")
    return (f'<div class="kcard {color}"><div class="kcard-label">{label}</div>'
            f'<div class="kcard-val" style="color:{c}">{value}</div>'
            f'<div class="kcard-sub">{sub}</div></div>')

def gauge(val,title,color="#58a6ff",thresh=85):
    fig=go.Figure(go.Indicator(mode="gauge+number",value=val,
        number={"suffix":"%","font":{"color":TEXT,"size":22,"family":"Rajdhani"}},
        title={"text":title,"font":{"color":MUTED,"size":10}},
        gauge={"axis":{"range":[0,100],"tickfont":{"color":MUTED,"size":8}},
               "bar":{"color":color},"bgcolor":"#161b22","borderwidth":0,
               "steps":[{"range":[0,60],"color":"#1c2128"},{"range":[60,thresh],"color":"#1e2820"},
                        {"range":[thresh,100],"color":"#1a2c1a"}],
               "threshold":{"line":{"color":"#f85149","width":2},"thickness":0.75,"value":thresh}}))
    fig.update_layout(height=175,**BL); return fig

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

def tranche_toggle(key_prefix):
    st.markdown("<p class='tranche-label'>Sélection des Tranches</p>",unsafe_allow_html=True)
    for i in range(1,11):
        if f"{key_prefix}_{i}" not in st.session_state:
            st.session_state[f"{key_prefix}_{i}"]=True
    rc1,rc2,_=st.columns([1.2,1.2,9])
    with rc1:
        if st.button("✅ Tout",key=f"all_{key_prefix}",use_container_width=True):
            for i in range(1,11): st.session_state[f"{key_prefix}_{i}"]=True
            st.rerun()
    with rc2:
        if st.button("❌ Aucun",key=f"none_{key_prefix}",use_container_width=True):
            for i in range(1,11): st.session_state[f"{key_prefix}_{i}"]=False
            st.rerun()
    cols=st.columns(10)
    for i,col in enumerate(cols,1):
        with col:
            active=st.session_state[f"{key_prefix}_{i}"]
            if st.button(f"T{i}",key=f"tog_{key_prefix}_{i}",use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state[f"{key_prefix}_{i}"]=not active; st.rerun()
    return [i for i in range(1,11) if st.session_state[f"{key_prefix}_{i}"]]

def view_toggle(key):
    if key not in st.session_state: st.session_state[key]="jour"
    _,vr=st.columns([7,2])
    with vr:
        v1,v2=st.columns(2)
        with v1:
            if st.button("📅 Journalier",key=f"vj_{key}",use_container_width=True,
                         type="primary" if st.session_state[key]=="jour" else "secondary"):
                st.session_state[key]="jour"; st.rerun()
        with v2:
            if st.button("📆 Tranche",key=f"vt_{key}",use_container_width=True,
                         type="primary" if st.session_state[key]=="tranche" else "secondary"):
                st.session_state[key]="tranche"; st.rerun()
    return st.session_state[key]

def page_header(icon,title,subtitle):
    st.markdown(f"""<div style='margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid #21262d'>
<h1 style='font-family:Rajdhani;font-size:2rem;color:#e6edf3;letter-spacing:2px;margin:0;font-weight:700'>{icon} {title}</h1>
<p style='color:#8b949e;font-size:0.78rem;margin:4px 0 0'>{subtitle}</p>
</div>""",unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🏭 TRS")
    st.markdown("<p style='color:#484f58;font-size:0.68rem;letter-spacing:2px;margin-top:-4px'>MEUBLES INC.</p>",unsafe_allow_html=True)
    st.markdown("---")
    PAGES={"📊  Dashboard Global":"global","🪚  Dép. Découpe":"decoupe",
           "⚙️  Dép. Usinage":"usinage","🎨  Dép. Peinture":"peinture",
           "🔍  Source des Pertes":"pertes","🏆  Dashboard Final":"final"}
    if "page" not in st.session_state: st.session_state.page="global"
    for label,key in PAGES.items():
        if st.session_state.page==key:
            st.markdown(f"<div style='background:linear-gradient(90deg,#1f3a5f,#1a2a4a);border:1px solid #1f6feb;border-radius:8px;padding:9px 14px;margin:1px 0;color:#58a6ff;font-size:0.8rem;font-weight:600'>{label}</div>",unsafe_allow_html=True)
        else:
            if st.button(label,key=f"nav_{key}",use_container_width=True):
                st.session_state.page=key; st.rerun()
    st.markdown("---")
    st.markdown("<p style='color:#484f58;font-size:0.6rem;text-transform:uppercase;letter-spacing:2px'>Données</p>",unsafe_allow_html=True)
    st.markdown("<p style='color:#8b949e;font-size:0.74rem;margin:2px 0'>📅 250 jours · 10 tranches × 25 j</p>",unsafe_allow_html=True)
    st.markdown("<p style='color:#8b949e;font-size:0.74rem;margin:2px 0'>📦 P1 P2 P3 P4 · 3 depts</p>",unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<p style='color:#484f58;font-size:0.6rem;text-transform:uppercase;letter-spacing:2px'>Seuils TPM</p>",unsafe_allow_html=True)
    for k,v in THRESHOLDS.items():
        st.markdown(f"<p style='color:{THRESH_COLORS[k]};font-size:0.74rem;margin:2px 0'>● {k} ≥ {v}%</p>",unsafe_allow_html=True)

page=st.session_state.page

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL
# ═══════════════════════════════════════════════════════════════════════════════
if page=="global":
    page_header("📊","DASHBOARD GLOBAL","Vue d'ensemble — 10 tranches × 25 jours · 3 départements · 4 produits")

    vm=view_toggle("vm_global")
    fc1,fc2=st.columns(2)
    with fc1: sel_prod=st.selectbox("Produit",["Tous","P1","P2","P3","P4"],key="g_prod")
    with fc2: sel_dept=st.selectbox("Département",["Tous"]+list(DEPT_COLORS.keys()),key="g_dept")

    if vm=="tranche":
        sel_t=tranche_toggle("g")
        if not sel_t: st.warning("Sélectionnez au moins une tranche."); st.stop()
    else:
        sel_t=ALL_P

    combined=pd.concat(dfs.values(),ignore_index=True)
    df=combined[combined["Tranche"].isin(sel_t)].copy()
    if sel_prod!="Tous": df=df[df["Produit"]==sel_prod]
    if sel_dept!="Tous": df=df[df["Département"]==sel_dept]
    if df.empty: st.warning("Aucune donnée."); st.stop()

    trs_m=df["TRS"].mean()*100; td_m=df["TD"].mean()*100
    tq_m=df["TQ"].mean()*100;   tp_m=df["TP"].mean()*100

    st.markdown("<br>",unsafe_allow_html=True)
    k1,k2,k3,k4=st.columns(4)
    with k1: st.markdown(kcard("TRS GLOBAL",f"{trs_m:.1f}%","blue" if trs_m>=85 else "red",f"{flag(trs_m,85)} Seuil ≥ 85%"),unsafe_allow_html=True)
    with k2: st.markdown(kcard("DISPONIBILITÉ TD",f"{td_m:.1f}%","green" if td_m>=90 else "red",f"{flag(td_m,90)} Seuil ≥ 90%"),unsafe_allow_html=True)
    with k3: st.markdown(kcard("QUALITÉ TQ",f"{tq_m:.1f}%","teal" if tq_m>=98 else "red",f"{flag(tq_m,98)} Seuil ≥ 98%"),unsafe_allow_html=True)
    with k4: st.markdown(kcard("PERFORMANCE TP",f"{tp_m:.1f}%","orange" if tp_m>=95 else "red",f"{flag(tp_m,95)} Seuil ≥ 95%"),unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)

    if vm=="tranche":
        by_t=df.groupby("Tranche")[["TRS","TD","TQ","TP"]].mean().reset_index().sort_values("Tranche")
        st.markdown("<div class='sh'>Évolution TRS · TD · TQ · TP par Tranche</div>",unsafe_allow_html=True)
        fig_ev=go.Figure()
        for kpi,c in KPI_COLORS.items():
            fig_ev.add_trace(go.Scatter(x=by_t["Tranche"],y=by_t[kpi]*100,name=kpi,
                line=dict(color=c,width=2.5),mode="lines+markers",marker=dict(size=7)))
        add_thresh(fig_ev,["TRS","TD","TQ","TP"])
        fig_ev.update_layout(height=290,**BL,xaxis=txax(by_t["Tranche"]),yaxis=ax(pct=True))
        fig_ev.update_yaxes(range=[0,110]); st.plotly_chart(fig_ev,use_container_width=True)

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
            fig_dt.update_layout(height=240,**BL,xaxis=txax(by_dt["Tranche"]),yaxis=ax(pct=True))
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
            fig_pt.update_layout(height=240,**BL,xaxis=txax(by_pt["Tranche"]),yaxis=ax(pct=True))
            fig_pt.update_yaxes(range=[0,110]); st.plotly_chart(fig_pt,use_container_width=True)

        st.markdown("<div class='sh'>Heatmap TRS — Département × Tranche</div>",unsafe_allow_html=True)
        piv=(df.groupby(["Département","Tranche"])["TRS"].mean().unstack().sort_index()*100).round(1)
        piv=piv.reindex(sorted(piv.columns),axis=1)
        fig_hm=go.Figure(go.Heatmap(z=piv.values,x=[f"T{int(c)}" for c in sorted(piv.columns)],
            y=piv.index.tolist(),colorscale=[[0,"#1c2128"],[0.5,"#d29922"],[1,"#3fb950"]],
            zmin=0,zmax=100,text=piv.values.astype(str),texttemplate="%{text}%",
            textfont=dict(size=10,color="white"),colorbar=dict(ticksuffix="%",tickfont=dict(color=MUTED))))
        fig_hm.update_layout(height=185,**BL,xaxis=ax(),yaxis=ax())
        st.plotly_chart(fig_hm,use_container_width=True)

        st.markdown("<div class='sh'>📋 Tableau Récapitulatif par Tranche</div>",unsafe_allow_html=True)
        st.dataframe(recap_table(df),use_container_width=True,hide_index=True,column_config=pbar_cfg())

    else:
        # ── Vue JOURNALIÈRE ──
        comb_all=pd.concat(dfs.values(),ignore_index=True)
        if sel_prod!="Tous": comb_all=comb_all[comb_all["Produit"]==sel_prod]

        st.markdown("<div class='sh'>TRS Journalier J1→J250 — 3 Départements</div>",unsafe_allow_html=True)
        fig_jg=go.Figure()
        pal_bg=["rgba(88,166,255,0.04)","rgba(63,185,80,0.04)","rgba(210,153,34,0.04)",
                "rgba(163,113,247,0.04)","rgba(248,81,73,0.04)"]
        for t in range(1,11):
            j0=(t-1)*25+1; j1=t*25
            fig_jg.add_vrect(x0=j0,x1=j1,fillcolor=pal_bg[(t-1)%5],layer="below",line_width=0)
            fig_jg.add_annotation(x=(j0+j1)/2,y=107,text=f"T{t}",showarrow=False,font=dict(color=MUTED,size=8),yref="y")
        for dept,dc in DEPT_COLORS.items():
            sub_d=(comb_all[comb_all["Département"]==dept]
                   .groupby("Journée")["TRS"].mean().reset_index().sort_values("Journée"))
            if sub_d.empty: continue
            fig_jg.add_trace(go.Scatter(x=sub_d["Journée"],y=sub_d["TRS"]*100,name=dept,
                line=dict(color=dc,width=1.5),mode="lines"))
        fig_jg.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.5,
                         annotation_text="Seuil 85%",annotation_font=dict(color="#f85149",size=9))
        fig_jg.update_layout(height=270,**BL,xaxis=ax(title="Journée (1–250)"),yaxis=ax(pct=True))
        fig_jg.update_yaxes(range=[0,110]); st.plotly_chart(fig_jg,use_container_width=True)

        cl2,cr2=st.columns(2)
        with cl2:
            st.markdown("<div class='sh'>TRS journalier par Département</div>",unsafe_allow_html=True)
            fig_dj=go.Figure()
            for dept,dc in DEPT_COLORS.items():
                sub=(comb_all[comb_all["Département"]==dept]
                     .groupby("Journée")["TRS"].mean().reset_index().sort_values("Journée"))
                if sub.empty: continue
                # ✅ FIX: use DEPT_FILL for fillcolor instead of dc+"15"
                fig_dj.add_trace(go.Scatter(x=sub["Journée"],y=sub["TRS"]*100,name=dept,
                    line=dict(color=dc,width=1.5),mode="lines",fill="tozeroy",
                    fillcolor=DEPT_FILL[dept]))
            fig_dj.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.2)
            fig_dj.update_layout(height=230,**BL,xaxis=ax(title="Journée"),yaxis=ax(pct=True))
            fig_dj.update_yaxes(range=[0,110]); st.plotly_chart(fig_dj,use_container_width=True)
        with cr2:
            st.markdown("<div class='sh'>TRS journalier par Produit</div>",unsafe_allow_html=True)
            fig_pj=go.Figure()
            for p,pc in PROD_COLORS.items():
                sub=(comb_all[comb_all["Produit"]==p]
                     .groupby("Journée")["TRS"].mean().reset_index().sort_values("Journée"))
                if sub.empty: continue
                fig_pj.add_trace(go.Scatter(x=sub["Journée"],y=sub["TRS"]*100,name=p,
                    line=dict(color=pc,width=1.5),mode="lines"))
            fig_pj.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.2)
            fig_pj.update_layout(height=230,**BL,xaxis=ax(title="Journée"),yaxis=ax(pct=True))
            fig_pj.update_yaxes(range=[0,110]); st.plotly_chart(fig_pj,use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# DÉPARTEMENT (générique)
# ═══════════════════════════════════════════════════════════════════════════════
def dept_page(dept_name):
    color=DEPT_COLORS[dept_name]
    icons={"Découpe":"🪚","Usinage":"⚙️","Peinture":"🎨"}
    page_header(icons[dept_name],f"DÉPARTEMENT {dept_name.upper()}","Filtrage interactif — seuils TPM")

    vm=view_toggle(f"vm_{dept_name}")
    sel_prod=st.selectbox("Produit",["Tous","P1","P2","P3","P4"],key=f"p_{dept_name}")

    if vm=="tranche":
        sel_t=tranche_toggle(f"d{dept_name[:2]}")
        if not sel_t: st.warning("Sélectionnez au moins une tranche."); return
        df=dfs[dept_name][dfs[dept_name]["Tranche"].isin(sel_t)].copy()
    else:
        sel_t=ALL_P
        df=dfs[dept_name].copy()

    if sel_prod!="Tous": df=df[df["Produit"]==sel_prod]
    if df.empty: st.warning("Aucune donnée."); return

    trs_m=df["TRS"].mean()*100; td_m=df["TD"].mean()*100
    tq_m=df["TQ"].mean()*100;   tp_m=df["TP"].mean()*100

    st.markdown("<br>",unsafe_allow_html=True)
    k1,k2,k3,k4=st.columns(4)
    with k1: st.markdown(kcard("TRS MOYEN",f"{trs_m:.1f}%","blue" if trs_m>=85 else "red",f"{flag(trs_m,85)} Seuil 85%"),unsafe_allow_html=True)
    with k2: st.markdown(kcard("TD DISPONIBILITÉ",f"{td_m:.1f}%","green" if td_m>=90 else "red",f"{flag(td_m,90)} Seuil 90%"),unsafe_allow_html=True)
    with k3: st.markdown(kcard("TQ QUALITÉ",f"{tq_m:.1f}%","teal" if tq_m>=98 else "red",f"{flag(tq_m,98)} Seuil 98%"),unsafe_allow_html=True)
    with k4: st.markdown(kcard("TP PERFORMANCE",f"{tp_m:.1f}%","orange" if tp_m>=95 else "red",f"{flag(tp_m,95)} Seuil 95%"),unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)

    cg1,cg2,cg3,cg4=st.columns(4)
    with cg1: st.plotly_chart(gauge(trs_m,"TRS",color,85),use_container_width=True,key=f"g1_{dept_name}")
    with cg2: st.plotly_chart(gauge(td_m,"TD","#58a6ff",90),use_container_width=True,key=f"g2_{dept_name}")
    with cg3: st.plotly_chart(gauge(tq_m,"TQ","#3fb950",98),use_container_width=True,key=f"g3_{dept_name}")
    with cg4: st.plotly_chart(gauge(tp_m,"TP","#d29922",95),use_container_width=True,key=f"g4_{dept_name}")

    if vm=="tranche":
        by_t=df.groupby("Tranche")[["TRS","TD","TQ","TP"]].mean().reset_index().sort_values("Tranche")
        xvals=by_t["Tranche"]; xlabels=[f"T{int(v)}" for v in xvals]
        xax_cfg=txax(xvals)

        st.markdown("<div class='sh'>Évolution TRS · TD · TQ · TP par Tranche</div>",unsafe_allow_html=True)
        fig_t=go.Figure()
        for kpi,c in KPI_COLORS.items():
            fig_t.add_trace(go.Scatter(x=xvals,y=by_t[kpi]*100,name=kpi,
                line=dict(color=c,width=2.5),mode="lines+markers",marker=dict(size=7)))
        add_thresh(fig_t,["TRS","TD","TQ","TP"])
        fig_t.update_layout(height=285,**BL,xaxis=xax_cfg,yaxis=ax(pct=True))
        fig_t.update_yaxes(range=[0,110]); st.plotly_chart(fig_t,use_container_width=True)

        st.markdown("<div class='sh'>Évolution individuelle TRS · TD · TQ · TP</div>",unsafe_allow_html=True)
        cA,cB,cC,cD=st.columns(4)
        for col_,kpi,thresh in [(cA,"TRS",85),(cB,"TD",90),(cC,"TQ",98),(cD,"TP",95)]:
            with col_:
                fig_k=go.Figure()
                fig_k.add_trace(go.Scatter(x=xvals,y=by_t[kpi]*100,name=kpi,
                    line=dict(color=KPI_COLORS[kpi],width=2),mode="lines+markers",
                    marker=dict(size=6),fill="tozeroy",fillcolor=FILL_COLORS[kpi]))
                fig_k.add_hline(y=thresh,line_dash="dash",line_color=THRESH_COLORS[kpi],line_width=1.5,
                                annotation_text=f"Seuil {thresh}%",
                                annotation_font=dict(color=THRESH_COLORS[kpi],size=8))
                fig_k.update_layout(height=185,**BL,xaxis=xax_cfg,yaxis=ax(pct=True))
                fig_k.update_layout(title=dict(text=f"Évolution {kpi}",font=dict(color=TEXT,size=10)))
                fig_k.update_yaxes(range=[0,110])
                st.plotly_chart(fig_k,use_container_width=True,key=f"ind_{kpi}_{dept_name}")

        st.markdown("<div class='sh'>TRS · TD · TQ · TP par Tranche — Bâtonnets</div>",unsafe_allow_html=True)
        fig_j=go.Figure()
        for kpi,c in KPI_COLORS.items():
            yvals=by_t[kpi]*100
            fig_j.add_trace(go.Bar(name=kpi,x=xlabels,y=yvals,marker_color=c,
                marker_line_color="rgba(0,0,0,0)",
                text=[f"{v:.1f}%" for v in yvals],textposition="outside",textfont=dict(color=TEXT,size=8)))
        for kpi in ["TRS","TD","TQ","TP"]:
            fig_j.add_hline(y=THRESHOLDS[kpi],line_dash="dash",line_color=THRESH_COLORS[kpi],line_width=1.2,
                annotation_text=f"Seuil {kpi} {THRESHOLDS[kpi]}%",annotation_position="top right",
                annotation_font=dict(color=THRESH_COLORS[kpi],size=8))
        fig_j.update_layout(barmode="group",height=290,**BL,xaxis=ax(title="Tranche"),yaxis=ax(pct=True))
        fig_j.update_yaxes(range=[0,115]); st.plotly_chart(fig_j,use_container_width=True)

        st.markdown("<div class='sh'>📋 Tableau par Tranche</div>",unsafe_allow_html=True)
        st.dataframe(recap_table(df),use_container_width=True,hide_index=True,column_config=pbar_cfg())

    else:
        st.markdown("<div class='sh'>TRS journalier J1–J250</div>",unsafe_allow_html=True)
        fig_jd=go.Figure()
        pal_bg=["rgba(88,166,255,0.04)","rgba(63,185,80,0.04)","rgba(210,153,34,0.04)",
                "rgba(163,113,247,0.04)","rgba(248,81,73,0.04)"]
        for t in range(1,11):
            j0=(t-1)*25+1; j1=t*25
            fig_jd.add_vrect(x0=j0,x1=j1,fillcolor=pal_bg[(t-1)%5],layer="below",line_width=0)
            fig_jd.add_annotation(x=(j0+j1)/2,y=107,text=f"T{t}",showarrow=False,
                                   font=dict(color=MUTED,size=8),yref="y")
        sub_j=dfs[dept_name].copy()
        if sel_prod!="Tous": sub_j=sub_j[sub_j["Produit"]==sel_prod]
        for kpi,c in KPI_COLORS.items():
            gj=sub_j.groupby("Journée")[kpi].mean().reset_index().sort_values("Journée")
            fig_jd.add_trace(go.Scatter(x=gj["Journée"],y=gj[kpi]*100,name=kpi,
                line=dict(color=c,width=1.5),mode="lines"))
        fig_jd.add_hline(y=85,line_dash="dash",line_color="#f85149",line_width=1.5,
                          annotation_text="Seuil TRS 85%",annotation_font=dict(color="#f85149",size=9))
        fig_jd.update_layout(height=280,**BL,xaxis=ax(title="Journée (1–250)"),yaxis=ax(pct=True))
        fig_jd.update_yaxes(range=[0,110]); st.plotly_chart(fig_jd,use_container_width=True)

    # Analyse par Produit (always shown)
    st.markdown("<div class='sh'>Analyse par Produit — KPIs & Pertes</div>",unsafe_allow_html=True)
    df_prod=dfs[dept_name][dfs[dept_name]["Tranche"].isin(sel_t)].copy()
    by_p=df_prod.groupby("Produit").agg(
        TRS=("TRS","mean"),TD=("TD","mean"),TQ=("TQ","mean"),TP=("TP","mean"),
        Panne=("Panne","sum"),Arrêts_mineurs=("Arrêts_mineurs","sum"),
        Rejet_qualité=("Rejet_qualité","sum"),
        Rejet_Démarrage=("Rejet_Démarrage",lambda x:x.fillna(0).sum())
    ).reset_index()
    prods=[p for p in ["P1","P2","P3","P4"] if p in by_p["Produit"].values]

    cl_p,cr_p=st.columns(2)
    with cl_p:
        fig_pg=go.Figure()
        for kpi,c in KPI_COLORS.items():
            vals=[float(by_p[by_p["Produit"]==p][kpi].values[0])*100 if p in by_p["Produit"].values else 0 for p in prods]
            fig_pg.add_trace(go.Bar(name=kpi,x=prods,y=vals,marker_color=c,
                marker_line_color="rgba(0,0,0,0)",
                text=[f"{v:.1f}%" for v in vals],textposition="outside",textfont=dict(color=TEXT,size=9)))
        for kpi in ["TRS","TD","TQ","TP"]:
            fig_pg.add_hline(y=THRESHOLDS[kpi],line_dash="dash",line_color=THRESH_COLORS[kpi],line_width=1)
        fig_pg.update_layout(barmode="group",height=270,**BL,xaxis=ax(title="Produit"),yaxis=ax(pct=True))
        fig_pg.update_layout(title=dict(text="KPIs par Produit",font=dict(color=TEXT,size=11)))
        fig_pg.update_yaxes(range=[0,115]); st.plotly_chart(fig_pg,use_container_width=True)
    with cr_p:
        scores=[]
        for p in prods:
            row=by_p[by_p["Produit"]==p]
            trs_p=float(row["TRS"].values[0])*100; td_p=float(row["TD"].values[0])*100
            tq_p=float(row["TQ"].values[0])*100;   tp_p=float(row["TP"].values[0])*100
            gap=max(0,85-trs_p)+max(0,90-td_p)+max(0,98-tq_p)+max(0,95-tp_p)
            scores.append({"Produit":p,"TRS %":round(trs_p,1),"TD %":round(td_p,1),
                           "TQ %":round(tq_p,1),"TP %":round(tp_p,1),"Écart":round(gap,1),
                           "Pannes":int(float(row["Panne"].values[0])),
                           "Rejets":int(float(row["Rejet_qualité"].values[0])+float(row["Rejet_Démarrage"].values[0]))})
        sdf=pd.DataFrame(scores).sort_values("Écart",ascending=False)
        if not sdf.empty:
            w=sdf.iloc[0]; b=sdf.iloc[-1]
            st.markdown(f"<div style='background:#1a1010;border:1px solid #f85149;border-radius:8px;padding:10px 14px;margin-bottom:8px'><p style='color:#f85149;font-weight:700;margin:0 0 2px;font-family:Rajdhani'>⚠️ Plus critique : {w['Produit']} — Écart : {w['Écart']}%</p><p style='color:#c9d1d9;font-size:0.76rem;margin:0'>TRS={w['TRS %']}% · TD={w['TD %']}% · TQ={w['TQ %']}% · TP={w['TP %']}%</p></div>",unsafe_allow_html=True)
            st.markdown(f"<div style='background:#0d1a0d;border:1px solid #3fb950;border-radius:8px;padding:10px 14px;margin-bottom:8px'><p style='color:#3fb950;font-weight:700;margin:0 0 2px;font-family:Rajdhani'>✅ Meilleur : {b['Produit']} — Écart : {b['Écart']}%</p><p style='color:#c9d1d9;font-size:0.76rem;margin:0'>TRS={b['TRS %']}% · TD={b['TD %']}% · TQ={b['TQ %']}% · TP={b['TP %']}%</p></div>",unsafe_allow_html=True)
        pbar4={"TRS %":st.column_config.ProgressColumn("TRS %",min_value=0,max_value=100,format="%.1f%%"),
               "TD %": st.column_config.ProgressColumn("TD %", min_value=0,max_value=100,format="%.1f%%"),
               "TQ %": st.column_config.ProgressColumn("TQ %", min_value=0,max_value=100,format="%.1f%%"),
               "TP %": st.column_config.ProgressColumn("TP %", min_value=0,max_value=100,format="%.1f%%")}
        st.dataframe(sdf,use_container_width=True,hide_index=True,column_config=pbar4)

if page=="decoupe":  dept_page("Découpe")
elif page=="usinage": dept_page("Usinage")
elif page=="peinture":dept_page("Peinture")

# ═══════════════════════════════════════════════════════════════════════════════
# SOURCE DES PERTES — version complète avec analyse par département
# ═══════════════════════════════════════════════════════════════════════════════
elif page=="pertes":
    page_header("🔍","SOURCE DES PERTES","Analyse causale — 3 familles · 11 sources · démarche TPM")

    with st.expander("📖 Fondement méthodologique — Démarche TPM",expanded=False):
        st.markdown("""<div style='color:#c9d1d9;font-size:0.82rem;line-height:1.9'>
<p>La démarche <strong>TPM</strong> décompose l'inefficacité selon :</p>
<p style='text-align:center;font-family:Rajdhani;font-size:1.3rem;color:#58a6ff;background:#161b22;padding:8px;border-radius:6px'>TRS = TD × TQ × TP</p>
<hr style='border-color:#21262d'>
<p><span style='color:#f85149'>🔴</span> <strong>DISPONIBILITÉ (TD)</strong> — Pannes · Remplacement préventif</p>
<p><span style='color:#d29922'>🟡</span> <strong>PERFORMANCE (TP)</strong> — Arrêts mineurs · Nettoyage · Réglage dérive · Inspection · Changement outil · Déplacement · Lubrification</p>
<p><span style='color:#3fb950'>🟢</span> <strong>QUALITÉ (TQ)</strong> — Rejet démarrage · Rejet qualité</p>
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

    pv={l:df_p[c].fillna(0).sum() for l,(c,_,_) in PDEF.items()}
    td_l=pv["Pannes"]+pv["Remplacement préventif"]
    tp_l=sum(pv[l] for l,(_,f,_) in PDEF.items() if f=="TP")
    tq_l=pv["Rejet démarrage"]+pv["Rejet qualité"]

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION A — Source majoritaire par département (NOUVEAU)
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown("<div class='sh'>🏭 Source de Perte Majoritaire — Analyse par Département</div>",unsafe_allow_html=True)
    st.markdown("""<div class='infobox'>
<strong style='color:#f0883e'>Pourquoi cette analyse ?</strong>
Chaque département a un <strong>profil de pertes différent</strong> selon sa nature opérationnelle.
Identifier la source dominante permet de <strong>prioriser les actions correctives</strong> là où le gain est maximal.
Les calculs ci-dessous sont basés sur les données réelles des 250 jours de production.</div>""",unsafe_allow_html=True)

    dept_loss_data={}
    for dept in ["Découpe","Usinage","Peinture"]:
        sub=combined[combined["Département"]==dept][combined["Tranche"].isin(sel_t_p)]
        if sel_prod_p!="Tous": sub=sub[sub["Produit"]==sel_prod_p]
        losses={}
        for lbl,(col,fam,clr) in PDEF.items():
            losses[lbl]={"val":sub[col].fillna(0).sum(),"fam":fam,"clr":clr}
        sorted_losses=sorted(losses.items(),key=lambda x:x[1]["val"],reverse=True)
        total_loss=sum(v["val"] for _,v in losses.items())
        dept_loss_data[dept]={"losses":losses,"sorted":sorted_losses,"total":total_loss,
                               "td":losses["Pannes"]["val"]+losses["Remplacement préventif"]["val"],
                               "tp":sum(v["val"] for _,v in losses.items() if v["fam"]=="TP"),
                               "tq":losses["Rejet démarrage"]["val"]+losses["Rejet qualité"]["val"],
                               "td_pct":sub["TD"].mean()*100,"tp_pct":sub["TP"].mean()*100,
                               "tq_pct":sub["TQ"].mean()*100,"trs_pct":sub["TRS"].mean()*100}

    # Diagnostic texte par département
    DEPT_DIAGNOSTIC = {
        "Découpe": {
            "titre": "🪚 Découpe — Dominé par les Pannes Machines (TD)",
            "fam_color": "#f85149",
            "explication": (
                "Le département Découpe souffre principalement de <strong>pertes de disponibilité</strong> dues aux pannes fréquentes. "
                "Les lames et disques de découpe s'usent rapidement sous contrainte mécanique intense, provoquant des arrêts non planifiés répétés. "
                "Le remplacement préventif vient en second, signalant un manque de planification maintenance. "
                "Conséquence directe : le <strong>TD est le KPI le plus dégradé</strong> de ce département. "
                "Action prioritaire : mettre en place un <strong>plan de maintenance préventive basé sur le MTBF</strong> et équiper les machines de capteurs de vibration pour détecter l'usure avant la casse."
            ),
            "action": "Maintenance préventive (GMAO) + Analyse MTBF",
            "kpi_cible": "TD ≥ 90%",
            "action_color": "#f85149"
        },
        "Usinage": {
            "titre": "⚙️ Usinage — Dominé par les Arrêts Mineurs & Réglages (TP)",
            "fam_color": "#d29922",
            "explication": (
                "Le département Usinage accumule des <strong>pertes de performance</strong> à travers de multiples micro-arrêts : "
                "arrêts mineurs, nettoyage des copeaux, réglages de dérive d'outil et changements fréquents d'outils. "
                "Ces interruptions courtes mais cumulées empêchent la machine d'atteindre sa cadence nominale. "
                "La <strong>dérive des paramètres d'usinage</strong> (jeu, usure progressive) impose des recalibrations régulières. "
                "Le <strong>TP est l'indicateur le plus pénalisé</strong>. "
                "Action prioritaire : appliquer le <strong>SMED</strong> sur les changements d'outils et installer des capteurs SPC pour détecter les dérives en temps réel."
            ),
            "action": "SMED + SPC (contrôle dérive) + 5S",
            "kpi_cible": "TP ≥ 95%",
            "action_color": "#d29922"
        },
        "Peinture": {
            "titre": "🎨 Peinture — Dominé par les Rejets Qualité (TQ)",
            "fam_color": "#3fb950",
            "explication": (
                "Le département Peinture génère les <strong>pertes qualité les plus élevées</strong> des trois départements. "
                "Les rejets au démarrage sont particulièrement importants : chaque changement de couleur ou de produit nécessite une phase de stabilisation "
                "où les premières pièces sont hors tolérances (épaisseur, adhérence, teinte). "
                "Les rejets qualité en production traduisent une instabilité des paramètres de pulvérisation (pression, viscosité, température). "
                "Le <strong>TQ est le KPI le plus critique</strong> de ce département. "
                "Action prioritaire : déployer des <strong>Poka-Yoke de démarrage</strong> (paramètres figés par recette produit) "
                "et une <strong>AMDEC</strong> pour identifier les étapes à risque élevé de rebut."
            ),
            "action": "Poka-Yoke démarrage + AMDEC + Autocontrôle",
            "kpi_cible": "TQ ≥ 98%",
            "action_color": "#3fb950"
        }
    }

    d1,d2,d3=st.columns(3)
    for col_widget,dept in zip([d1,d2,d3],["Découpe","Usinage","Peinture"]):
        with col_widget:
            dl=dept_loss_data[dept]
            dc=DEPT_COLORS[dept]
            diag=DEPT_DIAGNOSTIC[dept]
            top_loss_name,top_loss_data=dl["sorted"][0]
            top2_name,top2_data=dl["sorted"][1]
            top_pct=top_loss_data["val"]/max(dl["total"],1)*100
            top2_pct=top2_data["val"]/max(dl["total"],1)*100

            # KPI le plus dégradé
            kpi_vals={"TD":dl["td_pct"],"TP":dl["tp_pct"],"TQ":dl["tq_pct"]}
            worst_kpi=min(kpi_vals,key=lambda k:kpi_vals[k]-THRESHOLDS[k])
            worst_val=kpi_vals[worst_kpi]
            worst_thresh=THRESHOLDS[worst_kpi]

            st.markdown(f"""<div style='background:#161b22;border:1px solid {dc};border-radius:12px;padding:16px;margin-bottom:8px'>

<div style='font-family:Rajdhani;font-size:1.1rem;font-weight:700;color:{dc};margin-bottom:10px'>{diag["titre"]}</div>

<div style='background:#0d1117;border-radius:8px;padding:10px 12px;margin-bottom:10px'>
  <div style='font-size:0.65rem;color:#484f58;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px'>Top sources de perte</div>
  <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:4px'>
    <span style='color:#e6edf3;font-size:0.78rem;font-weight:600'>① {top_loss_name}</span>
    <span style='color:{top_loss_data["clr"]};font-size:0.8rem;font-weight:700'>{top_pct:.1f}%</span>
  </div>
  <div style='background:#1c2128;border-radius:3px;height:4px;margin-bottom:8px'>
    <div style='background:{top_loss_data["clr"]};height:4px;border-radius:3px;width:{min(top_pct,100):.0f}%'></div>
  </div>
  <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:4px'>
    <span style='color:#8b949e;font-size:0.75rem'>② {top2_name}</span>
    <span style='color:{top2_data["clr"]};font-size:0.76rem;font-weight:600'>{top2_pct:.1f}%</span>
  </div>
  <div style='background:#1c2128;border-radius:3px;height:3px'>
    <div style='background:{top2_data["clr"]};height:3px;border-radius:3px;width:{min(top2_pct,100):.0f}%'></div>
  </div>
</div>

<div style='background:#0d1117;border-radius:8px;padding:10px 12px;margin-bottom:10px'>
  <div style='font-size:0.65rem;color:#484f58;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px'>KPI le plus dégradé</div>
  <div style='display:flex;justify-content:space-between'>
    <span style='color:#e6edf3;font-size:0.8rem;font-weight:700'>{worst_kpi}</span>
    <span style='color:{"#3fb950" if worst_val>=worst_thresh else "#f85149"};font-size:0.8rem;font-weight:700'>{worst_val:.1f}% / {worst_thresh}%</span>
  </div>
  <div style='background:#1c2128;border-radius:3px;height:5px;margin-top:4px'>
    <div style='background:{"#3fb950" if worst_val>=worst_thresh else "#f85149"};height:5px;border-radius:3px;width:{min(worst_val,100):.0f}%'></div>
  </div>
  <div style='font-size:0.68rem;color:{"#3fb950" if worst_val>=worst_thresh else "#f85149"};margin-top:3px'>
    {"✅ Conforme" if worst_val>=worst_thresh else f"⚠️ Écart : -{worst_thresh-worst_val:.1f} pts"}
  </div>
</div>

<div style='font-size:0.73rem;color:#c9d1d9;line-height:1.7;margin-bottom:10px'>{diag["explication"]}</div>

<div style='background:{diag["action_color"]}15;border:1px solid {diag["action_color"]}44;border-radius:6px;padding:8px 10px'>
  <div style='font-size:0.65rem;color:#484f58;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:3px'>Action prioritaire</div>
  <div style='color:{diag["action_color"]};font-size:0.75rem;font-weight:600'>{diag["action"]}</div>
  <div style='color:#8b949e;font-size:0.68rem;margin-top:2px'>Objectif : {diag["kpi_cible"]}</div>
</div>

</div>""",unsafe_allow_html=True)

    # Graphe comparatif des pertes par département (stacked bar)
    st.markdown("<div class='sh'>📊 Volume de Pertes par Département — Comparaison</div>",unsafe_allow_html=True)
    loss_cols_short=["Pannes","Arrêts mineurs","Nettoyage","Réglage dérive","Changement outil",
                     "Rejet qualité","Rejet démarrage","Remplacement préventif","Lubrification","Déplacement","Inspection"]
    fig_comp=go.Figure()
    for lbl in loss_cols_short:
        col_name=PDEF[lbl][0]; clr=PDEF[lbl][2]
        vals_per_dept=[]
        for dept in ["Découpe","Usinage","Peinture"]:
            sub=combined[combined["Département"]==dept][combined["Tranche"].isin(sel_t_p)]
            if sel_prod_p!="Tous": sub=sub[sub["Produit"]==sel_prod_p]
            vals_per_dept.append(sub[col_name].fillna(0).sum())
        fig_comp.add_trace(go.Bar(name=lbl,x=["Découpe","Usinage","Peinture"],y=vals_per_dept,
            marker_color=clr,marker_line_color="rgba(0,0,0,0)"))
    fig_comp.update_layout(barmode="stack",height=300,**BL,
        xaxis=ax(title="Département"),yaxis=ax(title="Total pertes (min / pcs)"),
        title=dict(text="Répartition des pertes par source et par département",font=dict(color=MUTED,size=11)))
    st.plotly_chart(fig_comp,use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION B — Analyse par famille (TD / TP / TQ) — détaillée
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("<br>",unsafe_allow_html=True)

    # ── TD ────────────────────────────────────────────────────────────────────
    st.markdown("""<div style='background:#1a1010;border:1px solid #f85149;border-radius:8px;padding:12px 18px;margin-bottom:8px'>
<p style='color:#f85149;font-family:Rajdhani;font-size:1rem;font-weight:700;margin:0 0 4px'>🔴 PERTES DE DISPONIBILITÉ (TD)</p>
<p style='color:#c9d1d9;font-size:0.8rem;margin:0'>
<strong>Formule :</strong> <code style='background:#1c2128;padding:1px 6px;border-radius:3px;color:#f0883e'>TD = TR / TO</code>
&nbsp;·&nbsp; <code style='background:#1c2128;padding:1px 6px;border-radius:3px;color:#f0883e'>TR = TO − Pannes − Remplacement préventif</code></p>
<p style='color:#8b949e;font-size:0.76rem;margin:4px 0 0'>Toute immobilisation non productive réduit le temps d'ouverture réel (TR) et donc TD.</p>
</div>""",unsafe_allow_html=True)

    td1,td2,td3=st.columns(3)
    with td1: st.markdown(kcard("PERTES TD TOTAL",f"{td_l:,.0f} min","red","Pannes + Maint. préventive"),unsafe_allow_html=True)
    with td2: st.markdown(kcard("PANNES",f"{pv['Pannes']:,.0f} min","red",f"{pv['Pannes']/max(td_l,1)*100:.0f}% des pertes TD"),unsafe_allow_html=True)
    with td3: st.markdown(kcard("MAINT. PRÉVENTIVE",f"{pv['Remplacement préventif']:,.0f} min","orange",f"{pv['Remplacement préventif']/max(td_l,1)*100:.0f}% des pertes TD"),unsafe_allow_html=True)

    by_td=df_p.groupby("Tranche").agg(Pannes=("Panne","sum"),
        Remplac=("Remplacement_préventif",lambda x:x.fillna(0).sum())).reset_index().sort_values("Tranche")
    fig_td=go.Figure()
    fig_td.add_trace(go.Bar(name="Pannes",x=[f"T{int(t)}" for t in by_td["Tranche"]],y=by_td["Pannes"],
        marker_color="#f85149",marker_line_color="rgba(0,0,0,0)"))
    fig_td.add_trace(go.Bar(name="Remplacement",x=[f"T{int(t)}" for t in by_td["Tranche"]],y=by_td["Remplac"],
        marker_color="#c9362e",marker_line_color="rgba(0,0,0,0)"))
    fig_td.update_layout(barmode="stack",height=220,**BL,xaxis=ax(title="Tranche"),yaxis=ax(title="Min perdues"))
    fig_td.update_layout(title=dict(text="Pertes TD par Tranche",font=dict(color=MUTED,size=10)))
    st.plotly_chart(fig_td,use_container_width=True)

    # ── TP ────────────────────────────────────────────────────────────────────
    st.markdown("""<div style='background:#1a1a0a;border:1px solid #d29922;border-radius:8px;padding:12px 18px;margin:10px 0 8px'>
<p style='color:#d29922;font-family:Rajdhani;font-size:1rem;font-weight:700;margin:0 0 4px'>🟡 PERTES DE PERFORMANCE (TP)</p>
<p style='color:#c9d1d9;font-size:0.8rem;margin:0'>
<strong>Formule :</strong> <code style='background:#1c2128;padding:1px 6px;border-radius:3px;color:#f0883e'>TP = tn / tfb</code>
&nbsp;·&nbsp; <code style='background:#1c2128;padding:1px 6px;border-radius:3px;color:#f0883e'>tfb = TR − (Arrêts + Nettoyage + Réglage + Inspection + Changement outil + Déplacement + Lubrification)</code></p>
<p style='color:#8b949e;font-size:0.76rem;margin:4px 0 0'>Chaque opération sans valeur ajoutée réduit le temps net et la cadence réelle.</p>
</div>""",unsafe_allow_html=True)

    tp1,tp2,tp3,tp4=st.columns(4)
    for ci,lbl in enumerate(["Arrêts mineurs","Nettoyage","Réglage dérive","Changement outil"]):
        v=pv.get(lbl,0)
        with [tp1,tp2,tp3,tp4][ci]:
            st.markdown(kcard(lbl.upper(),f"{v:,.0f} min","orange",f"{v/max(tp_l,1)*100:.0f}% des pertes TP"),unsafe_allow_html=True)

    by_tp2=df_p.groupby("Tranche").agg(
        Arrêts=("Arrêts_mineurs","sum"),Nettoyage=("Nettoyage","sum"),
        Réglage=("Réglage_dérive","sum"),Inspection=("Inspection","sum"),
        Outil=("Changement_outil","sum"),
        Déplacement=("Déplacement",lambda x:x.fillna(0).sum()),
        Lubrification=("Lubrification","sum")
    ).reset_index().sort_values("Tranche")
    tlbl=[f"T{int(t)}" for t in by_tp2["Tranche"]]
    fig_tp2=go.Figure()
    for cn,lbl,c in [("Arrêts","Arrêts mineurs","#d29922"),("Nettoyage","Nettoyage","#e3b341"),
                      ("Réglage","Réglage dérive","#f0c040"),("Inspection","Inspection","#ffd166"),
                      ("Outil","Changement outil","#ffb347"),("Déplacement","Déplacement","#f4845f"),
                      ("Lubrification","Lubrification","#c77dff")]:
        fig_tp2.add_trace(go.Bar(name=lbl,x=tlbl,y=by_tp2[cn],marker_color=c,marker_line_color="rgba(0,0,0,0)"))
    fig_tp2.update_layout(barmode="stack",height=230,**BL,xaxis=ax(title="Tranche"),yaxis=ax(title="Min perdues"))
    fig_tp2.update_layout(title=dict(text="Pertes TP par Tranche — 7 sources",font=dict(color=MUTED,size=10)))
    st.plotly_chart(fig_tp2,use_container_width=True)

    # ── TQ ────────────────────────────────────────────────────────────────────
    st.markdown("""<div style='background:#0a1a0a;border:1px solid #3fb950;border-radius:8px;padding:12px 18px;margin:10px 0 8px'>
<p style='color:#3fb950;font-family:Rajdhani;font-size:1rem;font-weight:700;margin:0 0 4px'>🟢 PERTES DE QUALITÉ (TQ)</p>
<p style='color:#c9d1d9;font-size:0.8rem;margin:0'>
<strong>Formule :</strong> <code style='background:#1c2128;padding:1px 6px;border-radius:3px;color:#f0883e'>TQ = (Quantité − Rejets) / Quantité</code>
&nbsp;·&nbsp; <code style='background:#1c2128;padding:1px 6px;border-radius:3px;color:#f0883e'>Rejets = Rejet_Démarrage + Rejet_qualité</code></p>
<p style='color:#8b949e;font-size:0.76rem;margin:4px 0 0'>Proportion de pièces conformes — défauts de démarrage et de production continue.</p>
</div>""",unsafe_allow_html=True)

    tq1,tq2,tq3=st.columns(3)
    with tq1: st.markdown(kcard("PERTES TQ TOTAL",f"{tq_l:,.0f} pcs","teal","Rejets cumulés"),unsafe_allow_html=True)
    with tq2: st.markdown(kcard("REJET DÉMARRAGE",f"{pv['Rejet démarrage']:,.0f} pcs","green",f"{pv['Rejet démarrage']/max(tq_l,1)*100:.0f}% des rejets"),unsafe_allow_html=True)
    with tq3: st.markdown(kcard("REJET QUALITÉ",f"{pv['Rejet qualité']:,.0f} pcs","teal",f"{pv['Rejet qualité']/max(tq_l,1)*100:.0f}% des rejets"),unsafe_allow_html=True)

    by_tq=df_p.groupby("Tranche").agg(
        RQ=("Rejet_qualité","sum"),RD=("Rejet_Démarrage",lambda x:x.fillna(0).sum())
    ).reset_index().sort_values("Tranche")
    fig_tq=go.Figure()
    fig_tq.add_trace(go.Bar(name="Rejet qualité",x=[f"T{int(t)}" for t in by_tq["Tranche"]],y=by_tq["RQ"],
        marker_color="#3fb950",marker_line_color="rgba(0,0,0,0)"))
    fig_tq.add_trace(go.Bar(name="Rejet démarrage",x=[f"T{int(t)}" for t in by_tq["Tranche"]],y=by_tq["RD"],
        marker_color="#56d364",marker_line_color="rgba(0,0,0,0)"))
    fig_tq.update_layout(barmode="stack",height=220,**BL,xaxis=ax(title="Tranche"),yaxis=ax(title="Pièces rejetées"))
    fig_tq.update_layout(title=dict(text="Pertes TQ par Tranche",font=dict(color=MUTED,size=10)))
    st.plotly_chart(fig_tq,use_container_width=True)

    # ── Pareto + Anneau ────────────────────────────────────────────────────────
    st.markdown("<br>",unsafe_allow_html=True)
    cl2,cr2=st.columns(2)
    with cl2:
        st.markdown("<div class='sh'>Diagramme de Pareto</div>",unsafe_allow_html=True)
        st.markdown("""<div class='infobox'><strong style='color:#f0883e'>Règle 80/20 :</strong>
80% des pertes viennent de 20% des causes. Traitez en priorité les barres à gauche de la ligne 80%.</div>""",unsafe_allow_html=True)
        sp=dict(sorted(pv.items(),key=lambda x:x[1],reverse=True))
        labels=list(sp.keys()); vals=list(sp.values())
        cumul=np.cumsum(vals)/max(sum(vals),1)*100
        bar_c=[PDEF[l][2] for l in labels]
        fig_par=make_subplots(specs=[[{"secondary_y":True}]])
        fig_par.add_trace(go.Bar(x=labels,y=vals,name="Total",marker_color=bar_c,marker_line_color="rgba(0,0,0,0)"),secondary_y=False)
        fig_par.add_trace(go.Scatter(x=labels,y=cumul,name="Cumulé %",line=dict(color="#f0883e",width=2),mode="lines+markers"),secondary_y=True)
        fig_par.add_hline(y=80,line_dash="dot",line_color="#8b949e",line_width=1,
                          annotation_text="80%",annotation_font=dict(color=MUTED,size=9),secondary_y=True)
        fig_par.update_layout(height=300,**BL,xaxis=ax(angle=30),yaxis=ax(),
                              yaxis2=dict(ticksuffix="%",tickfont=dict(color=MUTED,size=10),gridcolor="#1e2430"))
        st.plotly_chart(fig_par,use_container_width=True)
    with cr2:
        st.markdown("<div class='sh'>Anneau TPM — 6 Grandes Pertes</div>",unsafe_allow_html=True)
        donut_vals=[pv.get("Arrêts mineurs",0),pv["Pannes"],tq_l,
                    pv.get("Nettoyage",0)+pv.get("Réglage dérive",0)+pv.get("Changement outil",0),
                    pv.get("Rejet démarrage",0),
                    pv.get("Lubrification",0)+pv.get("Déplacement",0)+pv.get("Inspection",0)]
        donut_labels=["Vitesse réduite (TP)","Pannes machines","Rejets qualité",
                      "Arrêts mineurs","Démarrages","Nettoyage/Réglage"]
        donut_colors=["#58a6ff","#f85149","#3fb950","#d29922","#a371f7","#39d353"]
        total_d=sum(donut_vals) if sum(donut_vals)>0 else 1
        fig_do=go.Figure(go.Pie(
            labels=[f"{l} {v/total_d*100:.0f}%" for l,v in zip(donut_labels,donut_vals)],
            values=donut_vals,hole=0.52,
            marker=dict(colors=donut_colors,line=dict(color=BG,width=2)),
            textfont=dict(color="white",size=10),textposition="inside",textinfo="percent"))
        fig_do.update_layout(height=300,**BL,showlegend=True)
        fig_do.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED,size=9),
                                          orientation="v",x=1.01,y=0.5))
        st.plotly_chart(fig_do,use_container_width=True)

    st.markdown("<div class='sh'>📋 Tableau par Tranche</div>",unsafe_allow_html=True)
    tbl_r=[]
    for t in sorted(df_p["Tranche"].unique()):
        s=df_p[df_p["Tranche"]==t]
        tbl_r.append({"Tranche":f"T{int(t)}","Jours":f"{(int(t)-1)*25+1}–{int(t)*25}",
                      "TRS %":round(s["TRS"].mean()*100,2),"TD %":round(s["TD"].mean()*100,2),
                      "TQ %":round(s["TQ"].mean()*100,2),"TP %":round(s["TP"].mean()*100,2),
                      "Pannes min":int(s["Panne"].sum()),"Rejets":int(s["Rejet_qualité"].sum())})
    st.dataframe(pd.DataFrame(tbl_r),use_container_width=True,hide_index=True,column_config=pbar_cfg())

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD FINAL
# ═══════════════════════════════════════════════════════════════════════════════
elif page=="final":
    page_header("🏆","DASHBOARD FINAL","Plan d'Action · Gains estimés · Production supplémentaire")

    actuals={}
    for dept in ["Découpe","Usinage","Peinture"]:
        d=dfs[dept]
        actuals[dept]={"TD":d["TD"].mean()*100,"TP":d["TP"].mean()*100,
                       "TQ":d["TQ"].mean()*100,"TRS":d["TRS"].mean()*100}

    def sol_block(titre,prio,desc,outil,bg,bc,pc):
        return f"""<div class='sol-card' style='border-left:3px solid {bc}'>
<div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap'>
<span style='font-weight:600;color:#e6edf3;font-size:0.86rem'>{titre}</span>
<span class='badge' style='background:{bg};color:{pc};border:1px solid {pc}'>{prio}</span>
<span class='badge' style='background:#1c2128;color:#8b949e;border:1px solid #21262d'>{outil}</span>
</div><p style='color:#8b949e;font-size:0.77rem;margin:0;line-height:1.6'>{desc}</p></div>"""

    st.markdown("<h3 style='font-family:Rajdhani;font-size:1.4rem;color:#58a6ff;letter-spacing:1px;margin-bottom:14px'>🛠️ Plan d'Action — Actions concrètes</h3>",unsafe_allow_html=True)
    ca,cb,cc=st.columns(3)
    with ca:
        st.markdown("<div class='sh' style='color:#f85149'>🔴 TD — Disponibilité ≥ 90%</div>",unsafe_allow_html=True)
        for t,p,d,o in [
            ("Maintenance Préventive","Priorité 1","Plan basé sur MTBF. Remplacement avant défaillance. Objectif : -40% pannes.","GMAO"),
            ("Analyse MTBF/MTTR","Priorité 1","Calculer temps moyen entre pannes et réparation. Prioriser équipements critiques.","Analyse"),
            ("Maintenance Autonome","Priorité 2","Former les opérateurs : nettoyage, lubrification, inspection visuelle.","5S/TPM"),
            ("Standard Redémarrage","Priorité 3","Fiches standardisées. Viser MTTR < 30 min.","Standard Work"),
        ]:
            pc_="#f85149" if "1" in p else "#d29922" if "2" in p else "#8b949e"
            st.markdown(sol_block(t,p,d,o,"#2d1515","#f85149",pc_),unsafe_allow_html=True)
    with cb:
        st.markdown("<div class='sh' style='color:#d29922'>🟡 TP — Performance ≥ 95%</div>",unsafe_allow_html=True)
        for t,p,d,o in [
            ("SMED — Changements outils","Priorité 1","Convertir opérations internes en externes. Objectif : -50%.","SMED/Lean"),
            ("Élimination Arrêts Mineurs","Priorité 1","Analyser causes racines (OPL). Capteurs détection précoce.","OPL"),
            ("5S & Nettoyage Standard","Priorité 2","Standardiser durées nettoyage. Intégrer maintenance autonome.","5S"),
            ("Optimisation flux","Priorité 2","Spaghetti diagram. Réorganiser implantation.","VSM"),
            ("SPC — Dérive machine","Priorité 3","Détecter dérives avant réglage. Objectif : -60% réglages.","SPC"),
        ]:
            pc_="#f85149" if "1" in p else "#d29922" if "2" in p else "#8b949e"
            st.markdown(sol_block(t,p,d,o,"#2d2010","#d29922",pc_),unsafe_allow_html=True)
    with cc:
        st.markdown("<div class='sh' style='color:#3fb950'>🟢 TQ — Qualité ≥ 98%</div>",unsafe_allow_html=True)
        for t,p,d,o in [
            ("Poka-Yoke Démarrage","Priorité 1","Paramètres standardisés par produit. 0 rejet après J+3.","Poka-Yoke"),
            ("AMDEC Processus","Priorité 1","Identifier étapes critiques par IPR. Découpe et Peinture prioritaires.","AMDEC"),
            ("Autocontrôle Opérateur","Priorité 2","Standards photo. Objectif : 100% détection au poste.","Autocontrôle"),
            ("Capabilité Cp/Cpk","Priorité 2","Cpk < 1,33 → processus non capable. Réglages SPC.","SPC"),
        ]:
            pc_="#f85149" if "1" in p else "#d29922" if "2" in p else "#8b949e"
            st.markdown(sol_block(t,p,d,o,"#0d1f0d","#3fb950",pc_),unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div class='sh'>📅 Roadmap — Horizon 10 Tranches</div>",unsafe_allow_html=True)
    rm={"Action":["Maintenance Préventive","SMED Outils","5S Nettoyage","Poka-Yoke Démarrage",
                  "AMDEC Processus","SPC/Capabilité","Maintenance Autonome","Optimisation flux"],
        "Famille":["TD","TP","TP","TQ","TQ","TQ","TD","TP"],
        "Début":[1,1,2,1,2,3,3,4],"Fin":[4,3,10,4,5,10,10,10],
        "Impact":["+5%","+4%","+2%","+3%","+2%","+2%","+3%","+2%"]}
    rdf2=pd.DataFrame(rm); fam_c={"TD":"#f85149","TP":"#d29922","TQ":"#3fb950"}
    fig_rm=go.Figure(); shown=set()
    for _,row in rdf2.iterrows():
        c=fam_c.get(row["Famille"],"#58a6ff"); sl=row["Famille"] not in shown; shown.add(row["Famille"])
        fig_rm.add_trace(go.Bar(x=[row["Fin"]-row["Début"]+1],y=[row["Action"]],base=[row["Début"]-1],
            orientation="h",marker_color=c,marker_line_color="rgba(0,0,0,0)",
            name=row["Famille"],showlegend=sl,
            text=f" {row['Impact']}",textposition="inside",textfont=dict(color="white",size=10)))
    fig_rm.update_layout(height=270,**BL,barmode="overlay",
        xaxis=dict(**ax(),title=dict(text="Tranches",font=dict(color=MUTED)),
                   tickmode="array",tickvals=list(range(1,11)),ticktext=[f"T{i}" for i in range(1,11)]),
        yaxis=ax())
    fig_rm.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED,size=11)))
    st.plotly_chart(fig_rm,use_container_width=True)

    st.markdown("---")
    st.markdown("<h3 style='font-family:Rajdhani;font-size:1.4rem;color:#3fb950;letter-spacing:1px;margin-bottom:14px'>📊 Gains obtenus après application du plan d'action</h3>",unsafe_allow_html=True)

    for dept,dc in DEPT_COLORS.items():
        act=actuals[dept]; tgt=TARGETS[dept]; kpis=["TD","TP","TQ","TRS"]
        ann_cols=st.columns(4)
        for i,kpi in enumerate(kpis):
            a=act[kpi]; t=tgt[kpi]; delta=t-a
            with ann_cols[i]:
                st.markdown(f"""<div style='text-align:center;padding:4px 0'>
<div style='color:#8b949e;font-size:0.82rem'>{a:.1f}%</div>
<div style='color:{dc};font-size:0.9rem;font-weight:700'>↑ +{delta:.1f}pts</div>
<div style='color:#3fb950;font-family:Rajdhani;font-size:1.2rem;font-weight:700'>{t:.1f}%</div>
<div style='color:#8b949e;font-size:0.7rem;text-transform:uppercase'>{kpi}</div>
</div>""",unsafe_allow_html=True)
        fig_ab=go.Figure()
        fig_ab.add_trace(go.Bar(name="Actuel",x=kpis,y=[act[k] for k in kpis],
            marker_color="#4a5568",marker_line_color="rgba(0,0,0,0)",
            text=[f"{act[k]:.1f}%" for k in kpis],textposition="outside",textfont=dict(color=TEXT,size=10)))
        fig_ab.add_trace(go.Bar(name="Objectif",x=kpis,y=[tgt[k] for k in kpis],
            marker_color=dc,marker_line_color="rgba(0,0,0,0)",
            text=[f"{tgt[k]:.1f}%" for k in kpis],textposition="outside",textfont=dict(color=TEXT,size=10)))
        fig_ab.add_trace(go.Scatter(x=kpis,y=[act[k] for k in kpis],mode="lines",
            line=dict(color="#f85149",width=1.5,dash="dash"),showlegend=False,hoverinfo="skip"))
        fig_ab.update_layout(barmode="group",height=290,**BL,
            title=dict(text=f"Gains — {dept}",font=dict(color=MUTED,size=11)),
            xaxis=ax(),yaxis=ax(pct=True))
        fig_ab.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED,size=11)))
        fig_ab.update_yaxes(range=[0,115]); st.plotly_chart(fig_ab,use_container_width=True)
        st.markdown("<hr style='border-color:#1e2430;margin:6px 0'>",unsafe_allow_html=True)

    st.markdown("<div class='sh'>Production Supplémentaire Estimée</div>",unsafe_allow_html=True)
    ep1,ep2,ep3,ep4=st.columns(4)
    for col_,dept in zip([ep1,ep2,ep3],["Découpe","Usinage","Peinture"]):
        with col_:
            st.markdown(f"""<div style='background:#161b22;border:1px solid #21262d;border-radius:10px;padding:14px 18px;border-left:3px solid {DEPT_COLORS[dept]}'>
<div style='color:#8b949e;font-size:0.62rem;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:3px'>Unités/jour gagnées</div>
<div style='color:#3fb950;font-family:Rajdhani;font-size:2rem;font-weight:700'>+{EXTRA_PROD[dept]}</div>
<div style='color:#8b949e;font-size:0.7rem'>{dept}</div>
</div>""",unsafe_allow_html=True)
    with ep4:
        ann=min(EXTRA_PROD.values())*250
        st.markdown(f"""<div style='background:linear-gradient(135deg,#0d1f0d,#1a2c1a);border:1px solid #3fb950;border-radius:10px;padding:14px 18px'>
<div style='color:#8b949e;font-size:0.62rem;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:3px'>Gain annuel total</div>
<div style='color:#3fb950;font-family:Rajdhani;font-size:2rem;font-weight:700'>+{ann:,}</div>
<div style='color:#8b949e;font-size:0.7rem'>unités sur 250 jours</div>
</div>""",unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown("""<div style='background:linear-gradient(135deg,#161b22,#1c2128);border:1px solid #1f6feb;border-radius:10px;padding:14px 20px'>
<p style='color:#58a6ff;font-weight:700;margin:0 0 6px;font-family:Rajdhani;font-size:1rem'>💡 Synthèse — Gain TRS estimé</p>
<p style='color:#8b949e;font-size:0.78rem;margin:0;line-height:1.8'>
Actions priorité 1 et 2 → gain cumulé estimé <span style='color:#3fb950;font-weight:700'>+15% à +45%</span> selon le département.
<strong style='color:#58a6ff'>Découpe</strong> : maintenance préventive (pannes fréquentes).
<strong style='color:#3fb950'>Usinage</strong> : SMED (TP le plus faible).
<strong style='color:#d29922'>Peinture</strong> : Poka-Yoke (rejets les plus élevés).
</p></div>""",unsafe_allow_html=True)
