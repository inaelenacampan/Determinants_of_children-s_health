import prince
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


def mca_analysis(year, dfs, drop_columns):
    df = dfs[year]
    df_mca = df.drop(columns=[col for col in drop_columns])
    df_mca = df_mca.drop(columns=[col for col in df_mca.columns if 'imputed' in col])

    mca = prince.MCA(n_components=2).fit(df_mca)
    return df_mca, mca


def mca_plot_individuals(df_mca, mca):
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


def mca_plot_categories(df_mca, mca, seuil):

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
