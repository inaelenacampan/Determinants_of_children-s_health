# Étude sur les facteurs qui déterminent la santé des enfants aux États-Unis
## Une analyse statistique, économétrique et temporelle 

[ Python pour la Data Science, 2A Ensae ]

Groupe TP n°5 
*Auteurs : Ina Campan, Rachel Issiakou, Samuel Romano*

## Table des matières

 1. [Sujet](#subheading-1)
 2. [Problématique](#subheading-2)
 3. [Bases de données](#subheading-3)
 4. [Visualisation des données et modélisation](#subheading-4)
 5. [Navigation au sein du projet](#subheading-5)
 6. [Résultats principaux et conclusions](#subheading-6)

## Sujet <a name="subheading-1">

## Problématique <a name="subheading-2">

## Bases de données <a name="subheading-3">

I. Le **[NSCH](https://www.census.gov/programs-surveys/nsch/data/datasets.html)** (National Survey of Children’s Health) est une enquête auprès des ménages qui produit des données nationales et au niveau des États sur la santé physique et émotionnelle des enfants âgés de 0 à 17 ans aux États-Unis. L’enquête recueille des informations liées à la santé et au bien-être des enfants, notamment l’accès et le recours aux soins de santé, les interactions familiales, la santé des parents, les expériences scolaires et extrascolaires, ainsi que les caractéristiques du quartier de résidence. Depuis 2016, le NSCH est une enquête annuelle. L’enquête fournit des estimations nationales chaque année et des estimations au niveau des États en combinant 2 ou 3 années de données. Avant 2016, l’enquête était réalisée tous les 4 ans.

II. **[Les données géographiques](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html)** permettent de tracer sur un fond de carte des différents états des US des résultats issus de la base de données antérieure.

III. **[Les données économiques](https://apps.bea.gov/regional/downloadzip.htm)** permettent d'obtenir un indice synthétique plus fiable au niveau des état Américains. Le BEA (Bureau of Economic Analysis) c'est l’agence officielle américaine qui mesure l'activité économique : PIB, revenu, commerce, productivité, comptes régionaux, etc. Elle produit des données standardisées, fiables et comparables dans le temps, utilisées par le gouvernement, les chercheurs et les institutions internationales.

## Visualisation des données et modélisation <a name="subheading-4">

Pour s'y prendre une sélection de variable est faite à travers une dimension santé physique, une dimension santé mentale, des questions d'assurance et environnement familial.

Pour gérer les valeurs manquantes, non-dues à la forme du questionnaire, nous utilisons une imputation en utilisant la fonction ```KKNImputer``` de la librairie scikit-learn. Les valeurs manquantes de l'échantillon sont imputées en utilisant la valeur moyenne des ```n_neighbors``` plus proches voisins trouvés dans l’ensemble.

Pour comprendre la structure des données, nous effectuons une analyse des correspondances multiples et une carte de chaleur des corrélations (heatmap).

## Navigation au sein du projet <a name="subheading-5">

La fichier qui décrit l'ensemble des résultats en détail est "Determinants_of_children-s_health.ipynb".

Dans un terminal (depuis le dossier ```Determinants_of_children-s_health```), commencez par la commande : 
```bash
pip install -r requirements.txt 
```

Les fonctions annexes sont regroupés dans le dossier ```script```.

Pour s'y prendre une documentation est également fournie en format html dans le dossier ```docs```. 
```bash
pdoc --output-dir docs script
```

Pour une approche plus interactive, dans le terminal commencez par la commande :
```bash
pdoc script 
```

## Résultats principaux et conclusions <a name="subheading-6">
![Carte interactive](docs/USA_Map_2024.png)
![Classement des états](docs/classement_etats_sante.jpg)