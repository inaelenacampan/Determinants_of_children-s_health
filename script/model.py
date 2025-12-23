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
    """
    return (x * w).sum() / w.sum()


def scale_transformation(year, dfs, variables, cat_variables, bin_variables, groups, theme):
    """
    -- add legend
    """
    # extract dataframe
    df = dfs[year]

    all_variables = list(set(variables) | set(groups))

    df_theme = df[all_variables].copy()

    df_theme[cat_variables] = 6 - df_theme[cat_variables]

    if theme == "micro_eco":
        for var in bin_variables:
            df_theme[var] = abs(df_theme[var] - 2)
    else:
        for var in bin_variables:
            df_theme[var] = df_theme[var] - 1

    return df_theme


def state_indicator(df_theme, variables, theme, year, minimum, maximum):
    """
    -- add legend
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
    ---- to be defined
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
    --- to be defined
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
    --- to be defined
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
    ----- to be defined
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
