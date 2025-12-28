import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.stats import norm
from functools import reduce


def weighted_mean(x, w):
    """
    Calculer la moyenne pondérée

    Args :
        x : variable numérique
        w : poids

    Returns:
        float - moyenne pondérée
    """
    return (x * w).sum() / w.sum()


def scale_transformation(year, dfs, variables, cat_variables, bin_variables, groups, theme):
    """
    Applique des transformations d'échelle et d'orientation aux variables
    d'un thème donné.

    Cette fonction permet :
    - de sélectionner les variables pertinentes pour une année donnée,
    - d'harmoniser le sens des variables catégorielles (inversion d'échelle),
    - de transformer les variables binaires selon la logique du thème étudié.

    Args:
        year : str
            Année d'analyse utilisée pour extraire le DataFrame correspondant.

        dfs : dict
            Dictionnaire de DataFrames indexé par année.

        variables : list
            Liste des variables quantitatives à inclure dans l'analyse.

        cat_variables : list
            Liste des variables catégorielles ordinales codées sur une échelle
            de 1 à 5, dont le sens doit être inversé afin que des valeurs plus
            élevées correspondent à une meilleure situation de santé.

        bin_variables : list
            Liste des variables binaires (codées 1/2) nécessitant une
            transformation spécifique.

        groups : list
            Liste de variables supplémentaires (variables de regroupement et de poids)
            à conserver dans le DataFrame final.

        theme : str
            Thème d'analyse. Lorsque le thème est "micro_eco", les variables
            binaires sont transformées de façon symétrique ; sinon, une
            transformation standard est appliquée.

    Returns:
        pandas.DataFrame
            DataFrame contenant uniquement les variables sélectionnées,
            après transformation des échelles et harmonisation du sens
            des indicateurs.
    """
    # extract dataframe
    df = dfs[year]

    all_variables = list(set(variables) | set(groups))

    df_theme = df[all_variables].copy()
    if theme == "health":
        df_theme[cat_variables] = 6 - df_theme[cat_variables]
    else:
        for col in cat_variables:
            df_theme[col] = df_theme[col].nunique() + 1 - df_theme[col]

    if theme == "micro_eco":
        for var in bin_variables:
            df_theme[var] = abs(df_theme[var] - 2)
    else:
        for var in bin_variables:
            df_theme[var] = df_theme[var] - 1

    return df_theme


def state_indicator(df_theme, variables, theme, year, minimum, maximum):
    """
    Calcule un sous-indicateur de santé agrégé par État pour un thème donné
    et une année donnée.

    Args:
        df_theme : pandas.DataFrame
            DataFrame contenant les variables thématiques déjà transformées
            (échelles harmonisées), ainsi que les colonnes :
            - "FIPSST" : code de l'État
            - "FWC" : poids utilisés pour le calcul des moyennes pondérées.

        variables : list
            Liste des variables quantitatives entrant dans le calcul
            du sous-indicateur.

        theme : str
            Nom du thème étudié ("micro_eco", "health", "mental_health"),
            utilisé pour nommer la colonne du sous-indicateur.

        year : str
            Année d'analyse, utilisée pour nommer la colonne du sous-indicateur.

        minimum : float
            Valeur minimale théorique utilisée pour la
            normalisation du sous-indicateur.

        maximum : float
            Valeur maximale théorique utilisée pour la
            normalisation du sous-indicateur.

    Returns:
        pandas.Series
            Série indexée par le code FIPS des États (FIPSST) contenant
            le sous-indicateur normalisé sur l'intervalle [0, 1] pour
            le thème et l'année considérés.
    """
    # groupby -- préciser les colonnes d'interet afin d'éviter des soucis avec la mise-a-jour pandas
    # => les warnings disparaissent
    df_theme = df_theme.groupby("FIPSST")[variables + ["FWC"]].apply(
        lambda g: pd.Series({var: weighted_mean(g[var], g["FWC"]) for var in variables}))

    X = df_theme[variables]
    df_theme[f"sub_indicator_{theme}_{year}"] = X.mean(axis=1)

    indicator_column = df_theme[f"sub_indicator_{theme}_{year}"]
    df_theme[f"sub_indicator_{theme}_{year}"] = (indicator_column - minimum)/(maximum - minimum)
    return df_theme[f"sub_indicator_{theme}_{year}"]


def calculate_indicator(year, dfs, theme, cat_variables, bin_variables, groups):
    """
    -- add legend
    """
    variables = cat_variables + bin_variables
    df_theme = scale_transformation(year, dfs, variables, cat_variables, bin_variables, groups,
                                    theme)

    maximum = df_theme[variables].max().sum()/len(df_theme[variables].columns)
    minimum = df_theme[variables].min().sum()/len(df_theme[variables].columns)

    indicator = state_indicator(df_theme, variables, theme, year, minimum, maximum)
    return indicator


def economic_pca_indicator(df, state_eco_vars, year):
    """
    Construit un sous-indicateur macro-économique de santé au niveau des États
    à l'aide d'une Analyse en Composantes Principales (ACP).


    Args:
        df : pandas.DataFrame
            DataFrame contenant les variables macro-économiques par État.
            Doit inclure une colonne "FIPSST" ainsi que les variables listées
            dans `state_eco_vars`.

        state_eco_vars : list
            Liste des variables macro-économiques quantitatives utilisées
            pour la construction du sous-indicateur.

        year : str
            Année d'analyse, utilisée pour nommer la colonne du sous-indicateur.

    Returns:
        pandas.DataFrame
            DataFrame contenant :
            - la colonne "FIPSST" (code de l'État),
            - la colonne "sub_indicator_macroeco_<year>" correspondant
            au sous-indicateur macro-économique normalisé sur [0, 1].
    """
    df_macro_state = df[["FIPSST"] + state_eco_vars].copy()
    X = df_macro_state[state_eco_vars]

    scaler = StandardScaler()
    X_std = scaler.fit_transform(X)
    X_std = pd.DataFrame(X_std, columns=state_eco_vars, index=df_macro_state.index)

    pca = PCA()
    pca.fit(X_std)

    loadings = pca.components_[0]
    weights_raw = abs(loadings)
    weights = weights_raw / weights_raw.sum()
    df_macro_state[f"sub_indicator_macroeco_{year}"] = (X_std * weights).sum(axis=1)

    # Afin de se ramener à des valeurs entre 0 et 1
    # on normalise notre indicateur et on effectue la transformation I <- F(I)
    # où F est la fonction de répartition de la loi normale standard.

    std_indic = (
        df_macro_state[f"sub_indicator_macroeco_{year}"]
        - df_macro_state[f"sub_indicator_macroeco_{year}"].mean()
    ) / df_macro_state[f"sub_indicator_macroeco_{year}"].std()

    df_macro_state[f"sub_indicator_macroeco_{year}"] = norm.cdf(std_indic)
    df_macro_state["FIPSST"] = pd.to_numeric(df_macro_state["FIPSST"], errors="coerce")
    return df_macro_state


def average_economic_indicator(year, df_eco, dfs, theme, cat_variables, bin_variables, groups,
                               state_eco_vars_dict):
    """
    Construit un sous-indicateur économique global par État en combinant
    des dimensions micro-économiques et macro-économiques.

    Args:
        year : str
            Année d'analyse utilisée pour sélectionner les données et nommer
            les colonnes des sous-indicateurs.

        df_eco : pandas.DataFrame
            DataFrame contenant les variables macro-économiques par État,
            incluant la colonne "FIPSST".

        dfs : dict
            Dictionnaire de DataFrames indexé par année contenant les données
            micro-économiques issues de l'enquête NSCH.

        theme : str
            Nom du thème micro-économique utilisé pour la construction du
            sous-indicateur issu des données individuelles.

        cat_variables : list
            Liste des variables catégorielles ordinales nécessitant une
            transformation d'échelle.

        bin_variables : list
            Liste des variables binaires à transformer selon la logique
            du thème étudié.

        groups : list
            Liste de variables supplémentaires conservées lors du calcul
            du sous-indicateur micro-économique.

        state_eco_vars_dict : dict
            Dictionnaire associant à chaque année la liste des variables
            macro-économiques utilisées dans l'ACP.

    Returns:
        pandas.Series
            Série indexée par le code FIPS des États (FIPSST) contenant
            le sous-indicateur économique global normalisé sur l'intervalle
            [0, 1] pour l'année considérée.
    """
    indicator_NSCH = calculate_indicator(year, dfs, theme, cat_variables, bin_variables, groups)
    state_eco_vars = state_eco_vars_dict[year]
    indicator_pca = economic_pca_indicator(df_eco, state_eco_vars, year)

    indicator_eco = indicator_pca.merge(indicator_NSCH, on="FIPSST", how="inner")
    indicator_eco.set_index("FIPSST", inplace=True)
    indicator_eco[f"sub_indicator_eco_{year}"] = (indicator_eco[f"sub_indicator_macroeco_{year}"] +
                                                  indicator_eco[f"sub_indicator_{theme}_{year}"])/2
    return indicator_eco[f"sub_indicator_eco_{year}"]


def over_all_indicators_year(year, df_eco, dfs, groups,
                             mental_category_vars, mental_bin_vars,
                             health_category_vars, health_bin_vars,
                             NSCH_eco_cat_vars, NSCH_eco_bin_vars,
                             state_eco_vars_dict):
    """
    Calcule l'ensemble des sous-indicateurs thématiques de santé des enfants
    au niveau des États pour une année donnée.

    Cette fonction construit trois dimensions :
    - un sous-indicateur de santé mentale,
    - un sous-indicateur de santé physique,
    - un sous-indicateur économique combinant des dimensions micro-
      et macro-économiques.

    Chaque sous-indicateur est normalisé sur l'intervalle [0, 1] et
    agrégé au niveau des États (FIPSST).

    Args:
        year : str
            Année d'analyse utilisée pour sélectionner les données et nommer
            les colonnes des sous-indicateurs.

        df_eco : pandas.DataFrame
            DataFrame contenant les variables macro-économiques par État,
            incluant la colonne "FIPSST".

        dfs : dict
            Dictionnaire de DataFrames indexé par année contenant les données
            issues de l'enquête NSCH.

        groups : list
            Liste des variables de regroupement ou de pondération utilisées
            lors de l'agrégation au niveau des États.

        mental_category_vars : list
            Liste des variables catégorielles ordinales utilisées pour la
            construction du sous-indicateur de santé mentale.

        mental_bin_vars : list
            Liste des variables binaires utilisées pour la construction du
            sous-indicateur de santé mentale.

        health_category_vars : list
            Liste des variables catégorielles ordinales utilisées pour la
            construction du sous-indicateur de santé physique.

        health_bin_vars : list
            Liste des variables binaires utilisées pour la construction du
            sous-indicateur de santé physique.

        NSCH_eco_cat_vars : list
            Liste des variables catégorielles ordinales issues de l’enquête
            NSCH utilisées pour la dimension micro-économique.

        NSCH_eco_bin_vars : list
            Liste des variables binaires issues de l’enquête NSCH utilisées
            pour la dimension micro-économique.

        state_eco_vars_dict : dict
            Dictionnaire associant à chaque année la liste des variables
            macro-économiques utilisées dans la construction de l’indicateur
            économique.

    Returns:
        tuple of pandas.DataFrame
            Tuple contenant trois DataFrames indexés par le code FIPS des États :
            - sous-indicateur de santé mentale,
            - sous-indicateur de santé physique,
            - sous-indicateur économique.

        Chaque DataFrame contient une unique colonne correspondant
        au sous-indicateur et à l'année considérée.
    """

    mental_indicator = calculate_indicator(year, dfs, "mental_health", mental_category_vars,
                                           mental_bin_vars, groups)
    mental_indicator = mental_indicator.to_frame(name=f"sub_indicator_mental_{year}")
    mental = mental_indicator[[f"sub_indicator_mental_{year}"]]

    health_indicator = calculate_indicator(year, dfs, "health", health_category_vars,
                                           health_bin_vars, groups)
    health_indicator = health_indicator.to_frame(name=f"sub_indicator_health_{year}")
    health = health_indicator[[f"sub_indicator_health_{year}"]]

    eco_indicator = average_economic_indicator(year, df_eco, dfs, "micro_eco",
                                               NSCH_eco_cat_vars, NSCH_eco_bin_vars, groups,
                                               state_eco_vars_dict)
    eco_indicator = eco_indicator.to_frame(name=f"sub_indicator_eco_{year}")
    eco = eco_indicator[[f"sub_indicator_eco_{year}"]]

    return mental, health, eco


def global_health_over_years(years, df_eco, dfs, groups,
                             mental_category_vars, mental_bin_vars,
                             health_category_vars, health_bin_vars,
                             NSCH_eco_cat_vars, NSCH_eco_bin_vars,
                             state_eco_vars_dict):

    """
    Construit l'indicateur global de santé des enfants aux États-Unis
    pour plusieurs années, au niveau des États.

    Args:
        years : list
            Liste des années d'analyse.

        df_eco : pandas.DataFrame
            DataFrame contenant les variables macro-économiques par État,
            incluant la colonne "FIPSST".

        dfs : dict
            Dictionnaire de DataFrames indexé par année contenant les données
            issues de l'enquête NSCH.

        groups : list
            Liste des variables de regroupement ou de pondération utilisées
            lors de l'agrégation au niveau des États.

        mental_category_vars : list
            Liste des variables catégorielles ordinales utilisées pour la
            construction du sous-indicateur de santé mentale.

        mental_bin_vars : list
            Liste des variables binaires utilisées pour la construction du
            sous-indicateur de santé mentale.

        health_category_vars : list
            Liste des variables catégorielles ordinales utilisées pour la
            construction du sous-indicateur de santé physique.

        health_bin_vars : list
            Liste des variables binaires utilisées pour la construction du
            sous-indicateur de santé physique.

        NSCH_eco_cat_vars : list
            Liste des variables catégorielles ordinales issues de l’enquête
            NSCH utilisées pour la dimension micro-économique.

        NSCH_eco_bin_vars : list
            Liste des variables binaires issues de l’enquête NSCH utilisées
            pour la dimension micro-économique.

        state_eco_vars_dict : dict
            Dictionnaire associant à chaque année la liste des variables
            macro-économiques utilisées dans la construction de l'indicateur
            économique.

    Returns:
        pandas.DataFrame
            DataFrame indexé par le code FIPS des États (FIPSST) contenant :
            - l'ensemble des sous-indicateurs thématiques par année,
            - l'indicateur global de santé des enfants
            ("indicator_global_health_<year>") pour chaque année analysée.
    """
    indicators_dfs = []
    for year in years:
        mental, health, eco = over_all_indicators_year(year, df_eco, dfs, groups,
                                                       mental_category_vars, mental_bin_vars,
                                                       health_category_vars, health_bin_vars,
                                                       NSCH_eco_cat_vars, NSCH_eco_bin_vars,
                                                       state_eco_vars_dict)
        indicators_dfs.extend([mental, health, eco])

    indicators_dfs = reduce(lambda left, right: left.join(right, how="inner"), indicators_dfs)
    for year in years:
        indicators_dfs[f"indicator_global_health_{year}"] = (
             indicators_dfs[f"sub_indicator_mental_{year}"] *
             indicators_dfs[f"sub_indicator_health_{year}"] *
             indicators_dfs[f"sub_indicator_eco_{year}"])**(1/3)

    return indicators_dfs


def comparison_new_indicator(annual_report, df_global_indicator, df_eco):
    """
    """
    measures_to_keep = [
        "Social and Economic Factors", "Behaviors",
        "Clinical Care", "Health Outcomes", "Physical Environment"
    ]

    weight_dict = {
        "Social and Economic Factors": 0.3,
        "Physical Environment": 0.1,
        "Clinical Care": 0.15,
        "Behaviors": 0.2,
        "Health Outcomes": 0.25
    }

    geo_fips_clean = (
                        df_eco["GeoFIPS"]
                        .str.replace('"', '')
                        .str.strip()
                        .str[:-3]
                        .astype(str)
                        .str.lstrip('0')
    )

    state_to_fips = dict(zip(df_eco["STUSPS"], geo_fips_clean))

    # ---------------------------
    # Filtrage et sélection des colonnes
    # ---------------------------
    df = annual_report[annual_report["Measure"].isin(measures_to_keep)][["Measure", "State",
                                                                         "Score"]].copy()

    # ---------------------------
    # Ajout des poids
    # ---------------------------
    df["Weight"] = df["Measure"].map(weight_dict)

    # ---------------------------
    # Calcul de la moyenne pondérée globale par État
    # ---------------------------
    df["global_indicator_UHF"] = (df["Score"] * df["Weight"]) \
        .groupby(df["State"]).transform('sum') / df.groupby("State")["Weight"].transform('sum')

    # ---------------------------
    # Étape 4 : ajout du code FIPS
    # ---------------------------
    df["FIPSST"] = df["State"].map(state_to_fips).astype(str)
    df_global_indicator.index = df_global_indicator.index.astype(str)

    # ---------------------------
    # Étape 5 : garder 1 ligne par État pour fusionner
    # ---------------------------
    df_state = df.groupby("FIPSST", as_index=False)["global_indicator_UHF"].first()

    # ---------------------------
    # Étape 6 : merge avec df_global_indicator
    # ---------------------------
    df_final = df_state.set_index("FIPSST").join(
        df_global_indicator[["indicator_global_health_2024", "sub_indicator_health_2024",
                             "sub_indicator_mental_2024", "sub_indicator_eco_2024"]],
        how="inner"
    ).reset_index()

    # Sélection des colonnes finales
    df_final = df_final[["FIPSST",
                         "indicator_global_health_2024",
                         "global_indicator_UHF",
                         "sub_indicator_health_2024",
                         "sub_indicator_mental_2024",
                         "sub_indicator_eco_2024"]]

    return df_final
