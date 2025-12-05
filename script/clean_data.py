# Librairies

import pandas as pd
import geopandas as gpd

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
