import prince
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Ellipse
import folium
import geopandas as gpd  # pour la gestion des données géographiques (fichiers .shp)
import branca
import ipywidgets as widgets
from IPython.display import display
from IPython.display import clear_output
from scipy.stats import kendalltau
import pandas as pd


def bar_plot(year, dfs, variable, guide):
    """
    Réaliser un bar plot.

    Args :
        year (str) : années d'intéret
        dfs (dict) : dictionnaire des bases de données
        variable (str) : Le critère de regroupement.
        guide (pd object) : Le guide des variables NSCH.

    Returns : un bar plot
    """

    df = dfs[year]
    ax = sns.countplot(data=df, x=variable)

    # récuperer la signification du codage de la réponse
    responde_str = guide.loc[guide["Variable"] == variable, "Response Code"].iloc[0]
    code_dict = dict(item.split(' = ') for item in responde_str.split('||'))
    question_text = guide.loc[guide["Variable"] == variable, "Question"].iloc[0]

    # eviter l'affichage d'un warning lié au ticks
    ticks = ax.get_xticks()
    old_labels = [label.get_text() for label in ax.get_xticklabels()]

    # on utilise le dictionnaire pour un affichage lisible
    new_labels = [code_dict[name] for name in old_labels]
    ax.set_xticks(ticks)
    ax.set_xticklabels(new_labels)

    # pivoter les labels
    plt.xticks(rotation=45, fontsize=8)
    plt.xlabel("Réponse")
    plt.ylabel("Effectif")
    plt.title(f"Répartition de la variable d'intérêt \n{question_text}", fontsize=8)
    plt.show()


def interactive_barplot(variables, dfs, df_guide):
    """
    Créer un bar plot intéractif.

    Args :
        variables (set) : options de variables qui sont à visualiser
        dfs (dict) : dictionnaire des bases de données
        df_guide (dataframe) : dataframe du guide des variables

    Returns:
        None
    """

    year_selector = widgets.Dropdown(
        options=["2024", "2023", "2022", "2021"],
        description='Année',
        value="2023"
    )

    var_selector = widgets.Dropdown(
        options=list(variables),
        description='Variable:',
        value='BREATHING'
    )

    interactive_plot = widgets.interactive(
        bar_plot,
        variable=var_selector,
        year=year_selector,
        dfs=widgets.fixed(dfs),
        guide=widgets.fixed(df_guide)
    )

    display(interactive_plot)


def mca_analysis(year, dfs, drop_columns):
    """
    Réaliser une ACM.

    Args:
        year (str): L'année du formulaire.
        dfs (dict): Le dictionnaire des bases des formulaires NSCH.
        drop_columns (list) : La liste des colonnes à filtrer.

    Returns:
        df_mca : La base de données adéquate pour réaliser l'ACM.
        mca : Objet mca.
    """
    df = dfs[year]
    df_mca = df.drop(columns=[col for col in drop_columns])
    df_mca = df_mca.drop(columns=[col for col in df_mca.columns if 'imputed' in col])

    mca = prince.MCA(n_components=2).fit(df_mca)
    return df_mca, mca


def mca_plot_individuals(df_mca, mca):
    """
    Visualisation des individus de la base de données dans un plan 2D.

    Args:
        df_mca : La base de données adéquate pour réaliser l'ACM.
        mca : L'objet mca.

    Returns:
        génération d'un plot (pas de return explicite)
    """
    row_coords = mca.row_coordinates(df_mca)

    plt.figure(figsize=(10, 10))

    # Scatter plot
    plt.scatter(
        row_coords[0],
        row_coords[1],
        s=1,        # taille des points
        alpha=0.4,   # transparence pour zones denses
        color='blue',
        label='Individus'
    )

    # Labels et titre
    plt.xlabel('Dimension 0', fontsize=12)
    plt.ylabel('Dimension 1', fontsize=12)
    plt.title('Analyse en Composantes Multiples, Individus', fontsize=14)

    # Pour une grille
    plt.grid()

    plt.legend()
    plt.show()


def mca_plot_individuals_group(df_mca, mca, variable, guide):
    """
    Visualisation des individus selon un critère de regroument.

    Args:
        df_mca : La base de données adéquate pour réaliser l'ACM.
        mca : L'objet mca.
        variable (str) : Le critère de regroupement.
        guide (pd object) : Le guide des variables NSCH.

    Returns:
        génération d'un plot (pas de return explicite)
    """
    row_coords = mca.row_coordinates(df_mca)
    groups = df_mca[variable].unique()
    # Les variables sont catégorielles et la légende se présente sous forme d'un str
    # format : ciffre1 = ... || chiffre2 = ...
    responde_str = guide.loc[guide["Variable"] == variable, "Response Code"].iloc[0]
    code_dict = dict(item.split(' = ') for item in responde_str.split('||'))

    plt.figure(figsize=(10, 10))
    palette = sns.color_palette("tab10", len(groups))

    for i, group in enumerate(groups):
        mask = (df_mca[variable] == group)
        x = row_coords[0][mask]
        y = row_coords[1][mask]
        # Scatter plot par groupe
        label = code_dict.get(str(group), str(group))
        plt.scatter(x, y, s=5, alpha=0.6, color=palette[i], label=label)
        # code adapté depuis internet pour manipuler les ellipses
        # Ellipse pour montrer un regroupement des individus
        # plus d'un individu
        if len(x) > 1:
            cov = np.cov(x, y)
            # calcule les valeurs propres (vals) et vecteurs propres (vecs) d’une matrice symétrique
            vals, vecs = np.linalg.eigh(cov)
            width, height = 2 * np.sqrt(vals) * 2  # facteur 2 pour agrandir ellipse
            angle = np.degrees(np.arctan2(*vecs[:, 0][::-1]))
            ell = Ellipse(xy=(np.mean(x), np.mean(y)),
                          width=width, height=height,
                          angle=angle,
                          color=palette[i], alpha=0.2)
            # GCA = Get Current Axes
            plt.gca().add_patch(ell)

    # Récupération du texte de la question pour le titre
    question_text = guide.loc[guide["Variable"] == variable, "Question"].iloc[0]

    plt.xlabel('Dimension 0', fontsize=12)
    plt.ylabel('Dimension 1', fontsize=12)

    plt.title(f'ACM des individus par groupe: \n{question_text}', fontsize=10)
    plt.grid()

    plt.legend()
    plt.show()


def mca_plot_categories(df_mca, mca, seuil):
    """
    Visualisation des modalités (variables catégorielles) de la base de données dans un plan 2D.

    Args:
        df_mca : La base de données adéquate pour réaliser l'ACM.
        mca : L'objet mca.
        seuil (int) : Pour mieux visualiser le graphique, combien de composantes "principales".

    Returns:
        génération d'une figure avec 2 plot (pas de return explicite)
    """
    # Pour les modalités, le graphique est très dense
    # La longueur de la flèche indique l’importance de cette modalité dans l’espace MCA
    # plus la flèche est longue, plus cette modalité contribue à la variance
    # des premières dimensions.
    column_coords = mca.column_coordinates(df_mca)

    distances = np.sqrt(column_coords[0]**2 + column_coords[1]**2)
    top = distances.sort_values(ascending=False).head(seuil).index
    principales = column_coords.loc[top]
    secondaires = column_coords.drop(top)

    fig, axes = plt.subplots(1, 2, figsize=(24, 12))  # 1 ligne, 2 plots

    # ---------------------------
    # Plot n°1
    # ---------------------------

    ax = axes[0]
    for i, col in enumerate(principales.index):
        x, y = principales.iloc[i, 0], principales.iloc[i, 1]
        ax.arrow(0, 0, x, y, color='red', alpha=0.7, head_width=0.02)
        ax.text(x*1.05, y*1.05, col, color='red', fontsize=10)

    ax.set_xlabel('Dimension 0')
    ax.set_ylabel('Dimension 1')
    ax.set_title('Modalités principales')
    ax.grid()

    # ---------------------------
    # Plot n°2
    # ---------------------------
    ax = axes[1]
    for i, col in enumerate(secondaires.index):
        x, y = secondaires.iloc[i, 0], secondaires.iloc[i, 1]
        ax.arrow(0, 0, x, y, color='red', alpha=0.3, head_width=0.01)
        ax.text(x*1.05, y*1.05, col, color='red', fontsize=8)

    ax.set_xlabel('Dimension 0')
    ax.set_ylabel('Dimension 1')
    ax.set_title('Modalités restantes')
    ax.grid()

    plt.tight_layout()
    plt.show()


def heatmap_generator(df):
    """
    Visualisation de la matrice des corrélations de façon hierarchique.

    Args:
        df : La base de données.

    Returns:
        génération d'un plot (pas de return explicite)
    """
    matrix = df.corr()

    sns.set_theme(style="white")  # style propre

    # Clustermap => Un clustering hiérarchique
    # Il regroupe automatiquement les variables qui se ressemblent le plus.
    # Un réarrangement automatique des lignes et colonnes
    # Pour mettre ensemble les variables ayant un comportement similaire.

    sns.clustermap(
        matrix,
        cmap="coolwarm",
        linewidths=0.3,
        figsize=(12, 10),
        # masquer la valeur de la corrélation
        annot=False,
        fmt=".2f",
        dendrogram_ratio=(0.1, 0.1),  # taille des dendrogrammes - l'arrangement de groupes générés
        cbar_pos=(0.02, 0.8, 0.03, 0.18),  # position de la barre de couleur
        robust=True          # évite que des valeurs extrêmes dominent l'affichage
    )

    plt.suptitle("Clustermap de la matrice de corrélation", fontsize=16, y=1.02)
    plt.show()


def boxplot_image(title, y_label, column):
    """
    Génère une boîte à moustaches (boxplot) pour une variable numérique et un violin plot.

    Args :
        title : str
            Titre du graphique.
        y_label : str
            Libellé de l'axe des ordonnées.
        column : pandas.Series
            Série contenant les valeurs numériques à représenter.

    Returns:
        None
    """
    plt.figure(figsize=(8, 6))

    plt.subplot(1, 2, 1)
    plt.boxplot(column.values, vert=True, showmeans=True)
    plt.title("Boxplot")
    plt.ylabel(y_label)

    plt.subplot(1, 2, 2)
    plt.violinplot(column.values, showmedians=True, showmeans=True)
    plt.title("Violin plot")

    plt.suptitle(title)

    plt.tight_layout()
    plt.show()


def map_united_states(df_indicator, df_geo, year):
    """
    Crée une carte choroplèthe interactive des États-Unis représentant
    un indicateur global de santé des enfants pour une année donnée.

    La carte est générée à l’aide de Folium à partir de données géographiques
    (GeoDataFrame) et d’un DataFrame contenant les indicateurs de santé.
    Chaque État est coloré selon la valeur de l’indicateur, allant du rouge
    (faible niveau de santé) au vert foncé (meilleur niveau de santé).

    Args:
        df_indicator : pandas.DataFrame
            DataFrame contenant l'indicateur de santé par État.
            L'index doit correspondre au code FIPS des États (FIPSST).
            Il doit contenir une colonne nommée :
            "indicator_global_health_<year>".

        df_geo : geopandas.GeoDataFrame
            GeoDataFrame contenant les polygones des États américains.
            Doit inclure les colonnes :
            - "GeoFIPS" : code FIPS sous forme de chaîne
            - "GeoName" : nom de l'État
            - "geometry" : géométrie des États

        year : str
            Année de l'indicateur de santé à afficher sur la carte.

    Returns:
        folium.Map
            Objet Folium représentant la carte interactive des États-Unis,
            avec une légende et des infobulles affichant le nom de l'État
            et la valeur de l'indicateur de santé.

    Références
    ----------
    Tutoriel Folium utilisé :
    https://python-visualization.github.io/folium/latest/user_guide/geojson/geojson_popup_and_tooltip.html
    """

    new_df = df_geo.copy()
    new_df["FIPSST"] = new_df["GeoFIPS"].str.replace('"', '').str.strip().str[:-3].astype(int)

    gdf = gpd.GeoDataFrame(new_df, geometry='geometry')
    df_indicator = df_indicator.rename_axis('FIPSST')

    # Merge pour ajouter l'indicateur dans gdf
    gdf = gdf.merge(df_indicator, on="FIPSST", how="left")

    # Centrer la carte sur les USA
    m = folium.Map([43, -100], zoom_start=4, min_zoom=3, max_zoom=6)

    # Créer une échelle de couleur propre : rouge ---> vert
    colormap = branca.colormap.LinearColormap(
        vmin=gdf[f"indicator_global_health_{year}"].min(),
        vmax=gdf[f"indicator_global_health_{year}"].max(),
        colors=["red", "orange", "lightblue", "green", "darkgreen"],
        caption=f"Indice global de santé (0-1) pour l'année {year}"
    )

    # ajout des polygones et des messages
    folium.GeoJson(
        gdf,
        style_function=lambda feature: {
            'fillColor': colormap(feature['properties'][f'indicator_global_health_{year}']),
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.8,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["GeoName", f"indicator_global_health_{year}"],
            aliases=["État:", "Indice santé :"],
            localize=True
        )
    ).add_to(m)

    # Ajouter la légende du colormap
    colormap.add_to(m)

    return m


def interactive_map(df_indicator, df_geo):
    """
    Affiche une carte interactive des États-Unis permettant de visualiser
    l'évolution d'un indicateur global de santé des enfants selon l'année.

    Cette fonction utilise des widgets ipywidgets pour créer un menu
    déroulant de sélection de l'année. Lorsque l'année change, la carte
    choroplèthe correspondante est automatiquement mise à jour.

    Args:
        df_indicator : pandas.DataFrame
            DataFrame contenant les indicateurs de santé par État et par année.
            L'index doit correspondre au code FIPS des États (FIPSST).
            Les colonnes doivent être nommées sous la forme :
            "indicator_global_health_<year>".

        df_geo : geopandas.GeoDataFrame
            GeoDataFrame contenant les informations géographiques des États
            américains (polygones, noms des États et codes FIPS).

    Returns:
        None
            La fonction ne retourne rien. Elle affiche directement un widget
            interactif et une carte Folium dans le notebook Jupyter.
    """

    years = ["2021", "2022", "2023", "2024"]
    year_selector = widgets.Dropdown(
        options=years,
        value="2024",
        description='Année:',
    )
    output = widgets.Output()

    def update_map(change):
        """
        """
        with output:
            clear_output(wait=True)
            display(map_united_states(df_indicator, df_geo, year=change['new']))

    year_selector.observe(update_map, names='value')
    display(year_selector, output)
    with output:
        display(map_united_states(df_indicator, df_geo, year=year_selector.value))


def kendall_analysis(df_indicator):
    """
    Calcule le taux de Kendall (tau) entre l'indicateur global de santé et
    plusieurs sous-indicateurs pour chaque année, et retourne un DataFrame récapitulatif.

    Args:
        df_indicator : pandas.DataFrame
            DataFrame contenant les colonnes suivantes pour chaque année :
            - indicator_global_health_{year}
            - sub_indicator_eco_{year}
            - sub_indicator_health_{year}
            - sub_indicator_mental_{year}

    Returns:
        pandas.DataFrame
            DataFrame contenant pour chaque sous-indicateur et chaque année :
            - Year : l'année
            - Sub_indicator : le nom du sous-indicateur
            - Kendall_tau : le taux de Kendall entre le sous-indicateur et l'indicateur global
            - p_value : la p-value du test de Kendall
    """

    years = ["2024", "2023", "2022", "2021"]
    sub_indicators = ["sub_indicator_eco", "sub_indicator_health", "sub_indicator_mental"]

    results = []

    for year in years:
        for sub in sub_indicators:
            # Calcul du tau de Kendall et de la p-value pour tester la signification statistique
            df1 = df_indicator[f"indicator_global_health_{year}"].sort_values(ascending=True)
            df_global = df1.index.tolist()

            df2 = df_indicator[f"{sub}_{year}"].sort_values(ascending=True)
            df_sub = df2.index.tolist()

            tau, _ = kendalltau(
                df_global, df_sub
            )

            results.append({
                "Year": year,
                "Sub_indicator": sub,
                "Kendall_tau": tau
            })

    # Retourner un DataFrame
    return pd.DataFrame(results)


def state_rankings(df_indicator, df_geo):
    """
    Génère et sauvegarde une heatmap représentant le classement des États
    américains selon un indicateur global de santé pour plusieurs années.

    La fonction associe les scores de santé contenus dans `df_indicator`
    aux noms des États présents dans `df_geo`, calcule les classements
    annuels (1 = meilleur État), puis affiche une matrice colorée où les
    lignes correspondent aux États et les colonnes aux années. Les États
    sont triés selon leur classement pour l'année la plus récente (2024).

    Le graphique utilise une échelle de couleurs allant du vert (meilleur
    classement) au rouge (moins bon classement), avec les années affichées
    en haut du tableau.

    Args:
        df_indicator : pandas.DataFrame
            Table contenant les indicateurs globaux de santé par État, indexée
            par le code FIPS des États (FIPSST). Les colonnes doivent suivre la
            convention de nommage :
            `indicator_global_health_<année>`.

        df_geo : pandas.DataFrame
            Table de correspondance géographique contenant les informations
            des États. Doit inclure les colonnes :
            - `GeoFIPS` : code FIPS géographique de l'État
            - `GeoName` : nom de l'État

    Returns:
    None
        La fonction affiche le graphique et l'enregistre au format JPG
        dans le dossier `docs/`.
    """

    df = df_indicator.reset_index()
    new_df = df_geo.copy()
    new_df["FIPSST"] = new_df["GeoFIPS"].str.replace('"', '').str.strip().str[:-3].astype(int)
    df = df.merge(
        new_df[['FIPSST', 'GeoName']],
        on='FIPSST',
        how='left'
    )
    df = df.set_index('GeoName')
    years = [2024, 2023, 2023, 2021]
    cols = [f'indicator_global_health_{y}' for y in years]

    df_scores = df[cols]
    df_rank = df_scores.rank(
        axis=0,
        ascending=False,   # Meilleur état - score le plus grand
        method='min'
    )
    # renommer les colonnes
    df_rank.columns = [str(y) for y in years]

    # classement de référence : l'année 2024
    df_rank = df_rank.sort_values(by='2024')

    plt.figure(figsize=(15, 30))
    ax = sns.heatmap(
        df_rank,
        annot=True,
        fmt=".0f",
        cmap="RdYlGn_r",   # échelle : rouge (pire) ---> vert (meilleur)
        cbar_kws={'label': 'Classement'}
    )

    # années affichées en haut du plot

    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')
    ax.set_xlabel("Année")

    plt.title("Classement santé globale par État")
    plt.ylabel("État")

    # afficher la légénde de telle sorte que le vert soit en haut et le rouge en bas
    cbar = ax.collections[0].colorbar
    cbar.ax.invert_yaxis()

    plt.tight_layout()

    # sauvegarde au format jpg ---> inclusion dans le readMe
    plt.savefig(
        "docs/classement_etats_sante.jpg",
        format="jpg",
        dpi=300,
        bbox_inches="tight"
    )

    plt.show()
