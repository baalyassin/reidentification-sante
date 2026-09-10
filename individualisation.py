#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INDICATEUR D'INDIVIDUALISATION - VERSION GRAPHIQUES PROPRES
============================================================
Auteurs: BAALI Yassin, CANEVAL Gabrielle
Version: Avril 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
import re

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

plt.rcParams.update({
    'figure.figsize': (14, 8),
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'axes.titleweight': 'bold',
    'axes.labelweight': 'bold',
    'legend.fontsize': 10,
    'lines.linewidth': 2.5,
    'lines.markersize': 7,
    'grid.alpha': 0.3,
})

VARS_CONNUES_CROISSANT = [
    ['age10'],
    ['age10', 'sexe'],
    ['age10', 'sexe', 'entree_date_y'],
    ['age5',  'sexe', 'entree_date_y'],
    ['age5',  'sexe', 'entree_date_ym'],
    ['age',   'sexe', 'entree_date_ym'],
    ['age',   'sexe', 'entree_date_ym', 'specialite'],
    ['age',   'sexe', 'entree_date_ymd', 'specialite'],
    ['age',   'sexe', 'entree_date_ymd', 'specialite', 'entree_mode'],
    ['age',   'sexe', 'entree_date_ymd', 'specialite', 'entree_mode', 'sortie_mode'],
]

PROFILS_ATTAQUE = {
    'Démographique seul':  ['age', 'sexe'],
    'Temporel seul':       ['entree_date_ymd', 'sortie_date_ymd'],
    'Médical seul':        ['specialite', 'chirurgie'],
    'Démo + Année':        ['age', 'sexe', 'entree_date_y'],
    'Démo + Mois':         ['age', 'sexe', 'entree_date_ym'],
    'Démo + Jour':         ['age', 'sexe', 'entree_date_ymd'],
    'Démo + Jour + Spé':   ['age', 'sexe', 'entree_date_ymd', 'specialite'],
    'Profil Complet':      ['age', 'sexe', 'entree_date_ymd', 'specialite', 'entree_mode', 'sortie_mode'],
}


def thin_out_levels(niveaux, max_curves=8):
    if len(niveaux) <= max_curves:
        return niveaux
    result = [niveaux[0]]
    middle = niveaux[1:-1]
    step = len(middle) / (max_curves - 2)
    for i in range(1, max_curves - 1):
        idx = int(i * step)
        if idx < len(middle):
            result.append(middle[idx])
    result.append(niveaux[-1])
    return sorted(set(result))


def attaque_individualisation(connaissances, cible, variables):
    vars_ok = [v for v in variables
               if v in connaissances.columns and v in cible.columns]
    if not vars_ok:
        return None

    cible_comptage = (cible[vars_ok + ['id_sejour']]
                      .groupby(vars_ok)
                      .agg(nb_matches=('id_sejour', 'count'),
                           id_sejour_cible=('id_sejour', 'first'))
                      .reset_index())

    merged = connaissances[vars_ok + ['id_sejour']].merge(
        cible_comptage, on=vars_ok, how='left'
    )
    merged['nb_matches'] = merged['nb_matches'].fillna(0).astype(int)

    n_total = len(merged)
    masque_unique = merged['nb_matches'] == 1
    n_reussites = (
        masque_unique &
        (merged['id_sejour'] == merged['id_sejour_cible'])
    ).sum()

    return {
        'n_total': n_total,
        'n_reussites': n_reussites,
        'taux_reidentif': n_reussites / n_total * 100,
        'nb_vars': len(vars_ok),
    }


def extraire_niveau_bruit(nom_fichier):
    match = re.search(r'_(\d+)\.txt', nom_fichier)
    return int(match.group(1)) if match else None


def charger_fichiers(sous_dossier):
    """Charge les fichiers depuis un sous-dossier (out_direct ou out_sample)"""
    fichiers = {}
    pattern = os.path.join(sous_dossier, '*.txt')
    for chemin in sorted(glob.glob(pattern)):
        nom = os.path.basename(chemin)
        niveau = extraire_niveau_bruit(nom)
        if niveau is not None:
            df = pd.read_csv(chemin, sep='\t')
            fichiers[niveau] = df
            print(f"  ✓ {nom}: {len(df)} lignes")
    return fichiers


def plot_courbes_croissantes(connaissances, fichiers_cibles, output_dir, type_fichier):
    print(f"\n── Courbes croissantes ({type_fichier})")
    
    all_results = {}
    for bruit, cible in sorted(fichiers_cibles.items()):
        taux = []
        for variables in VARS_CONNUES_CROISSANT:
            res = attaque_individualisation(connaissances, cible, variables)
            taux.append(res['taux_reidentif'] if res else 0)
        all_results[bruit] = taux
    
    niveaux = sorted(all_results.keys())
    niveaux_affiches = thin_out_levels(niveaux, 8)
    
    fig, ax = plt.subplots(figsize=(14, 8))
    x = range(1, len(VARS_CONNUES_CROISSANT) + 1)
    colors = plt.cm.RdYlGn_r(np.linspace(0.1, 0.9, len(niveaux_affiches)))
    
    for idx, bruit in enumerate(niveaux_affiches):
        ax.plot(x, all_results[bruit], marker='o', linewidth=2.5,
                markersize=7, label=f'Bruit {bruit}%', color=colors[idx])
    
    ax.set_xlabel('Nombre de variables', fontsize=12, fontweight='bold')
    ax.set_ylabel('Taux de réidentification (%)', fontsize=12, fontweight='bold')
    ax.set_title(f'Évolution selon le nombre de variables ({type_fichier})',
                 fontsize=14, fontweight='bold', pad=15)
    ax.axhline(y=20, color='orange', linestyle=':', linewidth=1.5, alpha=0.7, label='Seuil alerte (20%)')
    ax.axhline(y=50, color='red', linestyle=':', linewidth=1.5, alpha=0.7, label='Seuil critique (50%)')
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=10)
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    out = os.path.join(output_dir, f'indiv_S2_croissantes_{type_fichier}.png')
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Sauvegardé: {out}")


def plot_profils_attaque(connaissances, fichiers_cibles, output_dir, type_fichier):
    print(f"\n── Profils d'attaque ({type_fichier})")
    
    resultats = {}
    for bruit, cible in sorted(fichiers_cibles.items()):
        resultats[bruit] = {}
        for nom_profil, vars_profil in PROFILS_ATTAQUE.items():
            res = attaque_individualisation(connaissances, cible, vars_profil)
            resultats[bruit][nom_profil] = res['taux_reidentif'] if res else 0
    
    niveaux = sorted(resultats.keys())
    niveaux_affiches = thin_out_levels(niveaux, 8)
    
    fig, ax = plt.subplots(figsize=(14, 8))
    markers = ['o', 's', '^', 'D', 'v', 'P', '*', 'X']
    
    for idx, nom_profil in enumerate(PROFILS_ATTAQUE.keys()):
        taux_list = [resultats[bruit][nom_profil] for bruit in niveaux_affiches]
        ax.plot(niveaux_affiches, taux_list, marker=markers[idx % len(markers)],
                linewidth=2.5, markersize=7, label=nom_profil)
    
    ax.set_xlabel('Niveau de bruit (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Taux de réidentification (%)', fontsize=12, fontweight='bold')
    ax.set_title(f'Comparaison des profils d\'attaque ({type_fichier})',
                 fontsize=14, fontweight='bold', pad=15)
    ax.axhline(y=20, color='orange', linestyle=':', linewidth=1.5, alpha=0.7, label='Seuil alerte (20%)')
    ax.axhline(y=50, color='red', linestyle=':', linewidth=1.5, alpha=0.7, label='Seuil critique (50%)')
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=10)
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    out = os.path.join(output_dir, f'indiv_S3_profils_{type_fichier}.png')
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Sauvegardé: {out}")


def main():
    print("\n" + "="*70)
    print("  ANALYSE INDIVIDUALISATION - VERSION GRAPHIQUES PROPRES")
    print("="*70)
    
    base_dir = '.'
    data_dir = os.path.join(base_dir, 'data')
    output_dir = os.path.join(base_dir, 'resultats_individualisation')
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n📂 Chargement des données...")
    
    connaissances_path = os.path.join(data_dir, 'connaissances_externes.txt')
    if not os.path.exists(connaissances_path):
        print(f"❌ Fichier non trouvé : {connaissances_path}")
        return
    
    connaissances = pd.read_csv(connaissances_path, sep='\t')
    print(f"  ✓ Connaissances : {len(connaissances)} séjours")
    
    # Charger depuis les sous-dossiers
    out_direct_dir = os.path.join(data_dir, 'out_direct')
    out_sample_dir = os.path.join(data_dir, 'out_sample')
    
    fichiers_direct = charger_fichiers(out_direct_dir) if os.path.exists(out_direct_dir) else {}
    fichiers_sample = charger_fichiers(out_sample_dir) if os.path.exists(out_sample_dir) else {}
    
    if not fichiers_direct and not fichiers_sample:
        print("❌ Aucun fichier trouvé dans data/out_direct/ ou data/out_sample/")
        return
    
    if fichiers_direct:
        print("\n" + "─"*50)
        print("  OUT_DIRECT")
        plot_courbes_croissantes(connaissances, fichiers_direct, output_dir, 'out_direct')
        plot_profils_attaque(connaissances, fichiers_direct, output_dir, 'out_direct')
    
    if fichiers_sample:
        print("\n" + "─"*50)
        print("  OUT_SAMPLE")
        plot_courbes_croissantes(connaissances, fichiers_sample, output_dir, 'out_sample')
        plot_profils_attaque(connaissances, fichiers_sample, output_dir, 'out_sample')
    
    print("\n✅ Analyse individualisation terminée.")
    print(f"   Résultats dans : {output_dir}")


if __name__ == "__main__":
    main()