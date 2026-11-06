# Page 7 : Decision Support / Recommendations — 3 key insights, 2 recommendations, 1 limitation
# The figures are recomputed from the data (they follow the filters) and refer to the charts of the other pages
import pandas as pd
import streamlit as st

from src.config import MOIS
from src.kpis import filtrer, regularite, par_groupe, causes, fmt_pct, fmt_pts, tgv_filtre


def afficher(d, f):
    st.header('Decision Support / Recommendations')
    annee, mois, seuil = f['annee'], f['mois'], f['seuil']
    periode = f"{MOIS[mois[0] - 1]}–{MOIS[mois[1] - 1]} {annee}"
    ter = d['ter'][~d['ter']['partiel'] & d['ter']['region'].isin(f['regions'])]
    tgv = tgv_filtre(d, f)

    # Evidence 1 : evolution vs previous year
    ter_n, ter_n1 = regularite(filtrer(ter, annee, mois)), regularite(filtrer(ter, annee - 1, mois))
    tgv_n, tgv_n1 = regularite(filtrer(tgv, annee, mois)), regularite(filtrer(tgv, annee - 1, mois))
    reg_n = par_groupe(filtrer(ter, annee, mois), 'region')
    reg_n1 = par_groupe(filtrer(ter, annee - 1, mois), 'region')
    evol = reg_n.merge(reg_n1[['region', 'regularite']], on='region', suffixes=('', '_n1'))
    en_recul = int((evol['regularite'] < evol['regularite_n1']).sum())
    annuel = {a: regularite(filtrer(ter, a, mois)) for a in range(2018, annee + 1)}
    rang_annee = sorted(annuel, key=annuel.get).index(annee) + 1

    # Evidence 2 : territorial gap
    sous_seuil = reg_n[reg_n['regularite'] < seuil].sort_values('regularite')
    ecart_regions = reg_n['regularite'].max() - reg_n['regularite'].min()

    # Evidence 3 : causes and seasonality
    c = causes(filtrer(tgv, annee, mois)) if annee < 2026 else causes(tgv[tgv['annee'].between(2022, 2025)])
    interne = c.loc[~c['Cause'].str.startswith('Externes'), 'Part'].sum()
    infra_trafic = c.loc[c['Cause'].str.startswith(('Infrastructure', 'Gestion du trafic')), 'Part'].sum()
    mensuel = ter[ter['date'] >= '2018-01'].groupby(['date', 'mois'])[['circules', 'retards']].sum().reset_index()
    mensuel['regularite'] = 100 * (1 - mensuel['retards'] / mensuel['circules'])
    profil = mensuel.groupby('mois')['regularite'].median()
    mois_faibles = [MOIS[m - 1] for m in profil.nsmallest(3).index]

    st.subheader(':material/insights: Trois constats clés')
    c1, c2, c3 = st.columns(3)
    with c1.container(border=True, height='stretch'):
        st.markdown('#### 1. Une dégradation générale')
        st.write(f"Sur {periode}, la régularité TER est de **{fmt_pct(ter_n)}** ({fmt_pts(ter_n - ter_n1)} vs {annee - 1}) "
                 f"et celle du TGV de **{fmt_pct(tgv_n)}** ({fmt_pts(tgv_n - tgv_n1)}). "
                 f"**{en_recul} régions sur {len(evol)}** reculent. Sur ces mêmes mois, {annee} est "
                 + (f"**la pire année TER depuis 2018**." if rang_annee == 1 else
                    f"la **{rang_annee}e plus mauvaise année** TER sur {len(annuel)} depuis 2018."))
        st.caption('Preuve : Executive Overview (KPI, courbe 2018-2026, barres par année).')
    with c2.container(border=True, height='stretch'):
        st.markdown('#### 2. Une fracture territoriale durable')
        st.write(f"**{ecart_regions:.1f} points** séparent la meilleure et la moins bonne région. "
                 f"{len(sous_seuil)} région(s) sont sous le seuil de {seuil:.0f} % : "
                 f"**{', '.join(sous_seuil['region']) or 'aucune'}**. Les régions faibles en TER le sont aussi en TGV : "
                 "le problème est lié au territoire (réseau, saturation, climat), pas seulement à l'exploitant.")
        st.caption('Preuve : carte et classement TER, nuage TER vs TGV (page Comparaison).')
    with c3.container(border=True, height='stretch'):
        st.markdown('#### 3. Des retards en grande partie actionnables et prévisibles')
        st.write(f"**{interne:.0f} %** des retards TGV relèvent de causes internes au système ferroviaire, dont "
                 f"**{infra_trafic:.0f} %** pour l'infrastructure et la gestion du trafic (périmètre SNCF Réseau). "
                 f"Les mois les plus faibles reviennent chaque année : **{', '.join(mois_faibles)}**.")
        st.caption('Preuve : page TGV (causes) et page TER (saisonnalité). '
                   + ('Causes calculées sur 2022-2025, à cause de la rupture de série de mai 2026.' if annee >= 2026 else ''))

    st.subheader(':material/recommend: Deux recommandations')
    r1, r2 = st.columns(2)
    with r1.container(border=True, height='stretch'):
        st.markdown('#### A. Lancer un plan d\'action ciblé sur les régions sous le seuil')
        cibles = ', '.join(sous_seuil['region'].head(3)) or 'les régions les plus faibles'
        st.write(f"Réunir pour **{cibles}** un comité Région – SNCF Voyageurs – SNCF Réseau, avec un objectif chiffré "
                 f"(revenir au-dessus de {seuil:.0f} %) et un suivi mensuel dans ce dashboard. Comme le TGV est aussi "
                 "dégradé sur ces territoires, prioriser les axes partagés (ex. Lyon – Marseille, liaisons "
                 "intersecteurs) dans les investissements de régénération et de régulation du trafic.")
        st.caption('Indicateur de succès : régularité TER de la région et écart à la moyenne France (benchmark).')
    with r2.container(border=True, height='stretch'):
        st.markdown('#### B. Anticiper les périodes à risque et fiabiliser la mesure')
        st.write(f"Préparer chaque année un plan dédié pour **{', '.join(mois_faibles)}** (adhérence des rails "
                 "à l'automne, intempéries l'hiver, chaleur et affluence l'été) : programmation des travaux hors de ces mois, renfort de maintenance, "
                 "information voyageurs. En parallèle, demander à SNCF la **publication des causes de retard pour le TER** "
                 "et une **méthode stable d'attribution des causes** (rupture constatée en mai 2026).")
        st.caption('Indicateur de succès : écart des mois à risque à la moyenne annuelle.')

    st.subheader(':material/block: Une limite')
    st.error("**Ce que le décideur ne doit pas conclure :** que le TGV est « moins bien géré » que le TER. "
             "L'écart observé entre les deux est en partie un effet de définition : un TER est compté en retard au-delà "
             "de 5 minutes, alors que pour le TGV le seuil dépend de la durée du trajet (définition AQST). "
             "La comparaison TER / TGV sert à repérer les territoires en difficulté, pas à juger les exploitants.",
             icon=':material/warning:')

    with st.expander('Preuve vs hypothèse', icon=':material/balance:'):
        st.write('**Observé dans les données** : niveaux et évolutions de régularité, classement des régions, mois faibles, '
                 'répartition des causes TGV, corrélation TER / TGV.')
        st.write('**Hypothèses / interprétation** : rôle du réseau partagé, explication saisonnière (feuilles, chaleur), '
                 'changement de méthode des causes en 2026, efficacité attendue des recommandations.')
