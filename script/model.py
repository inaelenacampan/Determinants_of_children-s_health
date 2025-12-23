import pandas as pd


def weighted_mean(x, w):
    """
    Calculer la moyenne pondérée

    Args :
        x : variable numérique
        w : poids
    """
    return (x * w).sum() / w.sum()


def scale_transformation(year, dfs, variables, cat_variables, bin_variables, groups):
    """
    -- add legend
    """
    # extract dataframe
    df = dfs[year]

    all_variables = list(set(variables) | set(groups))

    df_theme = df[all_variables].copy()

    df_theme[cat_variables] = 6 - df_theme[cat_variables]
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
    df_theme = scale_transformation(year, dfs, variables, cat_variables, bin_variables, groups)

    maximum = df_theme[variables].max().sum()/len(df_theme[variables].columns)
    minimum = df_theme[variables].min().sum()/len(df_theme[variables].columns)

    indicator = state_indicator(df_theme, variables, theme, year, minimum, maximum)
    return indicator
