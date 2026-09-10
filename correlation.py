#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORRÉLATION - VERSION GRAPHIQUES PROPRES
=========================================
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

VARS_DISTANCE = {
    '3 vars': ['age', 'sexe', 'entree_date_y'],
    '5 vars': ['age', 'sexe', 'entree_date_ym', 'specialite', 'entree_mode'],
    '7 vars': ['age', 'sexe', 'entree_date_ymd', 'specialite',
                'entree_mode', 'sortie_mode', 'chirurgie'],
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


def attaque_correlation_exacte(connaissances, cible, variables):
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
    n_correles = (merged['nb_matches'] >= 1).sum()
    n_corrects = (
        (merged['nb_matches'] == 1) &
        (merged['id_sejour'] == merged['id_sejour_cible'])
    ).sum()

    return {
        'n_total': n_total,
        'n_correles': n_correles,
        'n_corrects': n_corrects,
        'taux_correlation': n_correles / n_total * 100,
        'precision': n_corrects / n_correles * 100 if n_correles > 0 else 0,
        'nb_vars': len(vars_ok),
    }


def plot_doublons_sample(fichiers_sample, output_dir):
    print(f"\n📊 Doublons out_sample")
    niveaux = sorted(fichiers_sample.keys())
    taux_doublons = []
    max_reps = []

    for bruit in niveaux:
        cible = fichiers_sample[bruit]
        compte = cible['id_sejour'].value_counts()
        n_total = len(cible)
        n_lignes_doublons = compte[compte > 1].sum()
        taux_doublons.append(n_lignes_doublons / n_total * 100)
        max_reps.append(compte.max())

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    ax1.bar(niveaux, taux_doublons, color='steelblue', width=3)
    ax1.set_title('Taux de doublons dans out_sample', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Niveau de bruit (%)')
    ax1.set_ylabel('% de lignes en double')
    ax2.bar(niveaux, max_reps, color='coral', width=3)
    ax2.set_title('Séjour le plus répété', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Niveau de bruit (%)')
    ax2.set_ylabel('Nombre max de répétitions')
    
    plt.tight_layout()
    out = os.path.join(output_dir, 'corr_C2_doublons_sample.png')
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Sauvegardé: {out}")


def extraire_niveau_bruit(nom_fichier):
    match = re.search(r'_(\d+)\.txt', nom_fichier)
    return int(match.group(1)) if match else None


def charger_fichiers(sous_dossier):
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


def plot_correlation_exacte(connaissances, fichiers_cibles, output_dir, type_fichier):
    print(f"\n📊 Corrélation exacte ({type_fichier})")
    
    resultats = {}
    for bruit, cible in sorted(fichiers_cibles.items()):
        resultats[bruit] = {}
        for nom, variables in VARS_DISTANCE.items():
            res = attaque_correlation_exacte(connaissances, cible, variables)
            if res:
                resultats[bruit][nom] = res
    
    niveaux = sorted(resultats.keys())
    niveaux_affiches = thin_out_levels(niveaux, 8)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    for nom in VARS_DISTANCE.keys():
        taux = []
        nb_vars = []
        for bruit in niveaux_affiches:
            if nom in resultats[bruit]:
                taux.append(resultats[bruit][nom]['taux_correlation'])
                nb_vars.append(resultats[bruit][nom]['nb_vars'])
        if taux:
            ax1.plot(nb_vars, taux, marker='o', lw=2.5, ms=7, label=nom)
    
    ax1.set_xlabel('Nombre de variables')
    ax1.set_ylabel('Taux de corrélation (%)')
    ax1.set_title('Corrélation : % de séjours reliables')
    ax1.legend()
    ax1.set_ylim(0, 100)
    
    colors = plt.cm.RdYlGn_r(np.linspace(0.1, 0.9, len(niveaux_affiches)))
    for idx, bruit in enumerate(niveaux_affiches):
        precisions = []
        nb_vars = []
        for nom in VARS_DISTANCE.keys():
            if nom in resultats[bruit]:
                precisions.append(resultats[bruit][nom]['precision'])
                nb_vars.append(resultats[bruit][nom]['nb_vars'])
        if precisions:
            ax2.plot(nb_vars, precisions, marker='s', lw=2.5, ms=7,
                    label=f'Bruit {bruit}%', color=colors[idx])
    
    ax2.set_xlabel('Nombre de variables')
    ax2.set_ylabel('Précision (%)')
    ax2.set_title('Corrélation : % de liaisons correctes')
    ax2.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    ax2.set_ylim(0, 100)
    
    plt.tight_layout()
    out = os.path.join(output_dir, f'corr_C1_exacte_{type_fichier}.png')
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Sauvegardé: {out}")


def plot_comparatif_direct_sample(connaissances, fichiers_direct, fichiers_sample, output_dir):
    print(f"\n📊 Comparatif direct vs sample")
    niveaux = sorted(set(fichiers_direct.keys()) & set(fichiers_sample.keys()))
    niveaux_affiches = thin_out_levels(niveaux, 8)
    nom_ref = '5 vars'
    
    taux_direct, taux_sample = [], []
    for bruit in niveaux_affiches:
        res_d = attaque_correlation_exacte(connaissances, fichiers_direct[bruit], VARS_DISTANCE[nom_ref])
        res_s = attaque_correlation_exacte(connaissances, fichiers_sample[bruit], VARS_DISTANCE[nom_ref])
        if res_d:
            taux_direct.append(res_d['precision'])
        if res_s:
            taux_sample.append(res_s['precision'])
    
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(niveaux_affiches, taux_direct, 'o-', lw=2.5, ms=8, label='out_direct', color='steelblue')
    ax.plot(niveaux_affiches, taux_sample, 's-', lw=2.5, ms=8, label='out_sample', color='coral')
    ax.set_xlabel('Niveau de bruit (%)')
    ax.set_ylabel('Taux de corrélation (%)')
    ax.set_title('Corrélation : out_direct vs out_sample')
    ax.legend()
    ax.set_ylim(0, 100)
    
    plt.tight_layout()
    out = os.path.join(output_dir, 'corr_C3_comparatif.png')
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Sauvegardé: {out}")


def main():
    print("\n" + "="*70)
    print("  ANALYSE CORRÉLATION - VERSION GRAPHIQUES PROPRES")
    print("="*70)
    
    base_dir = '.'
    data_dir = os.path.join(base_dir, 'data')
    output_dir = os.path.join(base_dir, 'resultats_correlation')
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n📂 Chargement des données...")
    
    connaissances_path = os.path.join(data_dir, 'connaissances_externes.txt')
    if not os.path.exists(connaissances_path):
        print(f"❌ Fichier non trouvé : {connaissances_path}")
        return
    
    connaissances = pd.read_csv(connaissances_path, sep='\t')
    print(f"  ✓ Connaissances : {len(connaissances)} séjours")
    
    out_direct_dir = os.path.join(data_dir, 'out_direct')
    out_sample_dir = os.path.join(data_dir, 'out_sample')
    
    fichiers_direct = charger_fichiers(out_direct_dir) if os.path.exists(out_direct_dir) else {}
    fichiers_sample = charger_fichiers(out_sample_dir) if os.path.exists(out_sample_dir) else {}
    
    if not fichiers_direct and not fichiers_sample:
        print("❌ Aucun fichier trouvé")
        return
    
    if fichiers_direct:
        print("\n" + "─"*50)
        print("  OUT_DIRECT")
        plot_correlation_exacte(connaissances, fichiers_direct, output_dir, 'out_direct')
    
    if fichiers_sample:
        print("\n" + "─"*50)
        print("  OUT_SAMPLE")
        plot_correlation_exacte(connaissances, fichiers_sample, output_dir, 'out_sample')
        plot_doublons_sample(fichiers_sample, output_dir)
    
    if fichiers_direct and fichiers_sample:
        plot_comparatif_direct_sample(connaissances, fichiers_direct, fichiers_sample, output_dir)
    
    print("\n✅ Analyse corrélation terminée.")


if __name__ == "__main__":
    main()