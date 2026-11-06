# BDML1 Individual Project — La ponctualité ferroviaire en France (TER vs TGV)
# Thomas BELOT — 2ème année ingénieur, apprentissage, Big Data & Machine Learning (I2-APP-BDML1) — Efrei
# Professeur : Mano Joseph MATHEW
# Run with : streamlit run app.py
import streamlit as st

from src.config import MOIS, SEUIL_DEFAUT, LOGO
from src.data import charger_ter, ter_regional, charger_tgv, tgv_nettoye, tgv_par_region
from src.sections import accueil, executif, ter, tgv, comparaison, qualite, decision

# Page configuration (title of the tab, icon and wide layout)
# The colors and fonts of the page are defined in .streamlit/config.toml (same theme as my portfolio)
st.set_page_config(page_title='Ponctualité ferroviaire — TER vs TGV', page_icon=':material/train:',
                   layout='wide')

# Loading the data only once (st.cache_data in src/data.py)
with st.spinner('Chargement des données SNCF...'):
    ter_brut, ter_detail = charger_ter()
    ter_reg = ter_regional()
    tgv_brut, _ = charger_tgv()
    tgv_df, journal_tgv = tgv_nettoye()
    tgv_reg = tgv_par_region()
# TGV analysed only up to the last TER month : both datasets cover exactly the same period
dernier_mois = ter_reg['date'].max()
tgv_df = tgv_df[tgv_df['date'] <= dernier_mois]
tgv_reg = tgv_reg[tgv_reg['date'] <= dernier_mois]
donnees = {'ter': ter_reg, 'ter_detail': ter_detail, 'ter_brut': ter_brut, 'tgv': tgv_df, 'tgv_reg': tgv_reg,
           'tgv_brut': tgv_brut, 'journal_tgv': journal_tgv}

# Sidebar : Efrei logo, title, navigation
# The app begins with the Executive Overview (hook + context + KPIs), then : context -> data -> analysis ->
# comparison -> decision support (final section)
st.sidebar.image(str(LOGO), width='stretch')
st.sidebar.title(':material/train: Ponctualité ferroviaire')
st.sidebar.caption('TER vs TGV — France, 2018-2026')
PAGES = {
    'Executive Overview': (':material/dashboard:', executif),
    'Contexte & questions': (':material/flag:', accueil),
    'Données & qualité': (':material/fact_check:', qualite),
    'TER : analyse régionale': (':material/map:', ter),
    'TGV : liaisons & causes': (':material/route:', tgv),
    'Comparaison TER vs TGV': (':material/compare_arrows:', comparaison),
    'Decision Support / Recommendations': (':material/lightbulb:', decision),
}
page = st.sidebar.radio('Navigation', list(PAGES), format_func=lambda p: f'{PAGES[p][0]} {p}')
st.sidebar.divider()

# Global filters, shared by every page
st.sidebar.subheader(':material/filter_alt: Filtres')
annees = sorted(a for a in ter_reg['annee'].unique() if a >= 2019)
annee = st.sidebar.selectbox("Année d'analyse", annees, index=len(annees) - 1,
                             help='Comparée automatiquement aux mêmes mois de l\'année précédente.')
mois_max = dernier_mois.month if annee == dernier_mois.year else 12
mois = st.sidebar.select_slider('Mois', options=list(range(1, mois_max + 1)), value=(1, mois_max),
                                format_func=lambda m: MOIS[m - 1])
toutes_regions = sorted(ter_reg['region'].unique())
regions = st.sidebar.multiselect('Régions', toutes_regions, default=toutes_regions,
                                 placeholder='Toutes les régions')
if not regions:
    regions = toutes_regions
seuil = st.sidebar.slider("Seuil d'alerte régularité (%)", 80.0, 96.0, SEUIL_DEFAUT, 0.5,
                          help='En dessous de ce taux, une région ou une liaison est signalée « à surveiller ».')
axes = st.sidebar.pills('Axes TGV', sorted(tgv_df['axe'].unique()), selection_mode='multi',
                        default=sorted(tgv_df['axe'].unique()))
if not axes:
    axes = sorted(tgv_df['axe'].unique())

st.sidebar.divider()
st.sidebar.caption(f'Données SNCF / AQST via data.gouv.fr · dernier mois commun : '
                   f'{MOIS[dernier_mois.month - 1]} {dernier_mois.year}')

# Author and course information
st.sidebar.divider()
st.sidebar.subheader(':material/person: Auteur')
st.sidebar.write('**Thomas BELOT**')
st.sidebar.caption('2ème année ingénieur - apprentissage - Big Data & Machine Learning')
st.sidebar.caption('Groupe(s) : I2-APP-BDML1')
st.sidebar.write(':material/mail: [thomas.belot@efrei.net](mailto:thomas.belot@efrei.net)')
st.sidebar.write(':material/link: [LinkedIn](https://www.linkedin.com/in/thomas-belot/)')
st.sidebar.write(':material/code: [Code source (GitHub)](https://github.com/Thomsys/Streamlit_20261785_BELOT_BDML1)')
st.sidebar.subheader(':material/school: Professeur')
st.sidebar.write('**Mano Joseph MATHEW**')
st.sidebar.write(':material/mail: [mano.mathew@efrei.fr](mailto:mano.mathew@efrei.fr)')

filtres = {'annee': annee, 'mois': mois, 'regions': regions, 'seuil': seuil, 'axes': axes,
           'dernier_mois': dernier_mois, 'toutes_regions': toutes_regions}

# Title of the app, then the selected page
st.title('La ponctualité ferroviaire en France (TER vs TGV)')
periode = f'{MOIS[mois[0] - 1]}–{MOIS[mois[1] - 1]} {annee}' if mois[0] != mois[1] else f'{MOIS[mois[0] - 1]} {annee}'
badges = st.container(horizontal=True)
badges.badge(f'Période : {periode}', icon=':material/calendar_month:', color='blue')
badges.badge(f'Comparée à : même période {annee - 1}', icon=':material/history:', color='gray')
badges.badge(f'{len(regions)} région(s)', icon=':material/location_on:', color='green')
badges.badge(f'Seuil : {seuil:.1f} %'.replace('.', ','), icon=':material/warning:', color='orange')

PAGES[page][1].afficher(donnees, filtres)
