# KPI calculations : every rate is recomputed from the sums of trains (never an average of percentages)
import numpy as np
import pandas as pd

from src.config import CAUSES


def filtrer(df, annee, mois, regions=None, colonne_region='region'):
    # Selected year, range of months and regions
    masque = (df['annee'] == annee) & df['mois'].between(mois[0], mois[1])
    if regions is not None and colonne_region in df:
        masque &= df[colonne_region].isin(regions)
    return df[masque]


def regularite(df, circules='circules'):
    # Regularity = 1 - late trains / trains that ran (in %)
    total = df[circules].sum()
    return np.nan if total == 0 else 100 * (1 - df['retards'].sum() / total)


def annulation(df, prevus='programmes'):
    total = df[prevus].sum()
    return np.nan if total == 0 else 100 * df['annules'].sum() / total


def part(df, colonne, circules='circules'):
    total = df[circules].sum()
    return np.nan if total == 0 else 100 * df[colonne].sum() / total


def retard_moyen(df):
    # Average delay of the late TGV, weighted by the number of late trains
    poids = df['retards'].fillna(0)
    valeurs = df['retard_moyen']
    ok = valeurs.notna() & (poids > 0)
    return np.nan if poids[ok].sum() == 0 else np.average(valeurs[ok], weights=poids[ok])


def par_groupe(df, colonne, prevus='programmes'):
    # Table of regularity / cancellation rate by region, route, axis...
    agg = {'circules': 'sum', 'retards': 'sum', 'annules': 'sum', prevus: 'sum'}
    if 'retards_15' in df:
        agg['retards_15'] = 'sum'
    table = df.groupby(colonne, as_index=False).agg(agg)
    table['regularite'] = 100 * (1 - table['retards'] / table['circules'].replace(0, np.nan))
    table['annulation'] = 100 * table['annules'] / table[prevus].replace(0, np.nan)
    if 'retards_15' in table:
        table['retard_15'] = 100 * table['retards_15'] / table['circules'].replace(0, np.nan)
    return table


def mensuel(df, prevus='programmes'):
    # Monthly time series (one point per month)
    return par_groupe(df, 'date', prevus).sort_values('date')


def causes(df):
    # Share of each cause of delay (weighted by the number of late trains)
    total = df[list(CAUSES)].sum()
    if total.sum() == 0:
        return pd.DataFrame(columns=['Cause', 'Part'])
    return pd.DataFrame({'Cause': [CAUSES[c] for c in CAUSES], 'Part': (100 * total / total.sum()).values})


def evolution(actuel, precedent):
    # Difference in points between two rates (None when one of them is missing)
    if pd.isna(actuel) or pd.isna(precedent):
        return None
    return actuel - precedent


def fmt_pct(valeur, decimales=1):
    return '—' if pd.isna(valeur) else f'{valeur:.{decimales}f} %'.replace('.', ',')


def fmt_pts(valeur):
    return None if valeur is None or pd.isna(valeur) else f'{valeur:+.1f} pt'.replace('.', ',')


def fmt_nb(valeur):
    return '—' if pd.isna(valeur) else f'{valeur:,.0f}'.replace(',', ' ')


def normaliser(serie):
    # Min-max normalization between 0 and 100 (used by the scorecard)
    mini, maxi = serie.min(), serie.max()
    if maxi == mini:
        return pd.Series(50.0, index=serie.index)
    return 100 * (serie - mini) / (maxi - mini)


def tgv_filtre(d, f):
    # TGV routes of the selected axes; if some regions only are selected, the routes serving them
    tgv = d['tgv']
    if len(f['regions']) < len(f['toutes_regions']):
        tgv = d['tgv_reg'][d['tgv_reg']['region'].isin(f['regions'])].drop_duplicates(['date', 'liaison'])
    return tgv[tgv['axe'].isin(f['axes'])]
