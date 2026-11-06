# Constants shared by every page : paths, colors, mappings (regions and TGV stations)
from pathlib import Path

# Paths of the data files (data/ folder next to app.py)
DATA_DIR = Path(__file__).parent.parent / 'data'
TER_CSV = DATA_DIR / 'regularite-mensuelle-ter.csv'
TGV_CSV = DATA_DIR / 'regularite-mensuelle-tgv-aqst.csv'
GEOJSON = DATA_DIR / 'regions.geojson'
LOGO = DATA_DIR / 'logo_efrei.png'

# Sources (data.gouv.fr pages and direct links of the CSV exports)
SOURCE_TER = 'https://www.data.gouv.fr/datasets/regularite-mensuelle-ter-sncf'
SOURCE_TGV = 'https://www.data.gouv.fr/datasets/regularite-mensuelle-tgv-par-liaisons'
URL_TER = ('https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/regularite-mensuelle-ter/'
           'exports/csv?use_labels=true&delimiter=%3B')
URL_TGV = ('https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/regularite-mensuelle-tgv-aqst/'
           'exports/csv?use_labels=true&delimiter=%3B')

# Same color palette as my portfolio (fixed order : slot 1 = blue, slot 2 = orange, ...)
couleurs = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4']
COULEUR_TER = couleurs[0]   # TER always in blue
COULEUR_TGV = couleurs[1]   # TGV always in orange
COULEUR_ALERTE = '#d64545'  # red only for the regions / routes that need attention
COULEUR_OK = couleurs[2]
GRIS = '#8a94a6'

# Default attention threshold (TER regularity objective, can be changed in the sidebar)
SEUIL_DEFAUT = 90.0

# Old regions (before the 2016 reform) and commercial lots (2025) -> current administrative region
# This mapping is needed to compare 2013-2017 with 2018-2026 on the same perimeter
REGION_ACTUELLE = {
    'Alsace': 'Grand Est', 'Champagne Ardenne': 'Grand Est', 'Lorraine': 'Grand Est', 'Grand Est': 'Grand Est',
    'Aquitaine': 'Nouvelle-Aquitaine', 'Limousin': 'Nouvelle-Aquitaine', 'Poitou Charentes': 'Nouvelle-Aquitaine',
    'Nouvelle Aquitaine': 'Nouvelle-Aquitaine',
    'Auvergne': 'Auvergne-Rhône-Alpes', 'Rhône Alpes': 'Auvergne-Rhône-Alpes',
    'Auvergne-Rhône-Alpes': 'Auvergne-Rhône-Alpes',
    'Basse Normandie': 'Normandie', 'Haute Normandie': 'Normandie', 'Normandie': 'Normandie',
    'Bourgogne': 'Bourgogne-Franche-Comté', 'Franche Comté': 'Bourgogne-Franche-Comté',
    'Bourgogne-Franche-Comté': 'Bourgogne-Franche-Comté',
    'Centre': 'Centre-Val de Loire', 'Centre Val-de-Loire': 'Centre-Val de Loire',
    'Languedoc Roussillon': 'Occitanie', 'Midi Pyrénées': 'Occitanie', 'Occitanie': 'Occitanie',
    'Nord Pas de Calais': 'Hauts-de-France', 'Picardie': 'Hauts-de-France', 'Hauts-de-France': 'Hauts-de-France',
    'Etoile Amiens': 'Hauts-de-France',
    'Pays-de-la-Loire': 'Pays de la Loire', 'Loire Océan': 'Pays de la Loire',
    "Provence Alpes Côte d'Azur": "Provence-Alpes-Côte d'Azur", 'Sud Azur': "Provence-Alpes-Côte d'Azur",
    'Bretagne': 'Bretagne',
}

# TGV stations : current region (or country) and coordinates (city level, used for the map)
GARES = {
    'AIX EN PROVENCE TGV': ("Provence-Alpes-Côte d'Azur", 43.455, 5.317),
    'ANGERS SAINT LAUD': ('Pays de la Loire', 47.464, -0.556),
    'ANGOULEME': ('Nouvelle-Aquitaine', 45.653, 0.165),
    'ANNECY': ('Auvergne-Rhône-Alpes', 45.902, 6.122),
    'ARRAS': ('Hauts-de-France', 50.287, 2.781),
    'AVIGNON TGV': ("Provence-Alpes-Côte d'Azur", 43.922, 4.786),
    'BARCELONA': ('Espagne', 41.379, 2.140),
    'BELLEGARDE (AIN)': ('Auvergne-Rhône-Alpes', 46.109, 5.826),
    'BESANCON FRANCHE COMTE TGV': ('Bourgogne-Franche-Comté', 47.307, 5.954),
    'BORDEAUX ST JEAN': ('Nouvelle-Aquitaine', 44.826, -0.556),
    'BREST': ('Bretagne', 48.388, -4.479),
    'CHAMBERY CHALLES LES EAUX': ('Auvergne-Rhône-Alpes', 45.571, 5.920),
    'DIJON VILLE': ('Bourgogne-Franche-Comté', 47.323, 5.027),
    'DOUAI': ('Hauts-de-France', 50.371, 3.091),
    'DUNKERQUE': ('Hauts-de-France', 51.031, 2.369),
    'FRANCFORT': ('Allemagne', 50.107, 8.663),
    'GENEVE': ('Suisse', 46.210, 6.142),
    'GRENOBLE': ('Auvergne-Rhône-Alpes', 45.191, 5.715),
    'ITALIE': ('Italie', 45.486, 9.204),
    'LA ROCHELLE VILLE': ('Nouvelle-Aquitaine', 46.153, -1.145),
    'LAUSANNE': ('Suisse', 46.517, 6.629),
    'LAVAL': ('Pays de la Loire', 48.077, -0.762),
    'LE CREUSOT MONTCEAU MONTCHANIN': ('Bourgogne-Franche-Comté', 46.765, 4.499),
    'LE MANS': ('Pays de la Loire', 47.995, 0.192),
    'LILLE': ('Hauts-de-France', 50.639, 3.075),
    'LYON PART DIEU': ('Auvergne-Rhône-Alpes', 45.760, 4.859),
    'MACON LOCHE': ('Bourgogne-Franche-Comté', 46.282, 4.779),
    'MADRID': ('Espagne', 40.407, -3.689),
    'MARNE LA VALLEE': ('Île-de-France', 48.870, 2.783),
    'MARSEILLE ST CHARLES': ("Provence-Alpes-Côte d'Azur", 43.303, 5.380),
    'METZ': ('Grand Est', 49.110, 6.177),
    'MONTPELLIER': ('Occitanie', 43.605, 3.881),
    'MULHOUSE VILLE': ('Grand Est', 47.742, 7.343),
    'NANCY': ('Grand Est', 48.690, 6.174),
    'NANTES': ('Pays de la Loire', 47.217, -1.542),
    'NICE VILLE': ("Provence-Alpes-Côte d'Azur", 43.705, 7.262),
    'NIMES': ('Occitanie', 43.832, 4.366),
    'PARIS EST': ('Île-de-France', 48.877, 2.359),
    'PARIS LYON': ('Île-de-France', 48.844, 2.374),
    'PARIS MONTPARNASSE': ('Île-de-France', 48.841, 2.320),
    'PARIS NORD': ('Île-de-France', 48.881, 2.355),
    'PARIS VAUGIRARD': ('Île-de-France', 48.838, 2.317),
    'PERPIGNAN': ('Occitanie', 42.696, 2.879),
    'POITIERS': ('Nouvelle-Aquitaine', 46.582, 0.333),
    'QUIMPER': ('Bretagne', 47.995, -4.092),
    'REIMS': ('Grand Est', 49.259, 4.024),
    'RENNES': ('Bretagne', 48.103, -1.672),
    'SAINT ETIENNE CHATEAUCREUX': ('Auvergne-Rhône-Alpes', 45.443, 4.400),
    'ST MALO': ('Bretagne', 48.646, -2.004),
    'ST PIERRE DES CORPS': ('Centre-Val de Loire', 47.386, 0.723),
    'STRASBOURG': ('Grand Est', 48.585, 7.734),
    'STUTTGART': ('Allemagne', 48.784, 9.182),
    'TOULON': ("Provence-Alpes-Côte d'Azur", 43.128, 5.930),
    'TOULOUSE MATABIAU': ('Occitanie', 43.611, 1.454),
    'TOURCOING': ('Hauts-de-France', 50.717, 3.163),
    'TOURS': ('Centre-Val de Loire', 47.390, 0.694),
    'VALENCE ALIXAN TGV': ('Auvergne-Rhône-Alpes', 44.991, 4.978),
    'VANNES': ('Bretagne', 47.664, -2.752),
    'ZURICH': ('Suisse', 47.378, 8.540),
}

# The Paris terminal of a route gives its axis (useful drill-down : Axe -> Liaison -> Mois)
AXE_PAR_GARE_PARIS = {
    'PARIS LYON': 'Sud-Est', 'PARIS MONTPARNASSE': 'Atlantique', 'PARIS VAUGIRARD': 'Atlantique',
    'PARIS NORD': 'Nord', 'PARIS EST': 'Est',
}

# Causes of delay (TGV dataset) : column name -> short label
CAUSES = {
    'Prct retard pour causes externes': 'Externes (météo, intrusions, malveillance...)',
    'Prct retard pour cause infrastructure': 'Infrastructure (voies, signalisation, travaux)',
    'Prct retard pour cause gestion trafic': 'Gestion du trafic',
    'Prct retard pour cause matériel roulant': 'Matériel roulant',
    'Prct retard pour cause gestion en gare et réutilisation de matériel': 'Gestion en gare',
    'Prct retard pour cause prise en compte voyageurs (affluence, gestions PSH, correspondances)': 'Voyageurs (affluence, PSH...)',
}

MOIS = 'Jan Fév Mar Avr Mai Juin Juil Août Sep Oct Nov Déc'.split()
