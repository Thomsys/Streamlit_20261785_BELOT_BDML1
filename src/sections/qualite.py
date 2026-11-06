# Page 6 : data sourcing, cleaning, validation, assumptions and limitations
import pandas as pd
import plotly.express as px
import streamlit as st

from src.charts import style_plotly, afficher_plotly, afficher_altair, question
from src.config import SOURCE_TER, SOURCE_TGV, URL_TER, URL_TGV, COULEUR_TER, COULEUR_TGV
from src.data import journal_ter
import altair as alt


def taux_remplissage(df, nom):
    # Same idea as msno.bar(df) in my notebook : share of non-missing values per column
    return pd.DataFrame({'Colonne': df.columns, 'Remplissage (%)': 100 * df.notna().mean().values, 'Fichier': nom})


def afficher(d, f):
    st.header('Données & qualité')
    tab_1, tab_2, tab_3, tab_4 = st.tabs([':material/source: Sources', ':material/cleaning_services: Nettoyage',
                                          ':material/rule: Hypothèses & limites', ':material/table: Données nettoyées'])

    with tab_1:
        col1, col2 = st.columns(2)
        with col1.container(border=True):
            st.subheader('TER')
            st.write(f'Page : {SOURCE_TER}')
            st.code(URL_TER, language=None)
            st.write(f"{len(d['ter_brut']):,} lignes × {d['ter_brut'].shape[1]} colonnes · producteur SNCF · licence ODbL".replace(',', ' '))
        with col2.container(border=True):
            st.subheader('TGV')
            st.write(f'Page : {SOURCE_TGV}')
            st.code(URL_TGV, language=None)
            st.write(f"{len(d['tgv_brut']):,} lignes × {d['tgv_brut'].shape[1]} colonnes · producteur SNCF / AQST · licence ODbL".replace(',', ' '))

        question('Les colonnes sont-elles complètes ?')
        gauche, droite = st.columns(2)
        for colonne, (brut, nom, couleur) in zip([gauche, droite], [(d['ter_brut'], 'TER', COULEUR_TER),
                                                                      (d['tgv_brut'], 'TGV', COULEUR_TGV)]):
            remplissage = taux_remplissage(brut, nom)
            remplissage['Colonne'] = remplissage['Colonne'].map(lambda c: c if len(c) <= 45 else c[:42] + '...')
            barres = px.bar(remplissage, x='Remplissage (%)', y='Colonne', orientation='h', color_discrete_sequence=[couleur],
                            title=f'Taux de remplissage par colonne — fichier {nom} brut', text_auto='.0f')
            barres.update_yaxes(autorange='reversed', title=None)
            barres.update_xaxes(range=[0, 105])
            with colonne:
                afficher_plotly(style_plotly(barres, 650 if nom == 'TGV' else 420, legende=False), f'remplissage_{nom}')
        st.caption('Les colonnes « Commentaire » sont presque vides : elles ne sont utilisées qu\'à titre illustratif '
                   '(drill-down). Les colonnes de mesure TER ont 37 mois manquants sur 2 380.')

        # Coverage : number of months published per current region and per year
        question('Toutes les régions sont-elles couvertes chaque année ?')
        couverture = d['ter'].groupby(['region', 'annee']).agg(mois=('date', 'nunique'), partiel=('partiel', 'sum')).reset_index()
        couverture['Couverture'] = couverture.apply(lambda l: 'Partielle' if l['partiel'] > 0 else 'Complète', axis=1)
        grille = alt.Chart(couverture).mark_rect(stroke='white', strokeWidth=2).encode(
            x=alt.X('annee:O', title=None), y=alt.Y('region:N', title=None),
            color=alt.Color('Couverture:N', scale=alt.Scale(domain=['Complète', 'Partielle'], range=['#2a78d6', '#eda100'])),
            tooltip=['region', 'annee', alt.Tooltip('mois', title='Mois publiés'), alt.Tooltip('partiel', title='Mois partiels')],
        ).properties(title='Couverture TER par région actuelle et par année', height=330)
        afficher_altair(grille)
        st.caption('Avant 2018, les régions actuelles sont reconstituées à partir des anciennes régions. Jaune = au moins un '
                   'mois où une partie du territoire manque (Lorraine 2013-2016, Nouvelle-Aquitaine 2018-2020 réduite à '
                   'l\'Aquitaine, Occitanie début 2018). Ces mois sont exclus des classements.')

    with tab_2:
        question('Quelles corrections ont été appliquées ?')
        st.subheader('Fichier TER')
        st.dataframe(journal_ter(), hide_index=True, width='stretch')
        st.subheader('Fichier TGV')
        st.dataframe(d['journal_tgv'], hide_index=True, width='stretch')
        st.subheader('Mesures calculées')
        st.markdown(
            '- **Régularité** = 1 − trains en retard à l\'arrivée / trains ayant circulé (recalculée à partir des sommes, '
            'jamais en faisant la moyenne de pourcentages).\n'
            '- **Trains ayant circulé (TGV)** = circulations prévues − trains annulés.\n'
            '- **Taux d\'annulation** = trains annulés / trains programmés.\n'
            '- **Retard moyen** = moyenne pondérée par le nombre de trains en retard.\n'
            '- **Causes** = parts publiées × trains en retard de la liaison, puis re-agrégées.\n'
            '- **Validation** : le taux TER recalculé reproduit le taux publié (écart < 0,1 pt) sauf pour 12 lignes '
            '(janvier et décembre 2020), où le fichier source publie un taux incohérent avec ses propres comptages ; '
            'le taux recalculé est conservé.')
        st.subheader('Jointure TER × TGV')
        st.write('Clé : **mois × région actuelle**. Chaque gare TGV est rattachée à sa région (table de 59 gares). '
                 'Une liaison compte pour la région de chacune de ses deux gares (Lyon → Marseille compte pour '
                 'Auvergne-Rhône-Alpes et pour Provence-Alpes-Côte d\'Azur) ; les gares parisiennes et étrangères ne '
                 'sont rattachées à aucune région TER. Les TGV ne sont analysés que jusqu\'au dernier mois TER '
                 'disponible, pour comparer des périodes identiques.')

    with tab_3:
        st.subheader('Hypothèses')
        st.markdown(
            '- Les anciennes régions (avant la réforme de 2016) et les lots ouverts à la concurrence (2025) sont '
            'additionnés dans leur région actuelle pour obtenir des séries continues.\n'
            '- Le seuil d\'alerte par défaut (90 %) est un choix d\'analyse, proche des objectifs usuels des conventions '
            'TER ; il est modifiable dans la barre latérale.\n'
            '- Les comparaisons annuelles portent toujours sur **les mêmes mois** (ex. janvier-août 2026 vs janvier-août 2025).')
        st.subheader('Limites')
        st.markdown(
            '- **Seuils de retard différents** : un TER est en retard au-delà de 5 min ; pour le TGV, la définition AQST '
            'dépend de la durée du trajet. L\'écart TER / TGV est donc indicatif.\n'
            '- **Pas de nombre de voyageurs** : un retard sur une ligne très fréquentée pèse autant qu\'un retard sur '
            'une ligne peu fréquentée.\n'
            '- **Rupture de série des causes TGV (mai 2026)** : changement de méthode probable, comparaison impossible.\n'
            '- **Pas de causes pour le TER** : les leviers d\'action ne peuvent être identifiés que pour le TGV.\n'
            '- **Corrélation ≠ causalité** : le lien entre TER et TGV d\'une région suggère des causes communes, sans les prouver.')

    with tab_4:
        question('Consulter et exporter les données nettoyées')
        choix = st.radio('Table', ['TER par région actuelle et par mois', 'TGV par liaison et par mois'], horizontal=True)
        table = d['ter'] if choix.startswith('TER') else d['tgv'].drop(columns=['commentaire'])
        recherche = st.text_input('Filtrer (région, gare ou liaison contient...)', '')
        if recherche:
            colonne = 'region' if choix.startswith('TER') else 'liaison'
            table = table[table[colonne].str.contains(recherche, case=False, na=False)]
        st.dataframe(table, hide_index=True, width='stretch', height=400)
        st.download_button(f'Télécharger ({len(table):,} lignes, CSV)'.replace(',', ' '),
                           table.to_csv(index=False, sep=';').encode('utf-8-sig'),
                           file_name='ter_nettoye.csv' if choix.startswith('TER') else 'tgv_nettoye.csv',
                           mime='text/csv', icon=':material/download:')
