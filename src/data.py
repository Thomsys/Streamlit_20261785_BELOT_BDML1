# Loading, cleaning and validation of the two SNCF datasets (TER and TGV)
# Every function is cached with st.cache_data : the csv files are read and cleaned only once
import json
import numpy as np
import pandas as pd
import streamlit as st

from src.config import TER_CSV, TGV_CSV, GEOJSON, REGION_ACTUELLE, GARES, AXE_PAR_GARE_PARIS, CAUSES

# Number of old regions merged in each current region (2016 territorial reform)
COMPOSITION = {'Grand Est': 3, 'Nouvelle-Aquitaine': 3, 'Auvergne-Rhône-Alpes': 2, 'Normandie': 2,
               'Bourgogne-Franche-Comté': 2, 'Occitanie': 2, 'Hauts-de-France': 2}


def taux(numerateur, denominateur):
    # Percentage protected against the division by zero (months without any train)
    numerateur = np.asarray(numerateur, dtype=float)
    denominateur = np.asarray(denominateur, dtype=float)
    with np.errstate(divide='ignore', invalid='ignore'):
        resultat = np.where(denominateur > 0, 100 * numerateur / denominateur, np.nan)
    return resultat


def perimetre_partiel(region, date, n_sources):
    # True when the current region is only partly covered by the data for this month
    mois = date.strftime('%Y-%m')
    if region == 'Nouvelle-Aquitaine' and '2018-01' <= mois <= '2020-08':
        return True   # only "Aquitaine" is published (Limousin and Poitou-Charentes stop in 12/2017)
    if region == 'Occitanie' and '2018-01' <= mois <= '2018-06':
        return True   # only "Midi Pyrénées" is published (Languedoc-Roussillon stops in 12/2017)
    reforme = '2017-01' if region == 'Grand Est' else '2018-01'
    return mois < reforme and n_sources < COMPOSITION.get(region, 1)


@st.cache_data
def charger_ter():
    # Raw file (separator ;) -> one row per month and per published region (or commercial lot)
    brut = pd.read_csv(TER_CSV, sep=';')
    df = brut.rename(columns={
        'Date': 'date', 'Région': 'region_source',
        'Nombre de trains programmés': 'programmes', 'Nombre de trains ayant circulé': 'circules',
        'Nombre de trains annulés': 'annules', "Nombre de trains en retard à l'arrivée": 'retards',
        'Taux de régularité': 'taux_source', 'Commentaires': 'commentaire',
    }).drop(columns=["Nombre de trains à l'heure pour un train en retard à l'arrivée"])
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m')
    df['region'] = df['region_source'].map(REGION_ACTUELLE)
    df['region_source'] = df['region_source'].str.strip()
    # Recomputed regularity (1 - late trains / trains that ran) : allows to check the published rate
    df['taux_recalcule'] = 100 - taux(df['retards'], df['circules'])
    df['annee'] = df['date'].dt.year
    return brut, df


@st.cache_data
def ter_regional():
    # Aggregation at the current-region level (sums of trains, then rates recomputed from the sums)
    _, df = charger_ter()
    valides = df.dropna(subset=['circules'])
    reg = valides.groupby(['date', 'region'], as_index=False).agg(
        programmes=('programmes', 'sum'), circules=('circules', 'sum'), annules=('annules', 'sum'),
        retards=('retards', 'sum'), n_sources=('region_source', 'nunique'))
    reg['regularite'] = 100 - taux(reg['retards'], reg['circules'])
    reg['annulation'] = taux(reg['annules'], reg['programmes'])
    reg['partiel'] = [perimetre_partiel(r, d, n) for r, d, n in zip(reg['region'], reg['date'], reg['n_sources'])]
    reg['annee'] = reg['date'].dt.year
    reg['mois'] = reg['date'].dt.month
    return reg


@st.cache_data
def charger_tgv():
    brut = pd.read_csv(TGV_CSV, sep=';')
    df = brut.rename(columns={
        'Date': 'date', 'Service': 'service', 'Gare de départ': 'depart', "Gare d'arrivée": 'arrivee',
        'Durée moyenne du trajet': 'duree', 'Nombre de circulations prévues': 'prevus',
        'Nombre de trains annulés': 'annules', 'Nombre de trains en retard au départ': 'retards_depart',
        "Nombre de trains en retard à l'arrivée": 'retards',
        "Retard moyen des trains en retard à l'arrivée": 'retard_moyen',
        'Nombre trains en retard > 15min': 'retards_15', 'Nombre trains en retard > 30min': 'retards_30',
        'Nombre trains en retard > 60min': 'retards_60', "Commentaire retards à l'arrivée": 'commentaire',
    })
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m')
    df['depart'] = df['depart'].str.strip()
    df['arrivee'] = df['arrivee'].str.strip()
    return brut, df


@st.cache_data
def tgv_nettoye():
    # Cleaning of the TGV file. Returns the clean table and the log of every correction
    _, df = charger_tgv()
    journal = []
    comptes = ['prevus', 'annules', 'retards_depart', 'retards', 'retards_15', 'retards_30', 'retards_60']

    # 1. Impossible values : negative counts -> missing value
    for colonne in comptes:
        n = int((df[colonne] < 0).sum())
        if n:
            df.loc[df[colonne] < 0, colonne] = np.nan
            journal.append({'Étape': 'Valeurs négatives', 'Colonne': colonne, 'Lignes': n,
                            'Traitement': 'Remplacées par une valeur manquante (un nombre de trains ne peut pas être négatif)'})
    # Negative average delay of the late trains (e.g. -40 min) is impossible too
    n = int((df['retard_moyen'] < 0).sum())
    df.loc[df['retard_moyen'] < 0, 'retard_moyen'] = np.nan
    journal.append({'Étape': 'Valeurs négatives', 'Colonne': 'retard_moyen', 'Lignes': n,
                    'Traitement': 'Retard moyen négatif remplacé par une valeur manquante'})
    # Average trip time of 0 min = missing information
    n = int((df['duree'] <= 0).sum())
    df.loc[df['duree'] <= 0, 'duree'] = np.nan
    journal.append({'Étape': 'Valeurs aberrantes', 'Colonne': 'duree', 'Lignes': n,
                    'Traitement': 'Durée de trajet nulle remplacée par une valeur manquante'})

    # 2. Months without any planned train (Covid lockdown) : kept, but excluded from the rates
    n = int((df['prevus'] == 0).sum())
    journal.append({'Étape': 'Mois sans circulation', 'Colonne': 'prevus', 'Lignes': n,
                    'Traitement': 'Conservés mais exclus des taux (division par zéro)'})

    # 3. Same route and same month published twice (National + International split, 07-09/2025)
    cle = ['date', 'depart', 'arrivee']
    n = int(df.duplicated(cle, keep=False).sum())
    journal.append({'Étape': 'Doublons de clé', 'Colonne': 'date + gares', 'Lignes': n,
                    'Traitement': 'Lignes « National » et « International » d\'une même liaison additionnées'})
    # Weighted means need the weights first (average delay x number of late trains)
    df['_minutes_retard'] = df['retard_moyen'] * df['retards']
    causes = list(CAUSES)
    for cause in causes:
        df[cause] = df[cause] * df['retards'] / 100   # share -> number of late trains for this cause
    df['_duree_x_prevus'] = df['duree'] * df['prevus']
    agg = {c: (lambda x: x.sum(min_count=1)) for c in comptes + causes + ['_minutes_retard', '_duree_x_prevus']}
    agg.update({'service': lambda s: ' + '.join(sorted(s.unique())), 'commentaire': 'first'})
    df = df.groupby(cle, as_index=False).agg(agg)

    # 4. Calculated measures
    df['circules'] = df['prevus'] - df['annules']
    df['regularite'] = 100 - taux(df['retards'], df['circules'])
    df['annulation'] = taux(df['annules'], df['prevus'])
    df['retard_moyen'] = taux(df['_minutes_retard'], df['retards']) / 100
    df['duree'] = taux(df['_duree_x_prevus'], df['prevus']) / 100
    df = df.drop(columns=['_minutes_retard', '_duree_x_prevus'])

    # 5. Enrichment : route label, regions / countries of both stations, axis
    df['liaison'] = df['depart'] + ' → ' + df['arrivee']
    df['region_depart'] = df['depart'].map(lambda g: GARES[g][0])
    df['region_arrivee'] = df['arrivee'].map(lambda g: GARES[g][0])
    etranger = ~df['region_depart'].isin(REGIONS_FR) | ~df['region_arrivee'].isin(REGIONS_FR)
    df['perimetre'] = np.where(etranger, 'International', 'Domestique')

    def axe(depart, arrivee, internationale):
        if internationale:
            return 'International'
        for gare in (depart, arrivee):
            if gare in AXE_PAR_GARE_PARIS:
                return AXE_PAR_GARE_PARIS[gare]
        return 'Intersecteurs (sans Paris)'
    df['axe'] = [axe(d, a, i) for d, a, i in zip(df['depart'], df['arrivee'], etranger)]
    df['annee'] = df['date'].dt.year
    df['mois'] = df['date'].dt.month
    return df, pd.DataFrame(journal)


# Current French regions served by TER (Île-de-France and Corse have no TER in the dataset)
REGIONS_FR = sorted(set(REGION_ACTUELLE.values()) | {'Île-de-France'})


@st.cache_data
def tgv_par_region():
    # One TGV route serves the regions of its two stations (Paris / foreign stations excluded)
    # -> a route Lyon -> Marseille counts for Auvergne-Rhône-Alpes AND for Provence-Alpes-Côte d'Azur
    df, _ = tgv_nettoye()
    lignes = []
    for cote in ['region_depart', 'region_arrivee']:
        partie = df[df[cote].isin(REGION_ACTUELLE.values())].copy()
        partie['region'] = partie[cote]
        lignes.append(partie)
    eclate = pd.concat(lignes, ignore_index=True)
    # A route with both stations in the same region must not be counted twice
    eclate = eclate.drop_duplicates(['date', 'liaison', 'region'])
    return eclate


@st.cache_data
def charger_geojson():
    with open(GEOJSON, encoding='utf-8') as fichier:
        return json.load(fichier)


def journal_ter():
    # Data-quality summary of the TER file (for the "Qualité des données" page)
    brut, df = charger_ter()
    ecart = (df['taux_recalcule'] - df['taux_source']).abs()
    reg = ter_regional()
    return pd.DataFrame([
        {'Étape': 'Valeurs manquantes', 'Colonne': 'toutes les mesures', 'Lignes': int(df['circules'].isna().sum()),
         'Traitement': 'Mois non publiés (Lorraine 2013-2016 : refus de transmission, Nord-Pas-de-Calais) — exclus des calculs'},
        {'Étape': 'Doublons', 'Colonne': 'date + région', 'Lignes': int(df.duplicated(['date', 'region_source']).sum()),
         'Traitement': 'Aucun doublon'},
        {'Étape': 'Réforme territoriale 2016', 'Colonne': 'Région', 'Lignes': int(df['region_source'].isin(
            [k for k, v in REGION_ACTUELLE.items() if k != v and k not in ['Etoile Amiens', 'Loire Océan', 'Sud Azur',
                                                                            'Nouvelle Aquitaine', 'Centre Val-de-Loire']]).sum()),
         'Traitement': 'Anciennes régions rattachées à leur région actuelle (table de correspondance)'},
        {'Étape': 'Lots ouverts à la concurrence (2025)', 'Colonne': 'Région',
         'Lignes': int(df['region_source'].isin(['Etoile Amiens', 'Loire Océan', 'Sud Azur']).sum()),
         'Traitement': 'Sud Azur, Étoile d\'Amiens et Loire Océan additionnés à leur région'},
        {'Étape': 'Périmètre partiel', 'Colonne': 'région × mois', 'Lignes': int(reg['partiel'].sum()),
         'Traitement': 'Signalés (ex. Nouvelle-Aquitaine 2018-2020 = Aquitaine seule) et exclus du classement'},
        {'Étape': 'Validation du taux', 'Colonne': 'Taux de régularité',
         'Lignes': int((ecart > 0.1).sum()),
         'Traitement': f'Taux recalculé = 1 − retards / trains ayant circulé ; écart max avec le taux publié : {ecart.max():.2f} pt'},
    ])
