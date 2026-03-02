import streamlit as st
import pandas as pd
import requests
import gspread
from google.oauth2.service_account import Credentials

VAXTER_PER_SIDA = 12  # 588 växter

@st.cache_data(ttl=300)
def ladda_databas():
    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)
    blad = gc.open_by_key("1Pax0R2T-vQ8vZ9NAvSfac1N5tS55a26QOynWRnScQAI").sheet1
    rows = blad.get_all_values()
    max_kol = len(rows[0])
    for rad in rows[1:]:
        while len(rad) < max_kol:
            rad.append("")
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df["zon_min"] = pd.to_numeric(df["zon_min"])
    df["blomning_start"] = pd.to_numeric(df["blomning_start"])
    df["blomning_slut"] = pd.to_numeric(df["blomning_slut"])
    return df

def sok_filter(df, zon, sol, jord, stil, farg, typ, hojd, blom_fran, blom_till):
    res = df.copy()
    if sol: res = res[res["sol"] == sol]
    if zon: res = res[res["zon_min"] <= zon]
    jord_kol = "jordmån" if "jordmån" in res.columns else "jordman"
    if jord: res = res[res[jord_kol].isin([jord, "alla"])]
    if stil: res = res[res["stil"] == stil]
    farg_kol = "färg" if "färg" in res.columns else "farg"
    if farg: res = res[res[farg_kol] == farg]
    hojd_kol = "höjd" if "höjd" in res.columns else "hojd"
    if typ: res = res[res["typ"] == typ]
    if hojd: res = res[res[hojd_kol] == hojd]
    if blom_fran and blom_till:
        res = res[res["blomning_start"] > 0]
        res = res[(res["blomning_start"] <= blom_till) & (res["blomning_slut"] >= blom_fran)]
    return res

def vaxt_kort(v, visa_bilder):
    bild_url = v.get("bild_url", "")
    if visa_bilder:
        if bild_url and "Disambig" not in bild_url and "No_image" not in bild_url:
            st.image(bild_url, use_container_width=True)
        else:
            st.markdown('<div style="background:#e8f5e9;height:150px;display:flex;align-items:center;justify-content:center;font-size:50px;border-radius:8px 8px 0 0">🌿</div>', unsafe_allow_html=True)
    hv = v.get("höjd", v.get("hojd", ""))
    fv = v.get("färg", v.get("farg", ""))
    skotsel = v.get("skötselråd", "")
    st.markdown(f'<div style="background:#f0f7f0;border-left:4px solid #2d7a2d;border-radius:0 0 8px 8px;padding:12px;margin-bottom:4px"><strong style="font-size:16px">{v["namn"]}</strong><br><span style="color:#555">{v["blomning_text"]} | {hv} | {v["typ"]}</span><br><span style="color:#777">{fv} | {v["stil"]}</span></div>', unsafe_allow_html=True)
    if skotsel:
        with st.expander("Skötselråd"):
            st.markdown(f"🌱 {skotsel}")

st.set_page_config(page_title="Trädgårdsväljaren", layout="wide", page_icon="🌿")
st.markdown("""<style>
.main { background-color: #f9fdf9; }
.stButton>button { background-color: #2d7a2d; color: white; border-radius: 8px; border: none; padding: 8px 20px; }
.stButton>button:hover { background-color: #1f5c1f; }
</style>""", unsafe_allow_html=True)

st.title("Växtväljaren")
st.caption("Hitta rätt växt för just din trädgård")

df = ladda_databas()
sok_text = st.text_input("Sök växt direkt på namn", placeholder="t.ex. Tomat, Ros, Lavendel...")

with st.sidebar:
    st.markdown("## Filtrera växter")
    st.markdown("**Filter**")
    zon = st.slider("Växtzon (visa växter upp till och med zon)", 1, 8, 8)
    sol = st.selectbox("Solförhållanden", ["", "sol", "halvskugga", "skugga"])
    jord = st.selectbox("Jordmån", ["", "mull", "lera", "sand", "normal", "fuktig", "torr"])
    stil = st.selectbox("Trädgårdsstil", [""] + ["romantisk","japansk","modern","medelhav","gammaldags","cottage","vildträdgård","formell","nordisk","köksträdgård","krukodling"])
    st.divider()
    st.markdown("**Valfria filter**")
    farg = st.selectbox("Blomfärg", [""] + ["vit","rosa","röd","lila","blå","gul","orange","blandad","grön","svart"])
    typ = st.selectbox("Växttyp", [""] + ["perenn","annuell","buske","träd","klätterväxt","lök","gräs","ormbunke","grönsak","frukt","krydda","ros","dahlia","clematis","pelargon"])
    hojd = st.selectbox("Höjd", [""] + ["låg","medel","hög"])
    st.divider()
    st.markdown("**Blomningsperiod**")
    manad = ["jan","feb","mar","apr","maj","jun","jul","aug","sep","okt","nov","dec"]
    blom_fran, blom_till = st.select_slider("Välj period", options=list(range(1,13)), value=(1,12), format_func=lambda x: manad[x-1])
    anvand_blomning = st.checkbox("Filtrera på blomningsperiod")
    st.divider()
    visa_bilder = st.toggle("Visa bilder", value=True)

st.divider()

if sok_text.strip():
    sok_lower = sok_text.strip().lower()
    sokresultat = df[df["namn"].str.lower().str.contains(sok_lower, na=False)]
    st.subheader(f"{len(sokresultat)} träffar på '{sok_text}'")
    if len(sokresultat) == 0:
        st.warning("Ingen växt hittades med det namnet.")
    else:
        cols = st.columns(3)
        for i, (_, v) in enumerate(sokresultat.iterrows()):
            with cols[i % 3]:
                vaxt_kort(v, visa_bilder)
else:
    stil_map = {"vildträdgård": "vildträdgård", "köksträdgård": "köksträdgård"}
    stil_sok = stil_map.get(stil, stil) or None
    resultat = sok_filter(df, zon, sol, jord, stil_sok, farg or None, typ or None, hojd or None,
                   blom_fran if anvand_blomning else None, blom_till if anvand_blomning else None)
    totalt = len(resultat)
    kol_a, kol_b = st.columns([3,1])
    with kol_a:
        st.subheader(f"Växter hittades: {totalt}")
    with kol_b:
        st.metric("Zon", f"Zon {zon}")
    if totalt == 0:
        st.warning("Inga växter hittades. Prova att ändra filtren.")
    else:
        antal_sidor = max(1, -(-totalt // VAXTER_PER_SIDA))
        if "sida" not in st.session_state: st.session_state.sida = 0
        if st.session_state.sida >= antal_sidor: st.session_state.sida = 0
        start = st.session_state.sida * VAXTER_PER_SIDA
        slut = min(start + VAXTER_PER_SIDA, totalt)
        sida_resultat = resultat.iloc[start:slut]
        st.caption(f"Visar {start+1}-{slut} av {totalt} växter  |  Sida {st.session_state.sida+1} av {antal_sidor}")
        cols = st.columns(3)
        for i, (_, v) in enumerate(sida_resultat.iterrows()):
            with cols[i % 3]:
                vaxt_kort(v, visa_bilder)
        st.divider()
        c1, c2, c3 = st.columns([1,2,1])
        with c1:
            if st.button("Föregående") and st.session_state.sida > 0:
                st.session_state.sida -= 1
                st.rerun()
        with c2:
            st.markdown(f'<p style="text-align:center;color:#2d7a2d;font-weight:bold">Sida {st.session_state.sida+1} av {antal_sidor}</p>', unsafe_allow_html=True)
        with c3:
            if st.button("Nästa") and st.session_state.sida < antal_sidor - 1:
                st.session_state.sida += 1
                st.rerun()
        with st.expander("Visa som tabell"):
            st.dataframe(resultat[["namn","blomning_text","typ","stil"]], use_container_width=True, hide_index=True)
