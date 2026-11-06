# Page 4 : TGV — which routes, which causes ? (axis -> route -> month drill-down, causes, stations map)
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.charts import style_plotly, afficher_plotly, question, lecture
from src.config import COULEUR_TGV, COULEUR_ALERTE, COULEUR_OK, GRIS, GARES, MOIS, couleurs
from src.data import charger_geojson
from src.kpis import (filtrer, regularite, annulation, part, retard_moyen, par_groupe, causes, fmt_pct, fmt_pts,
                      evolution, tgv_filtre)

COULEURS_CAUSES = ['#8a94a6', '#d64545', '#2a78d6', '#eda100', '#1baf7a', '#e87ba4']


def afficher(d, f):
    st.header('TGV : liaisons & causes de retard')
    tgv = tgv_filtre(d, f)
    n, n1 = filtrer(tgv, f['annee'], f['mois']), filtrer(tgv, f['annee'] - 1, f['mois'])

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric('Liaisons suivies', n['liaison'].nunique(), border=True)
    col2.metric('Régularité TGV', fmt_pct(regularite(n)), fmt_pts(evolution(regularite(n), regularite(n1))), border=True)
    col3.metric('Retard > 60 min', fmt_pct(part(n, 'retards_60'), 2),
                fmt_pts(evolution(part(n, 'retards_60'), part(n1, 'retards_60'))), delta_color='inverse', border=True)
    col4.metric('Annulations', fmt_pct(annulation(n, 'prevus')),
                fmt_pts(evolution(annulation(n, 'prevus'), annulation(n1, 'prevus'))), delta_color='inverse', border=True)
    rm = retard_moyen(n)
    col5.metric('Retard moyen (TGV en retard)', '—' if pd.isna(rm) else f'{rm:.0f} min', border=True)

    tab_1, tab_2, tab_3, tab_4 = st.tabs([':material/route: Axes & liaisons', ':material/build: Causes de retard',
                                          ':material/location_on: Carte des gares', ':material/scatter_plot: Durée vs ponctualité'])

    # Tab 1 : drill-down Axe -> Liaison -> Mois (Q3)
    with tab_1:
        question('Quelles liaisons TGV dégradent le plus la ponctualité ? (Q3)')
        axes = par_groupe(n, 'axe', 'prevus').sort_values('regularite')
        axes1 = par_groupe(n1, 'axe', 'prevus')[['axe', 'regularite']]
        axes = axes.merge(axes1, on='axe', how='left', suffixes=('', '_n1'))
        fig = go.Figure()
        fig.add_trace(go.Bar(y=axes['axe'], x=axes['regularite'], orientation='h', name=str(f['annee']),
                             marker_color=COULEUR_TGV, text=axes['regularite'].map(lambda v: f'{v:.1f}'),
                             textposition='outside'))
        fig.add_trace(go.Scatter(y=axes['axe'], x=axes['regularite_n1'], mode='markers', name=str(f['annee'] - 1),
                                 marker=dict(color='#1c2333', symbol='line-ns', size=22, line=dict(width=3))))
        fig.add_vline(x=f['seuil'], line_dash='dot', line_color=COULEUR_ALERTE)
        fig.update_xaxes(range=[60, 100], title='Régularité (%)')
        fig.update_layout(title='Régularité par axe (barre = année analysée, trait = année précédente)')
        afficher_plotly(style_plotly(fig, 330), 'axes')

        gauche, droite = st.columns([1, 2])
        axe = gauche.selectbox('Axe', ['Tous'] + list(axes.sort_values('regularite')['axe']))
        top_n = gauche.slider('Nombre de liaisons affichées', 5, 20, 10)
        sens = gauche.radio('Afficher', ['Les moins ponctuelles', 'Les plus ponctuelles'])
        liaisons = par_groupe(n if axe == 'Tous' else n[n['axe'] == axe], 'liaison', 'prevus')
        liaisons = liaisons[liaisons['circules'] >= 50]   # at least 50 trains : avoid rates on tiny volumes
        liaisons = (liaisons.nsmallest if sens == 'Les moins ponctuelles' else liaisons.nlargest)(top_n, 'regularite')
        liaisons = liaisons.sort_values('regularite', ascending=sens == 'Les moins ponctuelles')
        barres = px.bar(liaisons, x='regularite', y='liaison', orientation='h', text_auto='.1f',
                        color=['Sous le seuil' if v < f['seuil'] else 'Au-dessus du seuil' for v in liaisons['regularite']],
                        color_discrete_map={'Sous le seuil': COULEUR_ALERTE, 'Au-dessus du seuil': COULEUR_OK},
                        hover_data={'circules': ':,', 'retard_15': ':.1f'},
                        labels={'regularite': 'Régularité (%)', 'liaison': '', 'circules': 'Trains', 'retard_15': '% > 15 min',
                                'color': ''},
                        title=f'Top {top_n} — {sens.lower()} ({axe})')
        barres.update_yaxes(autorange='reversed')
        barres.add_vline(x=f['seuil'], line_dash='dot', line_color=GRIS)
        with droite:
            afficher_plotly(style_plotly(barres, 420), 'top_liaisons')

        # Last level of the drill-down : one route, month by month, with the comments of the operator
        choix = st.selectbox('Détail d\'une liaison', liaisons['liaison'])
        historique = tgv[tgv['liaison'] == choix].sort_values('date')
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=historique['date'], y=historique['regularite'], name='Régularité', mode='lines+markers',
                                 line=dict(color=COULEUR_TGV), marker=dict(size=4)))
        fig.add_trace(go.Bar(x=historique['date'], y=historique['annules'], name='Trains annulés', yaxis='y2',
                             marker_color='#c3cbd9', opacity=0.6))
        fig.update_layout(title=f'{choix} : régularité mensuelle et annulations',
                          yaxis=dict(title='Régularité (%)'), yaxis2=dict(title='Annulés', overlaying='y', side='right', showgrid=False),
                          hovermode='x unified')
        afficher_plotly(style_plotly(fig, 360), 'liaison')
        commentaires = historique.dropna(subset=['commentaire']).tail(3)
        for _, ligne in commentaires.iterrows():
            st.caption(f"**{ligne['date']:%m/%Y}** — {ligne['commentaire'][:400]}")
        st.download_button('Exporter les liaisons affichées (CSV)', liaisons.to_csv(index=False, sep=';').encode('utf-8-sig'),
                           file_name='liaisons_tgv.csv', mime='text/csv', icon=':material/download:')

    # Tab 2 : causes of delay
    with tab_2:
        question('Pour quelles causes les TGV sont-ils en retard ? Sur lesquelles peut-on agir ?')
        par_an = []
        for annee in range(2018, f['dernier_mois'].year + 1):
            c = causes(tgv[tgv['annee'] == annee])
            c['Année'] = str(annee)
            par_an.append(c)
        par_an = pd.concat(par_an)
        empile = px.bar(par_an, x='Année', y='Part', color='Cause', color_discrete_sequence=COULEURS_CAUSES,
                        title='Répartition des causes de retard TGV par année (%)', text_auto='.0f')
        empile.update_traces(marker_line_color='white', marker_line_width=1)
        empile.update_yaxes(title='% des trains en retard', range=[0, 100])
        afficher_plotly(style_plotly(empile, 430), 'causes_annees')
        st.warning("**Rupture de série détectée (mai 2026)** : la part « Infrastructure » passe d'environ 20 % à 6 % et "
                   "la part « Gestion en gare » triple d'un mois à l'autre. Un changement aussi brutal correspond très "
                   "probablement à une évolution de la méthode d'attribution des causes, pas à une amélioration réelle "
                   "du réseau : les causes 2026 ne doivent pas être comparées aux années précédentes.",
                   icon=':material/warning:')
        c = causes(n)
        c['Interne'] = ['Hors contrôle SNCF' if 'Externes' in x else 'Leviers SNCF' for x in c['Cause']]
        gauche, droite = st.columns(2)
        donut = px.pie(c, names='Cause', values='Part', hole=0.55, color_discrete_sequence=COULEURS_CAUSES,
                       title=f"Causes — période analysée ({MOIS[f['mois'][0] - 1]}–{MOIS[f['mois'][1] - 1]} {f['annee']})")
        donut.update_traces(textinfo='percent', sort=False)
        with gauche:
            donut = style_plotly(donut, 380)
            donut.update_layout(legend=dict(orientation='v', x=1.02, y=0.5, yanchor='middle', font=dict(size=11)),
                                margin=dict(t=60, b=10, l=10, r=10))
            afficher_plotly(donut, 'donut')
        levier = c.loc[c['Interne'] == 'Leviers SNCF', 'Part'].sum()
        with droite.container(border=True):
            st.metric('Part des retards relevant de leviers internes', fmt_pct(levier),
                      help='Toutes les causes sauf « Externes » : infrastructure, trafic, matériel, gare, voyageurs.')
            st.write('Les causes externes (météo, intrusions, actes de malveillance, heurts) échappent en grande partie '
                     'au transporteur et au gestionnaire d\'infrastructure. Les autres causes correspondent à des '
                     'leviers d\'action : maintenance des voies, régulation du trafic, fiabilité du matériel.')
            st.caption('Hypothèse : les parts publiées par liaison sont pondérées par le nombre de trains en retard '
                       'à l\'arrivée de la liaison pour obtenir une part globale.')
        lecture(f"sur la période, {fmt_pct(levier)} des retards relèvent de causes internes au système ferroviaire.",
                "la majorité des retards est donc actionnable ; l'infrastructure et la gestion du trafic, qui relèvent "
                "de SNCF Réseau, pèsent chaque année autant que le matériel roulant (avant la rupture de 2026).")

    # Tab 3 : map of the stations (bubble = number of trains, color = regularity)
    with tab_3:
        question('Quelles gares sont desservies par les liaisons les moins ponctuelles ?')
        gares = []
        for cote in ['depart', 'arrivee']:
            g = n.groupby(cote)[['circules', 'retards']].sum().reset_index().rename(columns={cote: 'gare'})
            gares.append(g)
        gares = pd.concat(gares).groupby('gare', as_index=False).sum()
        gares['regularite'] = 100 * (1 - gares['retards'] / gares['circules'].replace(0, np.nan))
        gares['lat'] = gares['gare'].map(lambda g: GARES[g][1])
        gares['lon'] = gares['gare'].map(lambda g: GARES[g][2])
        gares['region'] = gares['gare'].map(lambda g: GARES[g][0])
        carte = px.scatter_geo(gares.dropna(subset=['regularite']), lat='lat', lon='lon', size='circules',
                               color='regularite', color_continuous_scale='RdYlBu',
                               range_color=[f['seuil'] - 15, f['seuil'] + 5], hover_name='gare',
                               hover_data={'lat': False, 'lon': False, 'region': True, 'circules': ':,', 'regularite': ':.1f'},
                               labels={'circules': 'TGV (arrivées + départs)', 'regularite': 'Régularité (%)', 'region': 'Région'},
                               size_max=32)
        # Light background with the outline of the French regions (same blue-gray tones as my portfolio map)
        contours = px.choropleth(geojson=charger_geojson(), locations=[x['properties']['nom'] for x in charger_geojson()['features']],
                                 featureidkey='properties.nom', color_discrete_sequence=['#f3f6fb']).data[0]
        contours.update(marker_line_color='#c3cbd9', hoverinfo='skip', showlegend=False)
        carte.add_trace(contours)
        carte.data = carte.data[::-1]
        carte.update_traces(marker=dict(line=dict(color='white', width=1)), selector=dict(type='scattergeo'))
        carte.update_geos(lataxis_range=[40, 52], lonaxis_range=[-6, 12], showcountries=True, countrycolor='#d5dce8',
                          showland=True, landcolor='#ffffff', showocean=True, oceancolor='#eef3fa', showframe=False,
                          showcoastlines=True, coastlinecolor='#c3cbd9', resolution=50, projection_type='mercator')
        carte.update_layout(height=600, margin=dict(t=10, b=10, l=10, r=10))
        afficher_plotly(carte, 'carte_gares')
        pire = gares.dropna(subset=['regularite']).nsmallest(3, 'regularite')
        lecture(f"les gares dont les liaisons sont les moins ponctuelles sont {', '.join(pire['gare'])}.",
                "une gare cumule les retards de toutes ses liaisons : une gare mal classée signale un problème d'axe "
                "(ligne saturée, travaux) plutôt qu'un problème local.")

    # Tab 4 : relationship trip time / punctuality (one point = one route)
    with tab_4:
        question('Les trajets les plus longs sont-ils les moins ponctuels ?')
        nuage = n.groupby(['liaison', 'axe'], as_index=False).agg(circules=('circules', 'sum'), retards=('retards', 'sum'),
                                                                   duree=('duree', 'mean'))
        nuage = nuage[nuage['circules'] >= 50]
        nuage['regularite'] = 100 * (1 - nuage['retards'] / nuage['circules'])
        nuage = nuage.dropna(subset=['duree', 'regularite'])
        fig = px.scatter(nuage, x='duree', y='regularite', color='axe', size='circules', hover_name='liaison',
                         color_discrete_sequence=couleurs + ['#6b4fd6'],
                         labels={'duree': 'Durée moyenne du trajet (min)', 'regularite': 'Régularité (%)', 'axe': 'Axe'},
                         title='Durée du trajet vs régularité (une bulle = une liaison)')
        if len(nuage) > 2:
            pente, origine = np.polyfit(nuage['duree'], nuage['regularite'], 1)
            x = np.array([nuage['duree'].min(), nuage['duree'].max()])
            fig.add_trace(go.Scatter(x=x, y=pente * x + origine, mode='lines', name='Tendance',
                                     line=dict(color=GRIS, dash='dash')))
            correlation = nuage[['duree', 'regularite']].corr().iloc[0, 1]
        afficher_plotly(style_plotly(fig, 450), 'duree')
        if len(nuage) > 2:
            lecture(f"corrélation durée / régularité : r = {correlation:.2f} ; la tendance perd environ "
                    f"{-pente * 60:.1f} point de régularité par heure de trajet supplémentaire.",
                    f"plus un trajet est long, plus il est exposé aux incidents, mais ce lien est "
                    f"{'faible' if abs(correlation) < 0.3 else 'modéré' if abs(correlation) < 0.6 else 'fort'} : l'axe "
                    "emprunté compte davantage que la distance (les liaisons intersecteurs, sans passer par Paris, et "
                    "internationales sont les plus fragiles).")
