# Hook (shown at the top of the Executive Overview) and page 2 : context, decision-maker, questions, data
import pandas as pd
import streamlit as st

from src.config import MOIS, SOURCE_TER, SOURCE_TGV
from src.kpis import filtrer, regularite, annulation, fmt_pct


def accroche(d, f):
    # HOOK : why does this problem matter ? (first block of the app, above the executive KPIs)
    ter_p = filtrer(d['ter'], f['annee'], f['mois'], f['regions'])
    tgv_p = filtrer(d['tgv'], f['annee'], f['mois'])
    tgv_p = tgv_p[tgv_p['axe'].isin(f['axes'])]
    reg_ter, reg_tgv = regularite(ter_p), regularite(tgv_p)
    ann_ter = annulation(ter_p)

    accroche = st.container(border=True)
    if pd.notna(reg_tgv) and pd.notna(reg_ter):
        accroche.markdown(f"### Sur la période sélectionnée, **1 TGV sur {100 / (100 - reg_tgv):.0f}** est arrivé en "
                          f"retard, ainsi que **{fmt_pct(100 - reg_ter)} des TER**.")
    accroche.write(
        "La ponctualité est le premier critère de satisfaction des voyageurs du train. Pour une Région, qui "
        "finance et organise les TER, chaque point de régularité perdu signifie des correspondances manquées, des "
        "salariés et des étudiants en retard, et des voyageurs qui reprennent leur voiture. "
        f"S'y ajoutent les trains supprimés : **{fmt_pct(ann_ter)}** des TER programmés n'ont pas circulé. "
        "Ce tableau de bord aide la direction des transports d'un Conseil régional à suivre la régularité TER, "
        "à la comparer au TGV et aux autres régions, et à décider où agir.")


def afficher(d, f):

    # 2. Decision-maker and decisions
    st.header('Pour qui ? Pour quelles décisions ?')
    gauche, droite = st.columns(2)
    with gauche.container(border=True):
        st.subheader(':material/account_balance: Décideur cible')
        st.write("**La direction des transports d'un Conseil régional** (autorité organisatrice des TER), "
                 "et ses interlocuteurs chez SNCF Voyageurs et SNCF Réseau.")
        st.write('Elle pilote la convention TER (objectifs de régularité, pénalités), et défend la qualité de '
                 'la desserte TGV de son territoire auprès de l\'État et de SNCF.')
    with droite.container(border=True):
        st.subheader(':material/gavel: Décisions appuyées par le dashboard')
        st.write(':material/check_circle: Fixer et suivre un objectif de régularité, déclencher un plan d\'action')
        st.write(':material/check_circle: Comparer sa région à la moyenne nationale et aux autres régions')
        st.write(':material/check_circle: Identifier les liaisons TGV et les mois qui dégradent le service')
        st.write(':material/check_circle: Cibler les causes sur lesquelles agir (infrastructure, matériel...)')

    # 3. Business questions
    st.header('Questions analytiques')
    questions = [
        ('Q1', 'Comment la ponctualité TER et TGV a-t-elle évolué depuis 2018 ? L\'année en cours est-elle meilleure ou pire ?', 'Executive Overview'),
        ('Q2', 'Quelles régions ont la meilleure et la moins bonne régularité TER, et lesquelles sont sous le seuil d\'alerte ?', 'TER : analyse régionale'),
        ('Q3', 'Quelles liaisons TGV et quelles causes expliquent les retards ?', 'TGV : liaisons & causes'),
        ('Q4', 'Dans chaque région, le TGV fait-il mieux ou moins bien que le TER ? Les deux évoluent-ils ensemble ?', 'Comparaison TER vs TGV'),
        ('Q5', 'Y a-t-il des mois « à risque » qui reviennent chaque année ?', 'TER : analyse régionale'),
    ]
    for code, texte, page in questions:
        st.markdown(f'**{code}** — {texte} &nbsp; :gray-badge[{page}]')

    # 4. CONTEXT : what does the data describe ?
    st.header('Les données')
    col1, col2 = st.columns(2)
    with col1.container(border=True):
        st.subheader(':material/directions_railway: Régularité mensuelle TER')
        st.write('Source : SNCF, publiée sur [data.gouv.fr](' + SOURCE_TER + ') (licence ODbL).')
        st.write(f"**{len(d['ter_brut']):,} lignes** · une ligne = un mois × une région (ou un lot) · "
                 f"janvier 2013 → {MOIS[f['dernier_mois'].month - 1]} {f['dernier_mois'].year}".replace(',', ' '))
        st.write('Mesures : trains programmés, ayant circulé, annulés, en retard à l\'arrivée, taux de régularité.')
    with col2.container(border=True):
        st.subheader(':material/train: Régularité mensuelle TGV par liaison')
        st.write('Source : SNCF / AQST, publiée sur [data.gouv.fr](' + SOURCE_TGV + ') (licence ODbL).')
        st.write(f"**{len(d['tgv_brut']):,} lignes** · une ligne = un mois × une liaison (gare → gare) · "
                 "janvier 2018 → septembre 2026".replace(',', ' '))
        st.write('Mesures : circulations prévues, annulations, retards (> 15, 30, 60 min), retard moyen, '
                 'répartition des causes de retard.')
    st.info("**Pourquoi combiner les deux ?** Le TGV sert de *benchmark* au TER : les deux circulent sur le même "
            "réseau. Si une région est mauvaise en TER **et** en TGV, la cause est probablement territoriale "
            "(infrastructure, saturation, météo) ; si seul le TER décroche, elle est plutôt liée à l'exploitation "
            "régionale. Jointure : mois × région, la région d'une liaison TGV étant celle de ses gares.",
            icon=':material/join_inner:')

    # Reading guide (story arc)
    expander = st.expander('Comment lire ce dashboard', icon=':material/menu_book:')
    expander.write('1. **Executive Overview** : la situation en un coup d\'œil (KPI vs année précédente).')
    expander.write('2. **Contexte & questions** puis **Données & qualité** : décideur, questions, sources, nettoyage.')
    expander.write('3. **TER** puis **TGV** : où, quand, sur quelles liaisons et pour quelles causes.')
    expander.write('4. **Comparaison** : benchmark TER vs TGV et scorecard des régions.')
    expander.write('5. **Decision Support / Recommendations** : 3 constats, 2 recommandations, 1 limite.')
    expander.write('Les filtres de la barre latérale (année, mois, régions, seuil, axes TGV) s\'appliquent à toutes les pages.')
