# Librairies

import pandas as pd
import geopandas as gpd
from sklearn.impute import KNNImputer

# Lecture des données


def lecture_fichier(fs, chemin_lecture, chemin_ecriture):
    """
    Lecture depuis l'espace de stockage S3.

    Args:
        fs : abstraction du filesystem
        chemin_lecture (str)
        chemin_ecriture (str)

    Returns:
        rien
    """
    fs.get(chemin_lecture, chemin_ecriture)


def lecture_fichier_sas(fs, chemin_lecture, chemin_ecriture):
    """
    Lecture des fichiers sas.

    Args:
        fs : abstraction du filesystem
        chemin_lecture (str)
        chemin_ecriture (str)

    Returns:
        génération d'un objet dataframe
    """
    for year in ["2024", "2023", "2022", "2021"]:
        lecture_fichier(fs, f"{chemin_lecture}nsch_{year}e_topical.sas7bdat",
                        f"{chemin_ecriture}nsch_{year}e_topical.sas7bdat")
    dfs = {}

    for year in ["2024", "2023", "2022", "2021"]:
        dfs[year] = pd.read_sas(f"{chemin_ecriture}nsch_{year}e_topical.sas7bdat",
                                format='sas7bdat', encoding='latin1')
    return dfs


def lecture_fichier_csv(fs, chemin_lecture, chemin_ecriture):
    """
    Lecture des fichiers csv.

    Args:
        fs : abstraction du filesystem
        chemin_lecture (str)
        chemin_ecriture (str)

    Returns:
        génération d'un objet dataframe
    """
    lecture_fichier(fs, chemin_lecture, chemin_ecriture)
    guide = pd.read_csv(chemin_ecriture, index_col=False)
    return guide


def lecture_fichier_shapefile(fs, chemin_lecture, chemin_ecriture):
    """
    Lecture des fichiers géographiques (.shp, principalement).

    Args:
        fs : abstraction du filesystem
        chemin_lecture (str)
        chemin_ecriture (str)

    Returns:
        génération d'un objet geopandas
    """
    for ext in ["shp", "shx", "dbf", "prj"]:
        lecture_fichier(fs, f"{chemin_lecture}cb_2024_us_state_20m.{ext}",
                            f"{chemin_ecriture}cb_2024_us_state_20m.{ext}")
    gdf = gpd.read_file(f"{chemin_ecriture}cb_2024_us_state_20m.shp")
    return gdf


def write_questions(variables, guide):
    """
    Sauvergarde des questions des variables d'interet.

    Args:
        variables (set) : variables séléctionnées
        guide (dataframe) : guide des variables NSCH

    Returns:
        rien
    """
    count = 1
    with open("data/questions_finales.txt", "w", encoding="utf-8") as f:
        for var in variables:
            q = guide[guide["Variable"] == var]
            for idx, row in q.iterrows():
                if str(row["Question"]) != "nan":
                    f.write(str(count) + ". " + str(row["Question"]) + "\t")
                if str(row["Response Code"]) != "nan":
                    f.write(str(row["Response Code"]) + "\n")
                count = count + 1


def impute_values(year, df):
    """
    Méthode d'imputation des variables manquantes.

    Args:
        year (str) : année du formulaire NSCH.
        df : dataframe sondage.

    Returns:
        génération d'un objet geopandas
    """
    # Ce code prend environ 2 minutes à tourner en vue du choix de voisins = 3
    # (la version avec un seul voisin est plus rapide)

    # Recoder FORMTYPE pour qu'il soit numérique
    df["FORMTYPE"] = df["FORMTYPE"].str.replace("T", "").astype(float)
    # Masque des valeurs manquantes pour toutes les colonnes
    missing_mask = df.isna()

    # Imputation générale pour toutes les variables sauf HEIGHT et WEIGHT ---
    other_cols = df.columns.difference(["HEIGHT", "WEIGHT"])
    df_other = df[other_cols].astype(float)  # conversion en float pour performer l'imputation
    imputer_general = KNNImputer(n_neighbors=3, weights="uniform")
    df_other_imputed_array = imputer_general.fit_transform(df_other)
    df_other_imputed = pd.DataFrame(df_other_imputed_array, columns=other_cols, index=df.index)

    # Imputation de HEIGHT et WEIGHT uniquement pour FORMTYPE != T1
    mask_hw = df["FORMTYPE"] != 1
    df_hw = df.loc[mask_hw, ["HEIGHT", "WEIGHT"]].astype(float)
    imputer_hw = KNNImputer(n_neighbors=3, weights="uniform")
    df_hw_imputed_array = imputer_hw.fit_transform(df_hw)
    df_hw_imputed = pd.DataFrame(df_hw_imputed_array,
                                 columns=["HEIGHT", "WEIGHT"], index=df_hw.index)

    # Remettre les valeurs imputées dans le DataFrame final
    df_final = df.copy()
    df_final[other_cols] = df_other_imputed
    df_final.loc[mask_hw, ["HEIGHT", "WEIGHT"]] = df_hw_imputed

    # Arrondir les colonnes (puisque on est sur des variables principalement catégorielles)
    df_final = df_final.round().astype(int, errors='ignore')
    df_final["FORMTYPE"] = "T" + df_final["FORMTYPE"].astype(int).astype(str)

    # Ajouter les colonnes _imputed pour savoir quelles valeurs ont été imputées
    for col in df.columns:
        df_final[col + "_imputed"] = missing_mask[col]

    return df_final


def impute_values_over_dataset(years, dfs):
    """
    Réalisation de l'amputation sur l'ensemble des bases de données.

    Args:
        years (list) : années des enquetes NSCH
        dfs (dict) : dictionnaire des dataset NSCH

    Returns:
        génération d'un dictionnaire de dataframes
    """
    # execution de l'imputation sur l'ensemble des bases de données
    dfs_final = {}
    for year in years:
        df = dfs[year]
        df_final = impute_values(year, df)
        dfs_final[year] = df_final
    return dfs_final


def write_on_S3(fs, years, dfs_final):
    """
    Ecriture parquet en S3.

    Args:
        fs : abstraction du filesystem
        years (list) : années des enquetes NSCH
        dfs_final (dict) : dictionnaire des dataset NSCH

    Returns:
        rien
    """
    MY_BUCKET = "inacampan"
    FILE_PATH_OUT_S3 = f"{MY_BUCKET}/diffusion/Determinants_of_children-s_health/NSCH/clean_data"

    for year in years:
        path = f"{FILE_PATH_OUT_S3}/{year}.parquet"
        df = dfs_final[year]
        with fs.open(path, 'wb') as file_out:
            df.to_parquet(file_out)


def read_on_S3(fs, years):
    """
    Lecture parquet depuis S3.

    Args:
        fs : abstraction du filesystem
        years (list) : années des enquetes NSCH

    Returns:
        dictionnaire de dataset NSCH
    """
    dfs_final = {}

    MY_BUCKET = "inacampan"
    FILE_PATH_OUT_S3 = f"{MY_BUCKET}/diffusion/Determinants_of_children-s_health/NSCH/clean_data"

    # récuperer les dataframes stockés antérieurement dans le S3

    for year in years:
        path = f"{FILE_PATH_OUT_S3}/{year}.parquet"
        with fs.open(path, 'rb') as file_in:
            df = pd.read_parquet(file_in)
            dfs_final[year] = df

    return dfs_final


def test_imputed(years, dfs_final):
    """
    Tester l'imputation.

    Args:
        years (list) : années des enquetes NSCH
        dfs_final (dict) : dictionnaire des dataset NSCH

    Returns:
        rien
    """
    # tester que l'imputation a été bien effectuée
    # on trie en ordre décroissant le pourcentage de valeurs manquantes
    # on regarde la première valeur
    for year in years:
        df = dfs_final[year]

        # Exclure HEIGHT et WEIGHT du test
        cols_to_check = df.columns.difference(["HEIGHT", "WEIGHT"])
        missing_values = df[cols_to_check].isna().mean().sort_values(ascending=False) * 100
        assert missing_values.iloc[0] == 0.0, f"Erreur: première valeur non-nulle pour {year}"

        mask = df["FORMTYPE"] != "T1"
        for col in ["HEIGHT", "WEIGHT"]:
            missing_pct = df.loc[mask, col].isna().mean() * 100
            assert missing_pct == 0.0, f"Erreur : {col} contient des NA pour {year}"
    print("---------------OK----------------------")


def clean_gpd_dataframe(gdp):
    """
    Nettoyage de la base de données économiques.

    Args:
        gdp (dataframe) : base de données économiques.

    Returns:
        base corrigée
    """
    gdp = gdp.replace({"(NA)": pd.NA})

    # on garde un peu plus d'années en cas de valeurs manquantes pour imputer
    years_to_drop = [str(y) for y in range(1998, 2018)]
    gdp = gdp.drop(columns=[col for col in years_to_drop])

    gdp = gdp.drop(columns=["IndustryClassification"])  # la colonne est vide
    gdp = gdp.iloc[:-4]  # du footnote
    gdp = gdp.drop(columns=["TableName"])  # ne rapporte aucune information

    return gdp


def merge_gdp_on_gdf(gdp, gdf):
    """
    Réaliser la jointure entre les données économiques et les données géographiques.

    Args:
        gdp : base de données économiques.
        gdf : base de données géographiques.

    Returns:
        dataframe obtenu avec la jointure
    """
    # On veut faire la jointure entre la base géographique et la base économique

    # Etape 1 : passage en format wide de la base économique
    years_data = [str(y) for y in range(2018, 2025)]

    gdp['indicator'] = gdp['Description'].str.strip()

    # Pivoter
    wide = gdp.pivot(
        index=["GeoFIPS", "GeoName"],
        columns="indicator",
        values=years_data
    )

    # Changer le nom des colonnes
    wide.columns = [f"{ind}_{year}" for (ind, year) in wide.columns]
    gdp = wide.reset_index()

    # Clé commune :
    gdp["STATEFP"] = gdp["GeoFIPS"].str[2:4]

    # Jointure :
    df_eco_geo = gdp.merge(gdf, how="left")

    return df_eco_geo


def numeric_only(df, prefixes=[str(y) for y in range(2018, 2025)]):
    """
    Nettoyer les types de la base de données économiques.

    Args :
        df : dataframe

    Returns:
        dataframe
    """

    for col in df.columns:
        if any(col.startswith(prefix) for prefix in prefixes):
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def clean_enrichment_datasets(gdp, gdf):
    """
    Regrouper les deux fonctions précédentes.

    Args:
        gdp : base de données économiques.
        gdf : base de données géographiques.

    Returns:
        dataframe obtenu avec la jointure, après un premier nettoyage
    """
    gdp = clean_gpd_dataframe(gdp)
    df = merge_gdp_on_gdf(gdp, gdf)

    # drop la ligne sur les états unis au niveau agrégé
    df = df[df["GeoFIPS"] != ' "00000"']

    df = df.reset_index(drop=True)
    df = numeric_only(df)
    return df
