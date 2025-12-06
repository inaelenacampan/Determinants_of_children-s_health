# Librairies

import pandas as pd
import geopandas as gpd
from sklearn.impute import KNNImputer

# Lecture des données


def lecture_fichier(fs, chemin_lecture, chemin_ecriture):
    fs.get(chemin_lecture, chemin_ecriture)


def lecture_fichier_sas(fs, chemin_lecture, chemin_ecriture):
    for year in ["2024", "2023", "2022", "2021"]:
        lecture_fichier(fs, f"{chemin_lecture}nsch_{year}e_topical.sas7bdat",
                        f"{chemin_ecriture}nsch_{year}e_topical.sas7bdat")
    dfs = {}

    for year in ["2024", "2023", "2022", "2021"]:
        dfs[year] = pd.read_sas(f"{chemin_ecriture}nsch_{year}e_topical.sas7bdat",
                                format='sas7bdat', encoding='latin1')
    return dfs


def lecture_fichier_csv(fs, chemin_lecture, chemin_ecriture):
    lecture_fichier(fs, chemin_lecture, chemin_ecriture)
    guide = pd.read_csv(chemin_ecriture, index_col=False)
    return guide


def lecture_fichier_shapefile(fs, chemin_lecture, chemin_ecriture):
    for ext in ["shp", "shx", "dbf", "prj"]:
        lecture_fichier(fs, f"{chemin_lecture}cb_2024_us_state_20m.{ext}",
                            f"{chemin_ecriture}cb_2024_us_state_20m.{ext}")
    gdf = gpd.read_file(f"{chemin_ecriture}cb_2024_us_state_20m.shp")
    return gdf


def write_questions(variables, guide):
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
    # Ce code prend environ 2 minutes à tourner en vue du choix de voisins = 3
    # (la version avec un seul voisin est plus rapide)

    # Cette variable n'est pas convertible telle que dans un type float => recodage
    df["FORMTYPE"] = df["FORMTYPE"].str.replace("T", "").astype(float)
    # sauvegarde de l'état des variables avant l'imputation
    missing_mask = df.isna()

    # pour imputer le dataset, un type float est obligatoire
    df_float = df.astype(float)

    # Imputation avec la méthode de k plus proches voisins
    imputer = KNNImputer(n_neighbors=3, weights="uniform")
    imputed_array = imputer.fit_transform(df_float)

    # Remettre dans un DataFrame
    df_final = pd.DataFrame(imputed_array, columns=df.columns)

    # recast puisque les variables sont catégorielles, on arrondit
    df_final = df_final.round().astype(int)
    df_final["FORMTYPE"] = "T" + df_final["FORMTYPE"].astype(int).astype(str)

    # On sait quelles valeurs ont été imputées dans le dataframe final
    for col in df.columns:
        df_final[col + "_imputed"] = missing_mask[col]

    return df_final


def impute_values_over_dataset(years, dfs):
    # execution de l'imputation sur l'ensemble des bases de données
    dfs_final = {}
    for year in years:
        df = dfs[year]
        df_final = impute_values(year, df)
        dfs_final[year] = df_final
    return dfs_final
