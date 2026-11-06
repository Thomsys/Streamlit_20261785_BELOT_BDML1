# Page 3 : TER regional analysis — where, when ? (map, benchmark table, heatmap, drill-down, seasonality)
import altair as alt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.charts import style_plotly, afficher_plotly, afficher_altair, question, lecture
from src.config import COULEUR_TER, COULEUR_ALERTE, COULEUR_OK, GRIS, MOIS, couleurs
from src.data import charger_geojson
from src.kpis import filtrer, regularite, par_groupe, fmt_pct


def tableau_benchmark(d, f):
    # Actual value | Benchmark (national average) | Difference | Previous year | % change
    ter = d['ter'][~d['ter']['partiel']]
    n = par_groupe(filtrer(ter, f['annee'], f['mois']), 'region')
    n1 = par_groupe(filtrer(ter, f['annee'] - 1, f['mois']), 'region')
    moyenne = regularite(filtrer(ter, f['annee'], f['mois']))
    table = n.merge(n1[['region', 'regularite', 'annulation']], on='region', how='left', suffixes=('', '_n1'))
    table['moyenne'] = moyenne
    table['ecart'] = table['regularite'] - moyenne
    table['evolution'] = table['regularite'] - table['regularite_n1']
    table['evolution_pct'] = 100 * (table['regularite'] / table['regularite_n1'] - 1)
    table['statut'] = ['À surveiller' if v < f['seuil'] else 'OK' for v in table['regularite']]
    table['rang'] = table['regularite'].rank(ascending=False).astype(int)
    return table.sort_values('rang'), moyenne


def afficher(d, f):
    st.header('TER : analyse régionale')
    table, moyenne = tableau_benchmark(d, f)
    selection = table[table['region'].isin(f['regions'])]

    tab_1, tab_2, tab_3, tab_4 = st.tabs([':material/map: Carte & classement', ':material/table: Benchmark',
                                          ':material/zoom_in: Drill-down région', ':material/calendar_month: Saisonnalité & anomalies'])

    # Tab 1 : map of the regions + ranking (Q2)
    with tab_1:
        question('Quelles régions ont la meilleure et la moins bonne régularité TER ? (Q2)')
        indicateur = st.segmented_control('Indicateur affiché', ['Régularité', 'Annulations', 'Évolution vs N-1'],
                                          default='Régularité')
        colonne, echelle, titre = {
            'Régularité': ('regularite', 'Blues', 'Taux de régularité (%)'),
            'Annulations': ('annulation', 'Oranges', 'Taux d\'annulation (%)'),
            'Évolution vs N-1': ('evolution', 'RdBu', 'Évolution (pts)'),
        }[indicateur or 'Régularité']
        gauche, droite = st.columns([3, 2])
        # px.choropleth (SVG, no map tiles) : works offline and on every browser
        carte = px.choropleth(selection, geojson=charger_geojson(), locations='region',
                              featureidkey='properties.nom', color=colonne, color_continuous_scale=echelle,
                              color_continuous_midpoint=0 if colonne == 'evolution' else None, hover_name='region',
                              hover_data={'region': False, 'regularite': ':.1f', 'annulation': ':.1f',
                                          'evolution': ':+.1f', 'rang': True},
                              labels={'regularite': 'Régularité (%)', 'annulation': 'Annulations (%)',
                                      'evolution': 'Évolution (pts)', 'rang': 'Rang'})
        carte.update_geos(fitbounds='geojson', visible=False)
        carte.update_traces(marker_line_color='white', marker_line_width=1.5)
        carte.update_layout(height=520, margin=dict(t=10, b=10, l=10, r=10),
                            coloraxis_colorbar=dict(title=titre, orientation='h', y=-0.02, thickness=12, len=0.6))
        with gauche:
            afficher_plotly(carte, 'carte_ter')
        st.caption('Île-de-France (Transilien) et Corse (CFC) ne sont pas couvertes par le jeu de données TER.')

        rang = selection.sort_values(colonne)
        barres = px.bar(rang, x=colonne, y='region', orientation='h',
                        color=['À surveiller' if s == 'À surveiller' else 'OK' for s in rang['statut']],
                        color_discrete_map={'À surveiller': COULEUR_ALERTE, 'OK': COULEUR_TER},
                        text=rang[colonne].map(lambda v: f'{v:.1f}'), title=f'Classement — {titre}',
                        labels={colonne: titre, 'region': '', 'color': ''})
        if colonne == 'regularite':
            barres.add_vline(x=moyenne, line_dash='dash', line_color=GRIS, annotation_text='Moyenne France',
                             annotation_position='bottom right')
            barres.update_xaxes(range=[max(70, rang[colonne].min() - 3), 100])
        with droite:
            afficher_plotly(style_plotly(barres, 520), 'barres_ter')
        if not selection.empty:
            haut, bas = selection.iloc[0], selection.iloc[-1]
            lecture(f"{haut['region']} est en tête ({fmt_pct(haut['regularite'])}), {bas['region']} ferme la marche "
                    f"({fmt_pct(bas['regularite'])}), soit {haut['regularite'] - bas['regularite']:.1f} points d'écart. "
                    f"Moyenne France : {fmt_pct(moyenne)}.",
                    "l'écart entre régions est stable d'une année à l'autre : les régions du sud et du sud-ouest "
                    "(Occitanie, PACA, Nouvelle-Aquitaine) sont structurellement en bas du classement, l'ouest et l'est "
                    "(Bretagne, Grand Est, Bourgogne-Franche-Comté) en haut.")

    # Tab 2 : benchmark table (interactive table + export)
    with tab_2:
        question('Chaque région fait-elle mieux ou moins bien que la moyenne nationale et que l\'année précédente ?')
        affichage = selection[['rang', 'region', 'regularite', 'moyenne', 'ecart', 'regularite_n1', 'evolution',
                               'evolution_pct', 'annulation', 'programmes', 'statut']]
        st.dataframe(affichage, hide_index=True, width='stretch', column_config={
            'rang': st.column_config.NumberColumn('Rang', width='small'),
            'region': 'Région',
            'regularite': st.column_config.ProgressColumn('Régularité (actuel)', format='%.1f %%', min_value=70, max_value=100),
            'moyenne': st.column_config.NumberColumn('Benchmark France', format='%.1f %%'),
            'ecart': st.column_config.NumberColumn('Écart au benchmark', format='%+.1f pt'),
            'regularite_n1': st.column_config.NumberColumn(f"Régularité {f['annee'] - 1}", format='%.1f %%'),
            'evolution': st.column_config.NumberColumn('Évolution', format='%+.1f pt'),
            'evolution_pct': st.column_config.NumberColumn('Évolution (%)', format='%+.2f %%'),
            'annulation': st.column_config.NumberColumn('Annulations', format='%.1f %%'),
            'programmes': st.column_config.NumberColumn('Trains programmés', format='localized'),
            'statut': 'Statut',
        })
        st.download_button('Télécharger le benchmark (CSV)', affichage.to_csv(index=False, sep=';').encode('utf-8-sig'),
                           file_name=f"benchmark_ter_{f['annee']}.csv", mime='text/csv', icon=':material/download:')
        recul = selection[selection['evolution'] < 0]
        lecture(f"{len(recul)} région(s) sur {len(selection)} reculent par rapport aux mêmes mois de {f['annee'] - 1}.",
                "un recul généralisé indique un facteur national (météo, travaux, social) ; un recul isolé appelle "
                "une analyse locale (drill-down).")

    # Tab 3 : drill-down France -> Région -> lot / ancienne région -> mois
    with tab_3:
        question('Que s\'est-il passé, mois par mois, dans une région donnée ?')
        region = st.selectbox('Région à analyser', sorted(f['regions']),
                              index=sorted(f['regions']).index(selection.iloc[-1]['region']) if not selection.empty else 0)
        brut = d['ter_detail']
        detail = brut[(brut['region'] == region) & (brut['date'] >= '2018-01')].dropna(subset=['circules'])
        france = d['ter'][(d['ter']['date'] >= '2018-01') & ~d['ter']['partiel']]
        france = france.groupby('date')[['circules', 'retards']].sum().reset_index()
        france['regularite'] = 100 * (1 - france['retards'] / france['circules'])
        fig = go.Figure()
        for i, (lot, groupe) in enumerate(detail.groupby('region_source')):
            fig.add_trace(go.Scatter(x=groupe['date'], y=groupe['taux_recalcule'], name=lot, mode='lines',
                                     line=dict(color=couleurs[i % 5], width=2)))
        fig.add_trace(go.Scatter(x=france['date'], y=france['regularite'], name='Moyenne France',
                                 line=dict(color=GRIS, dash='dot', width=1.5)))
        fig.add_hline(y=f['seuil'], line_dash='dot', line_color=COULEUR_ALERTE)
        fig.update_layout(title=f'{region} : régularité mensuelle par périmètre publié vs France', hovermode='x unified')
        fig.update_yaxes(title='%', ticksuffix=' %')
        afficher_plotly(style_plotly(fig, 400), 'drill')
        st.caption('Plusieurs courbes = la région est publiée en plusieurs périmètres (ancienne région, ou lot ouvert à '
                   'la concurrence depuis 2025 comme Sud Azur, Étoile d\'Amiens ou Loire Océan).')
        # Lowest months of the selected region, with the comment written by SNCF
        pires = detail[detail['annee'] == f['annee']].nsmallest(5, 'taux_recalcule').fillna({'commentaire': '— (pas de commentaire publié)'})
        st.markdown(f"**Les 5 mois les moins ponctuels en {f['annee']}** (commentaires publiés par SNCF) :")
        st.dataframe(pires[['date', 'region_source', 'taux_recalcule', 'annules', 'commentaire']], hide_index=True,
                     width='stretch', column_config={
                         'date': st.column_config.DateColumn('Mois', format='MMM YYYY'),
                         'region_source': 'Périmètre', 'taux_recalcule': st.column_config.NumberColumn('Régularité', format='%.1f %%'),
                         'annules': st.column_config.NumberColumn('Trains annulés', format='localized'),
                         'commentaire': st.column_config.TextColumn('Commentaire SNCF', width='large')})

    # Tab 4 : seasonality (Q5) and anomalies
    with tab_4:
        question('Y a-t-il des mois « à risque » qui reviennent chaque année ? (Q5)')
        ter = d['ter'][(d['ter']['date'] >= '2018-01') & d['ter']['region'].isin(f['regions']) & ~d['ter']['partiel']]
        # Heatmap region x month of the selected year (Altair, like my Uber heatmap)
        annee = ter[ter['annee'] == f['annee']].copy()
        annee['Mois'] = annee['mois'].map(lambda m: MOIS[m - 1])
        heatmap = alt.Chart(annee).mark_rect(stroke='white', strokeWidth=2).encode(
            x=alt.X('Mois:N', sort=MOIS, title=None),
            y=alt.Y('region:N', title=None, axis=alt.Axis(labelLimit=220), sort=alt.EncodingSortField('regularite', op='mean', order='descending')),
            color=alt.Color('regularite:Q', title='Régularité (%)', scale=alt.Scale(scheme='redyellowblue', domainMid=f['seuil'])),
            tooltip=[alt.Tooltip('region:N', title='Région'), 'Mois:N',
                     alt.Tooltip('regularite:Q', title='Régularité (%)', format='.1f'),
                     alt.Tooltip('annules:Q', title='Trains annulés', format=',')],
        ).properties(title=f"Heatmap régularité TER par région et par mois — {f['annee']}", height=380)
        afficher_altair(heatmap)

        # Monthly profile (all years 2018-2025) : box plot of the monthly national regularity
        mensuel = ter.groupby(['date', 'annee', 'mois'])[['circules', 'retards']].sum().reset_index()
        mensuel['regularite'] = 100 * (1 - mensuel['retards'] / mensuel['circules'])
        mensuel['Mois'] = mensuel['mois'].map(lambda m: MOIS[m - 1])
        gauche, droite = st.columns(2)
        boite = px.box(mensuel, x='Mois', y='regularite', points='all', hover_data=['annee'],
                       category_orders={'Mois': MOIS}, color_discrete_sequence=[COULEUR_TER],
                       title='Régularité selon le mois de l\'année (2018-2026)', labels={'regularite': '%', 'Mois': ''})
        with gauche:
            afficher_plotly(style_plotly(boite, 380, legende=False), 'saison')
        profil = mensuel.groupby('Mois')['regularite'].median().reindex(MOIS)
        lecture(f"les mois les plus faibles sont {', '.join(profil.nsmallest(3).index)} ; les meilleurs "
                f"{', '.join(profil.nlargest(3).index)}.",
                "l'automne (feuilles mortes et perte d'adhérence des rails, en octobre-novembre) et, dans une moindre "
                "mesure, l'été (chaleur, travaux, affluence) reviennent chaque année : ce sont des risques prévisibles, "
                "qui peuvent être anticipés dans la programmation.")

        # Anomalies : months more than 2 standard deviations below the usual level of the region
        stats = ter.groupby('region')['regularite'].agg(['mean', 'std']).reset_index()
        anomalies = ter.merge(stats, on='region')
        anomalies['z'] = (anomalies['regularite'] - anomalies['mean']) / anomalies['std']
        anomalies = anomalies[anomalies['z'] < -2].sort_values('z')
        nuage = px.scatter(ter.merge(stats, on='region'), x='date', y='regularite', color_discrete_sequence=['#c3cbd9'],
                           hover_data=['region'], title='Anomalies : mois à plus de 2 écarts-types sous la normale de la région',
                           labels={'regularite': '%', 'date': ''})
        nuage.add_trace(go.Scatter(x=anomalies['date'], y=anomalies['regularite'], mode='markers', name='Anomalie',
                                   marker=dict(color=COULEUR_ALERTE, size=9), text=anomalies['region'],
                                   hovertemplate='%{text}<br>%{x|%b %Y} : %{y:.1f} %<extra></extra>'))
        with droite:
            afficher_plotly(style_plotly(nuage, 380), 'anomalies')
        with st.expander(f'{len(anomalies)} mois anormaux détectés', icon=':material/warning:'):
            st.dataframe(anomalies[['date', 'region', 'regularite', 'mean', 'z']], hide_index=True, width='stretch',
                         column_config={'date': st.column_config.DateColumn('Mois', format='MMM YYYY'), 'region': 'Région',
                                        'regularite': st.column_config.NumberColumn('Régularité', format='%.1f %%'),
                                        'mean': st.column_config.NumberColumn('Normale région', format='%.1f %%'),
                                        'z': st.column_config.NumberColumn('Écart (σ)', format='%.1f')})
