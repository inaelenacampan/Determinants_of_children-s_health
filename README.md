# Étude sur les facteurs qui déterminent la santé des enfants aux États-Unis
## Une analyse statistique, économétrique et temporelle 

[ Python pour la Data Science, 2A Ensae ]

Groupe TP n°5 
*Auteurs : Ina Campan, Rachel Issiakou, Samuel Romano*

## Table des matières

 1. [Revue de Littérature](#subheading-1)
 2. [Sujet et problématique](#subheading-2)
 3. [Bases de données](#subheading-3)
 4. [Visualisation des données et modélisation](#subheading-4)
 5. [Navigation au sein du projet](#subheading-5)
 6. [Résultats principaux et conclusions](#subheading-6)

## Revue de Littérature <a name="subheading-1">

S'intéresser à la santé des enfants, c’est aussi s’intéresser à la santé des adultes de demain. Dans un environnement beaucoup moins certain, d’un point de vue climatique, économique et politique, l’enjeu de conduire les enfants vers la vie adulte dans les meilleures conditions possibles pour chacun n’a jamais été aussi complexe. De nombreuses recherches portent sur la santé de la population générale d’un pays et, dans une moindre mesure, sur celle des moins de 18 ans.

### État de santé des enfants aux États-Unis

Selon Forrest et al. (2025) et le rapport de l'UNICEF sur le bien-être des enfants (2022),  la santé des enfants s’est détériorée aux États-Unis lors des 17 dernières années. Trois critères sont étudiés plus en détails : 

* La mortalité des enfants : les nourrissons et les 1-19 ont beaucoup plus de chances de décéder aux États-Unis que dans le reste des pays de l’OCDE. Ainsi, les moins de 1 an ont 78% de risques de décéder en plus par rapport à la moyenne de l’OCDE. Chez les nourrissons, la mortalité est dûe aux naissances prématurées alors que chez les plus âgés, les décès liés à la santé sont le plus souvent des suicides.
* Les maladies chroniques : les conditions chroniques ont augmenté de 25,8% à 31% entre 2011 et 2023. Cela est dû majoritairement à une hausse des conditions liées à la santé mentale, notamment une hausse des personnes diagnostiquées pour dépression ou anxiété.
* Obésité : le taux d'obésité infantile est passé de 17,0 % (2007) à 20,9 % (2023)

### Indices de santé et de bien-être 

L’UNICEF propose dans son étude un outil dimensionnel pour mesurer le bien-être, dont la santé n’est qu’une composante. Liée à la sécurité, celle-ci inclut la mortalité infantile, le faible poids à la naissance, les taux de vaccination (rougeole, polio, DTP3) et la mortalité des 1-19 ans.
Pour cet indice, le score de chaque dimension est obtenu en faisant la moyenne des composantes qui la constituent et le classement général final est établi sur la base de la moyenne des notes obtenues dans les cinq dimensions. En effet, le but de cette étude est de comparer le bien-être dans 29 pays riches. Les États-Unis, en termes de bien-être global, sont 24e sur 29. 

L’étude du JAMA combine 3 sources de données pour construire ses indices, dont des Enquêtes nationales représentatives (NHANES, NHIS, NSCH, PSID, YRBS) basées sur les rapports des parents ou des jeunes. La méthode de mesure la plus utilisé est celle des le rapport de taux (Rate Ratios - RR). Il compare la fréquence d'un événement (décès ou maladie) soit entre deux zones (USA vs OCDE). Ainsi, le taux de mortalité annuel des États-Unis divisé par celui de l’OCDE constitue ce ```Rate Ratios```, outil comparatif.

### Choix de la base de données principale

À partir de ces références, nous avons retenu la base NSCH, qui répond au critère d’accessibilité en ligne sans nécessité de demande spécifique pour accéder aux données. Elle présente également l’avantage de couvrir l’ensemble des groupes d’âge des enfants et adolescents de moins de 18 ans.

### Références :

1. Forrest, C. B., Koenigsberg, L. J., Eddy Harvey, F., Maltenfort, M. G., & Halfon, N. (2025). Trends in US Children's Mortality, Chronic Conditions, Obesity, Functional Status, and Symptoms. JAMA, 334(6), 509–516. https://doi.org/10.1001/jama.2025.9855
2. UNICEF. (2022). Le bien-être des enfants dans les pays riches (Bilan Innocenti 11). Centre de recherche de l’UNICEF. https://www.unicef.fr/wp-content/uploads/2022/07/Le-bien-etre-des-enfants-dans-les-pays-riches.pdf

## Sujet et problématique <a name="subheading-2">

Dans ce projet, nous proposons de construire un indice synthétique de santé des enfants à l’échelle des États américains, à partir des données issues de la base NSCH. Notre objectif est de développer un indicateur multidimensionnel intégrant simultanément plusieurs dimensions de la santé : la santé physique, la santé mentale et la santé économique.

Cet indice vise à permettre l’identification de disparités géographiques entre les États, l’analyse des évolutions temporelles d’une année à l’autre, ainsi que la comparaison de nos résultats avec ceux d’autres indices de santé ou de bien-être existants.

## Bases de données <a name="subheading-3">

I. Le **[NSCH](https://www.census.gov/programs-surveys/nsch/data/datasets.html)** (National Survey of Children’s Health) est une enquête auprès des ménages qui produit des données nationales et au niveau des États sur la santé physique et émotionnelle des enfants âgés de 0 à 17 ans aux États-Unis. L’enquête recueille des informations liées à la santé et au bien-être des enfants, notamment l’accès et le recours aux soins de santé, les interactions familiales, la santé des parents, les expériences scolaires et extrascolaires, ainsi que les caractéristiques du quartier de résidence. Depuis 2016, le NSCH est une enquête annuelle. L’enquête fournit des estimations nationales chaque année et des estimations au niveau des États en combinant 2 ou 3 années de données. Avant 2016, l’enquête était réalisée tous les 4 ans.

II. **[Les données géographiques](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html)** permettent de tracer sur un fond de carte des différents états des US des résultats issus de la base de données antérieure.

III. **[Les données économiques](https://apps.bea.gov/regional/downloadzip.htm)** permettent d'obtenir un indice synthétique plus fiable au niveau des état Américains. Le BEA (Bureau of Economic Analysis) c'est l’agence officielle américaine qui mesure l'activité économique : PIB, revenu, commerce, productivité, comptes régionaux, etc. Elle produit des données standardisées, fiables et comparables dans le temps, utilisées par le gouvernement, les chercheurs et les institutions internationales.

IV. **[Les données d'America's Health Rankings](https://www.americashealthrankings.org/publications/articles/state-rankings-since-1990)** fournissent des indicateurs de santé agrégés au niveau de chaque État américain depuis 1990. Le classement général des États est établi à partir de divers indicateurs répartis en cinq catégories liées à la santé : facteurs sociaux et économiques, environnement physique, comportements, soins cliniques et résultats en matière de santé.

## Visualisation des données et modélisation <a name="subheading-4">

Pour s'y prendre, une sélection de variable est faite à travers une dimension santé physique, une dimension santé mentale, des questions d'assurance et environnement familial, variables économiques.

Pour traiter les valeurs manquantes, lorsqu’elles ne sont pas dues à la structure du questionnaire le cas échéant, nous utilisons une imputation en utilisant la fonction ```KKNImputer``` de la librairie scikit-learn. Les valeurs manquantes de l'échantillon sont imputées en utilisant la valeur moyenne des ```n_neighbors``` plus proches voisins trouvés dans l’ensemble.

Pour comprendre la structure des données, nous réalisons plusieurs analyses : analyses des correspondances multiples, cartes de chaleur des corrélations (heatmaps), analyses en composantes principales (ACP), ainsi que des visualisations graphiques telles que boxplots, violinplots ou barplots.

L’indice de santé, normalisé sur un intervalle de 0 à 1 (plus la valeur est élevée, meilleure est la santé), est construit en s’inspirant de l’indice de développement humain, sous la forme d’une moyenne géométrique de trois dimensions, comme mentionné précédemment. Les sous-indicateurs sont calculés soit comme des moyennes simples, soit comme des moyennes pondérées, en utilisant comme pondération les charges factorielles de chaque variable issues des ACP.

## Navigation au sein du projet <a name="subheading-5">

La fichier qui décrit l'ensemble des analyses et des résultats est "Determinants_of_children-s_health.ipynb".

Dans un terminal (depuis le dossier ```Determinants_of_children-s_health```), commencez par la commande : 
```bash
pip install -r requirements.txt 
```

Les fonctions annexes sont regroupés dans le dossier ```script```.

Pour s'y prendre une documentation est également fournie en format html dans le dossier ```docs```. 
```bash
pdoc --output-dir docs script
```

Pour une approche plus interactive de la documentation, dans le terminal commencez par la commande :
```bash
pdoc script 
```

## Résultats principaux et conclusions <a name="subheading-6">

![Carte interactive](docs/USA_Map_2024.png)
![Classement des états](docs/classement_etats_sante.jpg)