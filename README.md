# La ponctualité ferroviaire en France (TER vs TGV)

**BDML1 Individual Project — Data Visualization, Data Storytelling & Business Intelligence**

| | |
|---|---|
| **Étudiant** | Thomas BELOT — [thomas.belot@efrei.net](mailto:thomas.belot@efrei.net) — [LinkedIn](https://www.linkedin.com/in/thomas-belot/) |
| **Formation** | 2ème année ingénieur - apprentissage - Big Data & Machine Learning |
| **Groupe(s)** | I2-APP-BDML1 |
| **Vidéo de démonstration** | [`Video_20261785_BELOT_BDML1.mp4`](Video_20261785_BELOT_BDML1.mp4) |
| **Code source** | https://github.com/Thomsys/Streamlit_20261785_BELOT_BDML1 |
| **Professeur** | Mano Joseph MATHEW — [mano.mathew@efrei.fr](mailto:mano.mathew@efrei.fr) |
| **École** | Efrei — Paris Panthéon-Assas Université |

Application Streamlit d'aide à la décision qui analyse la régularité des trains régionaux (TER) et la compare
à celle des TGV, région par région, de 2018 à 2026.

---

## 1. Problème et décideur

| | |
|---|---|
| **Décideur cible** | Direction des transports d'un Conseil régional (autorité organisatrice des TER), avec ses interlocuteurs SNCF Voyageurs et SNCF Réseau |
| **Décisions appuyées** | Suivre l'objectif de régularité de la convention TER, déclencher un plan d'action, se comparer aux autres régions, identifier les liaisons TGV, les mois et les causes sur lesquels agir |
| **Narration** | L'application commence par l'Executive Overview (accroche + contexte + KPIs), puis : Contexte → Données → Analyse → Comparaison → Decision Support |

### Questions analytiques

1. **Q1** — Comment la ponctualité TER et TGV a-t-elle évolué depuis 2018 ? L'année en cours est-elle meilleure ou pire ?
2. **Q2** — Quelles régions ont la meilleure et la moins bonne régularité TER, et lesquelles sont sous le seuil d'alerte ?
3. **Q3** — Quelles liaisons TGV et quelles causes expliquent les retards ?
4. **Q4** — Dans chaque région, le TGV fait-il mieux ou moins bien que le TER ? Les deux évoluent-ils ensemble ?
5. **Q5** — Y a-t-il des mois « à risque » qui reviennent chaque année ?

## 2. Données

Deux jeux de données SNCF publiés sur **data.gouv.fr** (licence ODbL), validés par l'enseignant :

| Jeu | Page data.gouv.fr | Lien de téléchargement direct (CSV, séparateur `;`) | Taille |
|---|---|---|---|
| Régularité mensuelle TER | https://www.data.gouv.fr/datasets/regularite-mensuelle-ter-sncf | https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/regularite-mensuelle-ter/exports/csv?use_labels=true&delimiter=%3B | 2 380 lignes × 9 colonnes, 01/2013 → 08/2026 |
| Régularité mensuelle TGV par liaison (AQST) | https://www.data.gouv.fr/datasets/regularite-mensuelle-tgv-par-liaisons | https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/regularite-mensuelle-tgv-aqst/exports/csv?use_labels=true&delimiter=%3B | 12 907 lignes × 26 colonnes, 01/2018 → 09/2026 |

Les fichiers ont été téléchargés le 5 novembre 2026 et sont inclus dans `data/`.
`data/regions.geojson` (contours des régions, version simplifiée) provient de
https://github.com/gregoiredavid/france-geojson (licence ouverte).

**Pour mettre à jour les données**, il suffit de retélécharger les deux CSV avec les liens ci-dessus (garder le
séparateur `;`) et de les enregistrer sous les mêmes noms dans `data/`.

## 3. Installation et lancement

```bash
git clone https://github.com/Thomsys/Streamlit_20261785_BELOT_BDML1.git
cd Streamlit_20261785_BELOT_BDML1
python -m venv .venv
# Windows : .venv\Scripts\activate    |    macOS / Linux : source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre sur http://localhost:8501. Le chargement et le nettoyage sont mis en cache
(`st.cache_data`) : seul le premier affichage prend quelques secondes.

## 4. Structure du projet

```
Streamlit_20261785_BELOT_BDML1/
├── app.py                      # point d'entrée : logo, auteur, navigation, filtres globaux
├── requirements.txt
├── README.md
├── Video_20261785_BELOT_BDML1.mp4   # vidéo de démonstration
├── .streamlit/config.toml      # thème (couleurs, polices, barre latérale)
├── data/
│   ├── regularite-mensuelle-ter.csv
│   ├── regularite-mensuelle-tgv-aqst.csv
│   ├── regions.geojson         # contours des régions (carte)
│   └── logo_efrei.png          # logo affiché dans la barre latérale
└── src/
    ├── config.py               # chemins, palette, tables de correspondance (régions, 59 gares TGV)
    ├── data.py                 # chargement, nettoyage, validation, jointure (cache)
    ├── kpis.py                 # calcul des indicateurs
    ├── charts.py               # style commun des graphiques
    └── sections/               # une page = un module
        ├── executif.py         # 1. Executive Overview (hook + contexte, KPIs vs N-1, tendance, classement)
        ├── accueil.py          # 2. Contexte & questions (décideur, questions analytiques, données)
        ├── qualite.py          # 3. Données & qualité (sources, nettoyage, hypothèses, limites, export)
        ├── ter.py              # 4. TER : carte, benchmark, drill-down, saisonnalité, anomalies
        ├── tgv.py              # 5. TGV : axes → liaisons → mois, causes, carte des gares
        ├── comparaison.py      # 6. TER vs TGV, scorecard, simulation what-if
        └── decision.py         # 7. Decision Support / Recommendations (section finale)
```

## 5. Nettoyage et transformations

**TER**
- 37 mois sans mesure (Lorraine 2013-2016, qui refusait de transmettre ses données, et 2 mois du Nord-Pas-de-Calais) : exclus des calculs.
- Réforme territoriale de 2016 : les anciennes régions (Alsace, Picardie, Limousin...) sont rattachées à leur région actuelle pour obtenir des séries continues.
- Lots ouverts à la concurrence en 2025 (Sud Azur, Étoile d'Amiens, Loire Océan) : additionnés à leur région.
- Périmètres partiels signalés et exclus des classements (ex. Nouvelle-Aquitaine 2018-2020 = Aquitaine seule).
- Validation : taux recalculé = 1 − retards / trains ayant circulé. Il reproduit le taux publié sauf pour 12 lignes de 2020, où le fichier source est incohérent avec ses propres comptages.

**TGV**
- 43 valeurs négatives (trains en retard > 30 min) et 2 retards moyens négatifs → valeurs manquantes.
- 73 mois sans circulation (confinement 2020) : conservés mais exclus des taux.
- 84 lignes en double sur la clé mois + liaison (découpage National / International en 2025) → additionnées.
- Enrichissement : région de chaque gare, axe (Sud-Est, Atlantique, Nord, Est, Intersecteurs, International).
- Rupture de série détectée sur les causes de retard en mai 2026 (la part « Infrastructure » passe de ~20 % à 6 %) : signalée, non corrigée.

**Jointure** : mois × région actuelle. Une liaison TGV compte pour la région de chacune de ses deux gares (hors Paris et étranger). Les TGV sont analysés jusqu'au dernier mois TER disponible (août 2026).

**Règle de calcul** : tous les taux sont recalculés à partir des sommes de trains, jamais en faisant la moyenne de pourcentages.

## 6. KPIs

| KPI | Définition | Question de gestion |
|---|---|---|
| Régularité TER | 1 − TER en retard / TER ayant circulé | Le service régional atteint-il l'objectif ? |
| Régularité TGV | 1 − TGV en retard / TGV ayant circulé | Le benchmark grande vitesse progresse-t-il ? |
| Taux d'annulation TER | trains annulés / trains programmés | Combien de trains promis n'ont pas roulé ? |
| TGV > 15 min de retard | part des TGV arrivés avec plus de 15 min de retard | Quelle part des retards gêne vraiment les voyageurs ? |
| Retard moyen TGV | retard moyen des TGV en retard (pondéré) | Quelle est la gravité des retards ? |
| Régions sous le seuil | nombre de régions sous le seuil d'alerte (90 % par défaut) | Combien de territoires demandent une action ? |
| Meilleure / moins bonne région | classement de la régularité TER | Qui est en tête, qui décroche ? |
| Part des retards à leviers internes | causes hors « externes » | Quelle part des retards est actionnable ? |

Chaque KPI est comparé aux **mêmes mois de l'année précédente**.

## 7. Couverture des consignes

| Exigence | Où |
|---|---|
| Executive Overview en ouverture | Première page de l'application |
| ≥ 5 KPIs | Executive Overview (9 indicateurs, avec évolution vs N-1) |
| ≥ 5 visualisations interactives | Plus de 20 graphiques Plotly / Altair (survol, zoom, sélection) |
| ≥ 4 filtres | Barre latérale : année, mois, régions, seuil d'alerte, axes TGV ; et par page : indicateur, axe, top N, liaison, région, poids, simulation |
| Tableau interactif | Benchmark TER, scorecard, données nettoyées (recherche + tri) |
| Carte et série temporelle | Carte choroplèthe des régions, carte des gares TGV, courbe mensuelle 2018-2026 |
| Comparaison / benchmark | Région vs moyenne France, année vs N-1, TER vs TGV (actuel, benchmark, écart, % d'évolution) |
| Classement / segmentation | Classement des régions, top / bottom N liaisons, axes TGV, scorecard composite |
| Drill-down | France → région → périmètre publié → mois (TER) ; axe → liaison → mois (TGV) |
| Détection d'anomalies | Mois à plus de 2 écarts-types sous la normale de la région, rupture de série des causes |
| What-if | Simulation : réduction d'une cause de retard TGV |
| 3 constats, 2 recommandations, 1 limite | Page finale « Decision Support / Recommendations » |
| Export | Boutons de téléchargement CSV (benchmark, liaisons, scorecard, données nettoyées) |
| Cache | `st.cache_data` sur tout le chargement et le nettoyage |

## 8. Principaux résultats (janvier–août 2026 vs janvier–août 2025)

- **Dégradation générale** : régularité TER 90,1 % (−1,6 pt), TGV 81,0 % (−4,9 pts) ; les 11 régions reculent. C'est la pire année TER depuis 2018 sur ces mêmes mois.
- **Fracture territoriale** : 9 points d'écart entre la Bretagne (94,0 %) et l'Occitanie (84,9 %) ; 7 régions sur 11 sont sous 90 %. Les régions faibles en TER le sont aussi en TGV (r = 0,84 sur 2018-2026).
- **Retards actionnables et prévisibles** : plus de 80 % des retards TGV relèvent de causes internes au système ferroviaire (2022-2025) ; octobre, novembre et décembre sont les mois les plus faibles chaque année.

## 9. Limites

- Les seuils de retard ne sont pas identiques pour le TER (5 min) et pour le TGV (selon la durée du trajet, définition AQST).
- Le nombre de voyageurs n'est pas connu : tous les trains ont le même poids.
- Les causes de retard ne sont publiées que pour le TGV, et changent de méthode en mai 2026.
- Corrélation ≠ causalité : le lien TER / TGV d'une région suggère des causes communes sans les prouver.
- Le score composite dépend de poids choisis par l'utilisateur ; ils ne sont pas objectivement corrects.

## 10. Choix techniques

- Code structuré en modules (une page par fichier), dans la continuité du TP Uber : même thème, même palette (TER en bleu, TGV en orange, rouge réservé aux alertes), mêmes fonctions de regroupement (`groupby` + agrégations) et même démarche Question → Observation → Interprétation que dans mes notebooks.
- Plotly pour la plupart des graphiques, Altair pour les heatmaps.
- Les cartes utilisent `px.choropleth` / `px.scatter_geo`, sans fond de carte à tuiles (aucun jeton ni service externe requis).
