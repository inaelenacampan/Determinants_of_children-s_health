import prince
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Ellipse


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


"""
# brouillon affichage de PIB par état
# idée : utiliser ce code pour la carte finale, quand on aura calculé les indices de santé par état
year = 2024
column  =f"{year}_Real GDP (millions of chained 2017 dollars) 1/"

# convertion du type de la base de données

gdf = gpd.GeoDataFrame(df_eco_geo, geometry='geometry')

# Centrer la carte sur les USA
m = folium.Map([43, -100], zoom_start=4)

# Ajouter une carte choroplèthe
folium.Choropleth(
    geo_data=gdf,
    data=df_eco_geo,
    columns = ["GeoName",column],
    key_on="feature.properties.GeoName",
    fill_opacity=0.3,
    line_weight=2,
    highlight=True,
    fill_color = "viridis"
).add_to(m)

m
"""
