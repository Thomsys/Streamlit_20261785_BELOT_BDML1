# Page 2 : Executive overview — the main situation without reading every chart
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.charts import style_plotly, afficher_plotly, question, lecture
from src.config import COULEUR_TER, COULEUR_TGV, COULEUR_ALERTE, COULEUR_OK, GRIS, MOIS
from src.sections.accueil import accroche
from src.kpis import (filtrer, regularite, annulation, part, retard_moyen, par_groupe, mensuel, evolution,
                      fmt_pct, fmt_pts, fmt_nb, tgv_filtre)


def afficher(d, f):
    st.header('Executive Overview')
    # 1. Hook and context, then 2. the executive KPIs
    accroche(d, f)
    annee, mois, regions, seuil = f['annee'], f['mois'], f['regions'], f['seuil']

    # Current period and same months of the previous year
    ter_n = filtrer(d['ter'], annee, mois, regions)
    ter_n1 = filtrer(d['ter'], annee - 1, mois, regions)
    tgv_all = tgv_filtre(d, f)
    tgv_n, tgv_n1 = filtrer(tgv_all, annee, mois), filtrer(tgv_all, annee - 1, mois)

    reg_ter, reg_ter1 = regularite(ter_n), regularite(ter_n1)
    reg_tgv, reg_tgv1 = regularite(tgv_n), regularite(tgv_n1)
    ann_ter, ann_ter1 = annulation(ter_n), annulation(ter_n1)
    r15, r15_1 = part(tgv_n, 'retards_15'), part(tgv_n1, 'retards_15')
    rm, rm1 = retard_moyen(tgv_n), retard_moyen(tgv_n1)

    # Sparklines (last 24 months) inside the two main KPI cards
    fin = pd.Timestamp(f'{annee}-{mois[1]:02d}-01')
    spark_ter = mensuel(d['ter'][d['ter']['region'].isin(regions) & ~d['ter']['partiel']
                                 & d['ter']['date'].between(fin - pd.DateOffset(months=23), fin)])['regularite'].round(1)
    spark_tgv = mensuel(tgv_all[tgv_all['date'].between(fin - pd.DateOffset(months=23), fin)], prevus='prevus')['regularite'].round(1)

    # Row 1 : the 5 main KPIs (each one answers a management question)
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric('Régularité TER', fmt_pct(reg_ter), fmt_pts(evolution(reg_ter, reg_ter1)), border=True, chart_data=list(spark_ter), chart_type='area',
                help='Part des TER ayant circulé arrivés à l\'heure (retard < 5 min). Évolution vs mêmes mois N-1. Courbe : 24 derniers mois.')
    col2.metric('Régularité TGV', fmt_pct(reg_tgv), fmt_pts(evolution(reg_tgv, reg_tgv1)), border=True, chart_data=list(spark_tgv), chart_type='area',
                help='Part des TGV ayant circulé arrivés à l\'heure (définition AQST). Courbe : 24 derniers mois.')
    col3.metric('Annulations TER', fmt_pct(ann_ter), fmt_pts(evolution(ann_ter, ann_ter1)),
                delta_color='inverse', border=True, help='Trains annulés / trains programmés.')
    col4.metric('TGV > 15 min de retard', fmt_pct(r15), fmt_pts(evolution(r15, r15_1)), delta_color='inverse',
                border=True, help='Part des TGV ayant circulé arrivés avec plus de 15 min de retard.')
    col5.metric('Retard moyen TGV', '—' if pd.isna(rm) else f'{rm:.0f} min',
                None if pd.isna(rm1) or pd.isna(rm) else f'{rm - rm1:+.1f} min'.replace('.', ','),
                delta_color='inverse', border=True,
                help='Retard moyen à l\'arrivée des TGV en retard (pondéré par le nombre de trains en retard).')

    # Row 2 : regional benchmark (best / worst region, number of regions under the threshold)
    table = par_groupe(ter_n[~ter_n['partiel']], 'region')
    table1 = par_groupe(ter_n1[~ter_n1['partiel']], 'region')
    table = table.merge(table1[['region', 'regularite']], on='region', how='left', suffixes=('', '_n1'))
    sous_seuil = table[table['regularite'] < seuil].sort_values('regularite')
    col1, col2, col3, col4 = st.columns(4)
    if not table.empty:
        meilleure = table.loc[table['regularite'].idxmax()]
        pire = table.loc[table['regularite'].idxmin()]
        col1.metric('Meilleure région TER', meilleure['region'], fmt_pct(meilleure['regularite']),
                    delta_color='off', delta_arrow='off', border=True)
        col2.metric('Région la moins ponctuelle', pire['region'], fmt_pct(pire['regularite']),
                    delta_color='off', delta_arrow='off', border=True)
    col3.metric(f'Régions sous le seuil ({seuil:.0f} %)', f'{len(sous_seuil)} / {len(table)}',
                ', '.join(sous_seuil['region'].head(3)) or 'aucune', delta_color='off', delta_arrow='off', border=True)
    col4.metric('Trains TER programmés', fmt_nb(ter_n['programmes'].sum()),
                None if ter_n1.empty else f"{100 * (ter_n['programmes'].sum() / ter_n1['programmes'].sum() - 1):+.1f} %".replace('.', ','),
                delta_color='off', delta_arrow='off', border=True)

    # Automatic one-sentence summary for management
    sens = 'se dégrade' if (evolution(reg_ter, reg_ter1) or 0) < 0 else 'progresse'
    ecart = f'{abs(reg_tgv - reg_ter):.1f}'.replace('.', ',')
    st.info(f"**En résumé :** sur {MOIS[mois[0] - 1]}–{MOIS[mois[1] - 1]} {annee}, la régularité TER {sens} "
            f"({fmt_pts(evolution(reg_ter, reg_ter1)) or 'n.d.'} vs {annee - 1}) et celle du TGV évolue de "
            f"{fmt_pts(evolution(reg_tgv, reg_tgv1)) or 'n.d.'}. Le TGV reste {ecart} points "
            f"{'sous' if reg_tgv < reg_ter else 'au-dessus du'} TER. "
            f"{len(sous_seuil)} région(s) sur {len(table)} sont sous le seuil d'alerte.", icon=':material/summarize:')

    # Chart 1 : monthly trend since 2018, TER vs TGV, threshold and selected year highlighted
    question('Comment la ponctualité a-t-elle évolué depuis 2018 ? (Q1)')
    ter_m = mensuel(d['ter'][d['ter']['region'].isin(regions) & ~d['ter']['partiel'] & (d['ter']['date'] >= '2018-01')])
    tgv_m = mensuel(tgv_all, prevus='prevus')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ter_m['date'], y=ter_m['regularite'], name='TER', line=dict(color=COULEUR_TER, width=2.5),
                             hovertemplate='%{x|%b %Y} : %{y:.1f} %<extra>TER</extra>'))
    fig.add_trace(go.Scatter(x=tgv_m['date'], y=tgv_m['regularite'], name='TGV', line=dict(color=COULEUR_TGV, width=2.5),
                             hovertemplate='%{x|%b %Y} : %{y:.1f} %<extra>TGV</extra>'))
    fig.add_hline(y=seuil, line_dash='dot', line_color=COULEUR_ALERTE,
                  annotation_text=f'Seuil {seuil:.0f} %', annotation_position='bottom right')
    fig.add_vrect(x0=pd.Timestamp(f'{annee}-{mois[0]:02d}-01'), x1=pd.Timestamp(f'{annee}-{mois[1]:02d}-01') + pd.offsets.MonthEnd(0),
                  fillcolor=COULEUR_TER, opacity=0.08, line_width=0, annotation_text='Période analysée',
                  annotation_position='top left')
    # Annotations of the main events visible in the series
    for date, texte, y in [('2018-05-01', 'Grève 2018', 0.04), ('2019-12-01', 'Grève retraites', 0.04),
                           ('2020-04-01', 'Confinement', 0.12)]:
        fig.add_annotation(x=date, y=y, yref='paper', text=texte, showarrow=False, font=dict(size=10, color=GRIS))
    fig.update_yaxes(title='Taux de régularité (%)', ticksuffix=' %')
    fig.update_layout(title='Régularité mensuelle TER et TGV (2018-2026)', hovermode='x unified')
    afficher_plotly(style_plotly(fig, 420), 'tendance')

    # Chart 2 : yearly comparison (same months for every year -> fair comparison)
    gauche, droite = st.columns([3, 2])
    annuel = []
    for a in range(2018, f['dernier_mois'].year + 1):
        annuel.append({'Année': str(a), 'TER': regularite(filtrer(d['ter'][~d['ter']['partiel']], a, mois, regions)),
                       'TGV': regularite(filtrer(tgv_all, a, mois))})
    annuel = pd.DataFrame(annuel).melt('Année', var_name='Mode', value_name='Régularité')
    barres = px.bar(annuel, x='Année', y='Régularité', color='Mode', barmode='group', text_auto='.1f',
                    color_discrete_map={'TER': COULEUR_TER, 'TGV': COULEUR_TGV},
                    title=f'Régularité par année ({MOIS[mois[0] - 1]}–{MOIS[mois[1] - 1]} uniquement)')
    barres.update_yaxes(range=[70, 100], title='%')
    barres.update_traces(marker_line_color='white', marker_line_width=2, textfont_size=10)
    with gauche:
        afficher_plotly(style_plotly(barres, 380), 'annuel')

    # Chart 3 : regions to watch (ranking with threshold), red under the threshold
    table = table.sort_values('regularite')
    table['Statut'] = ['À surveiller' if v < seuil else 'Au-dessus du seuil' for v in table['regularite']]
    classement = px.bar(table, x='regularite', y='region', orientation='h', color='Statut',
                        color_discrete_map={'À surveiller': COULEUR_ALERTE, 'Au-dessus du seuil': COULEUR_OK},
                        text=table['regularite'].map(lambda v: f'{v:.1f}'),
                        title='Régularité TER par région', labels={'regularite': '%', 'region': ''})
    classement.add_vline(x=seuil, line_dash='dot', line_color=GRIS)
    classement.update_xaxes(range=[max(70, table['regularite'].min() - 3) if not table.empty else 70, 100])
    with droite:
        afficher_plotly(style_plotly(classement, 380), 'classement_exec')

    lecture(f"sur les mêmes mois, la meilleure année TER est {annuel[annuel.Mode == 'TER'].set_index('Année')['Régularité'].idxmax()} "
            f"et la meilleure année TGV est {annuel[annuel.Mode == 'TGV'].set_index('Année')['Régularité'].idxmax()}. "
            f"Le TGV est sous le TER chaque année.",
            "la comparaison « mêmes mois » évite de comparer un été à un hiver. Une baisse simultanée des deux "
            "modes pointe vers des causes communes au réseau (travaux, météo, mouvements sociaux).")
