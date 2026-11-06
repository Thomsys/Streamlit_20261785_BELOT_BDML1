# Page 5 : TER vs TGV benchmark, regional scorecard and what-if simulation
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.charts import style_plotly, afficher_plotly, question, lecture
from src.config import COULEUR_TER, COULEUR_TGV, COULEUR_ALERTE, GRIS, CAUSES
from src.kpis import filtrer, regularite, par_groupe, normaliser, fmt_pct, tgv_filtre


def table_regions(d, f, annee):
    # One row per region : TER and TGV regularity (TGV = routes serving the region), TER cancellations
    ter = par_groupe(filtrer(d['ter'][~d['ter']['partiel']], annee, f['mois']), 'region')
    tgv_reg = d['tgv_reg'][d['tgv_reg']['axe'].isin(f['axes'])]
    tgv = par_groupe(filtrer(tgv_reg, annee, f['mois']), 'region', 'prevus')
    table = ter[['region', 'regularite', 'annulation', 'programmes']].merge(
        tgv[['region', 'regularite', 'circules']], on='region', how='left', suffixes=('_ter', '_tgv'))
    table['ecart'] = table['regularite_tgv'] - table['regularite_ter']
    return table[table['region'].isin(f['regions'])]


def afficher(d, f):
    st.header('Comparaison TER vs TGV')
    table = table_regions(d, f, f['annee'])
    table1 = table_regions(d, f, f['annee'] - 1)
    table = table.merge(table1[['region', 'regularite_ter', 'regularite_tgv']], on='region', how='left', suffixes=('', '_n1'))
    table['evol_ter'] = table['regularite_ter'] - table['regularite_ter_n1']
    table['evol_tgv'] = table['regularite_tgv'] - table['regularite_tgv_n1']

    tab_1, tab_2, tab_3 = st.tabs([':material/compare_arrows: Benchmark TER vs TGV', ':material/leaderboard: Scorecard régions',
                                   ':material/tune: Simulation (what-if)'])

    # Tab 1 : dumbbell chart + benchmark table + correlation (Q4)
    with tab_1:
        question('Dans chaque région, le TGV fait-il mieux ou moins bien que le TER ? (Q4)')
        t = table.sort_values('regularite_ter')
        fig = go.Figure()
        for _, ligne in t.dropna(subset=['regularite_tgv']).iterrows():
            fig.add_shape(type='line', x0=ligne['regularite_tgv'], x1=ligne['regularite_ter'], y0=ligne['region'],
                          y1=ligne['region'], line=dict(color='#c3cbd9', width=3))
        fig.add_trace(go.Scatter(x=t['regularite_ter'], y=t['region'], mode='markers', name='TER',
                                 marker=dict(color=COULEUR_TER, size=13), hovertemplate='%{y} — TER : %{x:.1f} %<extra></extra>'))
        fig.add_trace(go.Scatter(x=t['regularite_tgv'], y=t['region'], mode='markers', name='TGV (liaisons desservant la région)',
                                 marker=dict(color=COULEUR_TGV, size=13), hovertemplate='%{y} — TGV : %{x:.1f} %<extra></extra>'))
        fig.add_vline(x=f['seuil'], line_dash='dot', line_color=COULEUR_ALERTE)
        fig.update_xaxes(title='Taux de régularité (%)', range=[min(70, t['regularite_tgv'].min() - 2), 100])
        fig.update_layout(title='Écart de régularité TER / TGV par région')
        afficher_plotly(style_plotly(fig, 450), 'haltere')
        st.caption('Normandie : aucune liaison TGV dans le jeu de données (pas de point orange).')

        st.dataframe(table[['region', 'regularite_ter', 'regularite_tgv', 'ecart', 'regularite_ter_n1', 'evol_ter',
                            'regularite_tgv_n1', 'evol_tgv']].sort_values('regularite_ter', ascending=False),
                     hide_index=True, width='stretch', column_config={
                         'region': 'Région',
                         'regularite_ter': st.column_config.NumberColumn('TER (actuel)', format='%.1f %%'),
                         'regularite_tgv': st.column_config.NumberColumn('TGV (benchmark)', format='%.1f %%'),
                         'ecart': st.column_config.NumberColumn('Écart TGV − TER', format='%+.1f pt'),
                         'regularite_ter_n1': st.column_config.NumberColumn(f"TER {f['annee'] - 1}", format='%.1f %%'),
                         'evol_ter': st.column_config.NumberColumn('Évol. TER', format='%+.1f pt'),
                         'regularite_tgv_n1': st.column_config.NumberColumn(f"TGV {f['annee'] - 1}", format='%.1f %%'),
                         'evol_tgv': st.column_config.NumberColumn('Évol. TGV', format='%+.1f pt')})

        # Do TER and TGV move together ? Region level (2018 -> last month) and monthly national series
        gauche, droite = st.columns(2)
        ter_all = par_groupe(d['ter'][(d['ter']['date'] >= '2018-01') & ~d['ter']['partiel']], 'region')
        tgv_all = par_groupe(d['tgv_reg'][d['tgv_reg']['axe'].isin(f['axes'])], 'region', 'prevus')
        lien = ter_all[['region', 'regularite']].merge(tgv_all[['region', 'regularite', 'circules']], on='region',
                                                        suffixes=('_ter', '_tgv')).dropna()
        r_region = lien[['regularite_ter', 'regularite_tgv']].corr().iloc[0, 1]
        nuage = px.scatter(lien, x='regularite_ter', y='regularite_tgv', text='region', size='circules',
                           color_discrete_sequence=[COULEUR_TGV],
                           labels={'regularite_ter': 'Régularité TER 2018-2026 (%)', 'regularite_tgv': 'Régularité TGV (%)'},
                           title=f'Régions : TER vs TGV sur 2018-2026 (r = {r_region:.2f})')
        nuage.update_traces(textposition='top center', textfont_size=10)
        with gauche:
            afficher_plotly(style_plotly(nuage, 420, legende=False), 'correlation')

        mensuel_ter = d['ter'][(d['ter']['date'] >= '2018-01') & ~d['ter']['partiel']].groupby('date')[['circules', 'retards']].sum()
        mensuel_tgv = tgv_filtre(d, f).groupby('date')[['circules', 'retards']].sum()
        serie = pd.DataFrame({'TER': 100 * (1 - mensuel_ter['retards'] / mensuel_ter['circules']),
                              'TGV': 100 * (1 - mensuel_tgv['retards'] / mensuel_tgv['circules'].replace(0, np.nan))}).dropna()
        r_mois = serie.corr().iloc[0, 1]
        mois = px.scatter(serie.reset_index(), x='TER', y='TGV', hover_data={'date': '|%b %Y'},
                          color=serie.index.year.astype(str), color_discrete_sequence=px.colors.sequential.Blues[2:],
                          labels={'TER': 'Régularité TER du mois (%)', 'TGV': 'Régularité TGV du mois (%)', 'color': 'Année'},
                          title=f'Mois par mois : TER vs TGV (r = {r_mois:.2f})')
        with droite:
            afficher_plotly(style_plotly(mois, 420), 'correlation_mois')
        lecture(f"le TGV est sous le TER dans toutes les régions ({table['ecart'].mean():+.1f} pt en moyenne). Les régions "
                f"où le TER est faible ont aussi un TGV faible (r = {r_region:.2f}), et les bons et mauvais mois "
                f"coïncident (r = {r_mois:.2f}).",
                "TER et TGV partagent le même réseau : une part importante de la ponctualité dépend de facteurs "
                "territoriaux communs (état et saturation des lignes, climat). Attention : corrélation ne veut pas dire "
                "causalité, et les seuils de retard ne sont pas identiques (voir Qualité des données).")

    # Tab 2 : composite scorecard with user-defined weights
    with tab_2:
        question('Quelles régions offrent globalement le meilleur service ferroviaire ?')
        st.write('Score composite = moyenne pondérée de 4 indicateurs **normalisés de 0 à 100** (min-max entre les '
                 'régions affichées : 100 = meilleure région, 0 = moins bonne). Les poids sont des choix de l\'utilisateur, '
                 'pas une vérité objective.')
        c1, c2, c3, c4 = st.columns(4)
        w1 = c1.slider('Poids régularité TER', 0, 100, 40, 5)
        w2 = c2.slider('Poids annulations TER', 0, 100, 20, 5)
        w3 = c3.slider('Poids régularité TGV', 0, 100, 20, 5)
        w4 = c4.slider('Poids tendance TER (vs N-1)', 0, 100, 20, 5)
        total = w1 + w2 + w3 + w4 or 1
        score = table.dropna(subset=['regularite_ter']).copy()
        score['n_ter'] = normaliser(score['regularite_ter'])
        score['n_ann'] = normaliser(-score['annulation'])       # fewer cancellations = better
        score['n_tgv'] = normaliser(score['regularite_tgv']).fillna(50)   # no TGV data -> neutral value
        score['n_tend'] = normaliser(score['evol_ter']).fillna(50)
        score['Score'] = (w1 * score['n_ter'] + w2 * score['n_ann'] + w3 * score['n_tgv'] + w4 * score['n_tend']) / total
        score = score.sort_values('Score', ascending=False)
        score['Rang'] = range(1, len(score) + 1)
        st.latex(rf"Score = {w1 / total:.2f}\,N(\text{{TER}}) + {w2 / total:.2f}\,N(-\text{{annul.}}) + "
                 rf"{w3 / total:.2f}\,N(\text{{TGV}}) + {w4 / total:.2f}\,N(\Delta\text{{TER}})")
        gauche, droite = st.columns([2, 3])
        with gauche:
            st.dataframe(score[['Rang', 'region', 'Score', 'n_ter', 'n_ann', 'n_tgv', 'n_tend']], hide_index=True, width='stretch',
                         column_config={'region': 'Région',
                                        'Score': st.column_config.ProgressColumn('Score', format='%.0f', min_value=0, max_value=100),
                                        'n_ter': st.column_config.NumberColumn('TER', format='%.0f'),
                                        'n_ann': st.column_config.NumberColumn('Annul.', format='%.0f'),
                                        'n_tgv': st.column_config.NumberColumn('TGV', format='%.0f'),
                                        'n_tend': st.column_config.NumberColumn('Tendance', format='%.0f')})
            st.download_button('Télécharger la scorecard (CSV)', score.to_csv(index=False, sep=';').encode('utf-8-sig'),
                               file_name='scorecard_regions.csv', mime='text/csv', icon=':material/download:')
        empile = score.melt(id_vars='region', value_vars=['n_ter', 'n_ann', 'n_tgv', 'n_tend'], var_name='Composante')
        poids = {'n_ter': w1, 'n_ann': w2, 'n_tgv': w3, 'n_tend': w4}
        empile['Contribution'] = empile.apply(lambda l: l['value'] * poids[l['Composante']] / total, axis=1)
        empile['Composante'] = empile['Composante'].map({'n_ter': 'Régularité TER', 'n_ann': 'Annulations TER',
                                                         'n_tgv': 'Régularité TGV', 'n_tend': 'Tendance TER'})
        barres = px.bar(empile, x='Contribution', y='region', color='Composante', orientation='h',
                        category_orders={'region': list(score['region'])},
                        color_discrete_sequence=[COULEUR_TER, '#9cc2ff', COULEUR_TGV, '#1baf7a'],
                        title='Contribution de chaque composante au score', labels={'region': ''})
        with droite:
            afficher_plotly(style_plotly(barres, 430), 'scorecard')
        with st.expander('Normalisation, hypothèses et limites du score', icon=':material/info:'):
            st.write('- **Normalisation** : min-max sur les régions sélectionnées → le score est relatif (il change si '
                     'on retire une région) et un écart de 1 point peut paraître grand si les régions sont proches.')
            st.write('- **Annulations** : le signe est inversé (moins d\'annulations = meilleur score).')
            st.write('- **Donnée absente** (Normandie sans TGV) : valeur neutre de 50 attribuée.')
            st.write('- **Poids** : choisis par l\'utilisateur ; les valeurs par défaut (40/20/20/20) privilégient le TER, '
                     'car c\'est le service dont la Région est responsable. Ils ne sont pas « objectivement corrects ».')

    # Tab 3 : what-if simulation on the causes of TGV delays
    with tab_3:
        question('Que gagnerait-on si une cause de retard était réduite ?')
        st.warning('**Simulation** : il s\'agit d\'un calcul théorique, pas d\'un résultat observé. Il suppose qu\'un '
                   'train retardé par la cause choisie serait arrivé à l\'heure sans elle. En 2026, la méthode '
                   'd\'attribution des causes a changé (voir page TGV).', icon=':material/science:')
        c1, c2 = st.columns(2)
        cause = c1.selectbox('Cause réduite', list(CAUSES), format_func=lambda c: CAUSES[c], index=1)
        reduction = c2.slider('Réduction des retards liés à cette cause', 0, 100, 20, 5, format='%d %%')
        periode = filtrer(tgv_filtre(d, f), f['annee'], f['mois'])
        actuel = regularite(periode)
        retards_evites = periode[cause].sum() * reduction / 100
        simule = 100 * (1 - (periode['retards'].sum() - retards_evites) / periode['circules'].sum())
        m1, m2, m3 = st.columns(3)
        m1.metric('Régularité TGV observée', fmt_pct(actuel), border=True)
        m2.metric('Régularité TGV simulée', fmt_pct(simule), f'{simule - actuel:+.1f} pt'.replace('.', ','), border=True)
        m3.metric('TGV en retard évités', f'{retards_evites:,.0f}'.replace(',', ' '), border=True)
        courbe = pd.DataFrame({'Réduction (%)': range(0, 101, 10)})
        courbe['Régularité simulée'] = [100 * (1 - (periode['retards'].sum() - periode[cause].sum() * r / 100) /
                                               periode['circules'].sum()) for r in courbe['Réduction (%)']]
        fig = px.line(courbe, x='Réduction (%)', y='Régularité simulée', markers=True, color_discrete_sequence=[COULEUR_TGV],
                      title=f'Régularité TGV simulée selon la réduction des retards « {CAUSES[cause]} »')
        fig.add_hline(y=actuel, line_dash='dot', line_color=GRIS, annotation_text='Observé')
        fig.add_hline(y=f['seuil'], line_dash='dot', line_color=COULEUR_ALERTE, annotation_text='Seuil')
        afficher_plotly(style_plotly(fig, 360, legende=False), 'whatif')
