#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INFÉRENCE V2 - VERSION GRAPHIQUES PROPRES
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
from collections import Counter
from scipy.stats import entropy as shannon_entropy

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

QUASI_IDENTIFIANTS = {
    'Démographique': ['age', 'sexe'],
    'Démo+Temps': ['age', 'sexe', 'entree_date_ym', 'sortie_date_ym'],
    'Étendu': ['age', 'sexe', 'entree_date_ymd', 'specialite', 'chirurgie'],
    'Complet': ['age', 'sexe', 'entree_date_ymd', 'specialite', 'chirurgie',
                'diabete', 'insuffisance_renale', 'demence'],
}

ATTRIBUTS_SECRETS = ['liste_diag', 'liste_acte']


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


def extraire_codes(liste_codes_str):
    if pd.isna(liste_codes_str) or liste_codes_str == '':
        return []
    return [code.strip() for code in str(liste_codes_str).split(';') if code.strip()]


def codes_unanimes(liste_de_listes):
    if not liste_de_listes or len(liste_de_listes) == 0:
        return []
    sets_codes = [set(codes) for codes in liste_de_listes if codes]
    if not sets_codes:
        return []
    codes_communs = sets_codes[0]
    for s in sets_codes[1:]:
        codes_communs = codes_communs.intersection(s)
    return sorted(list(codes_communs))


def calculer_entropie_codes(liste_de_listes):
    tous_codes = []
    for codes in liste_de_listes:
        tous_codes.extend(codes)
    if not tous_codes:
        return 0.0
    freq = Counter(tous_codes)
    total = len(tous_codes)
    probs = [count / total for count in freq.values()]
    return shannon_entropy(probs, base=2)


def attaque_inference_codes(connaissances, cible, quasi_ids, attribut_secret):
    vars_ok = [v for v in quasi_ids
               if v in connaissances.columns and v in cible.columns]
    
    if attribut_secret not in cible.columns:
        return None
    
    cible_avec_codes = cible.copy()
    cible_avec_codes['codes_extraits'] = cible_avec_codes[attribut_secret].apply(extraire_codes)
    
    grouped = cible_avec_codes.groupby(vars_ok)['codes_extraits'].apply(list).reset_index()
    
    stats_groupes = []
    for _, row in grouped.iterrows():
        liste_codes = row['codes_extraits']
        unanimes = codes_unanimes(liste_codes)
        entropie = calculer_entropie_codes(liste_codes)
        
        stats_groupes.append({
            **{v: row[v] for v in vars_ok},
            'nb_codes_unanimes': len(unanimes),
            'entropie': entropie,
        })
    
    stats_df = pd.DataFrame(stats_groupes)
    merged = connaissances[vars_ok].merge(stats_df, on=vars_ok, how='left')
    
    n_total = len(merged)
    n_inference_unanime = (merged['nb_codes_unanimes'] > 0).sum()
    entropie_moy = merged['entropie'].mean()
    
    return {
        'n_total': n_total,
        'n_inference_unanime': n_inference_unanime,
        'taux_inference_unanime': n_inference_unanime / n_total * 100,
        'entropie_moyenne': entropie_moy if not np.isnan(entropie_moy) else 0,
        'nb_vars': len(vars_ok),
    }


def extraire_niveau_bruit(nom_fichier):
    match = re.search(r'_(\d+)\.txt', nom_fichier)
    return int(match.group(1)) if match else None


def charger_fichiers_chemins(sous_dossier):
    fichiers = {}
    pattern = os.path.join(sous_dossier, '*.txt')
    for chemin in sorted(glob.glob(pattern)):
        nom = os.path.basename(chemin)
        niveau = extraire_niveau_bruit(nom)
        if niveau is not None:
            fichiers[niveau] = chemin
    if fichiers:
        print(f"📂 Fichiers trouvés : {len(fichiers)}")
    return fichiers


def plot_inference_codes_unanime(fichiers_chemins, connaissances, output_dir, type_fichier):
    print(f"\n📊 Inférence unanime ({type_fichier})")
    
    premier_chemin = list(fichiers_chemins.values())[0]
    df_test = pd.read_csv(premier_chemin, sep='\t')
    attributs = [a for a in ATTRIBUTS_SECRETS if a in df_test.columns]
    del df_test
    
    if not attributs:
        print("   ⚠️ Aucun attribut secret trouvé")
        return
    
    niveaux = sorted(fichiers_chemins.keys())
    niveaux_affiches = thin_out_levels(niveaux, 8)
    
    resultats = {}
    for idx, bruit in enumerate(niveaux_affiches):
        print(f"   Traitement niveau {bruit}% ({idx+1}/{len(niveaux_affiches)})...", end=' ')
        cible = pd.read_csv(fichiers_chemins[bruit], sep='\t')
        
        resultats[bruit] = {}
        for scenario, qi in QUASI_IDENTIFIANTS.items():
            resultats[bruit][scenario] = {}
            for attr in attributs:
                res = attaque_inference_codes(connaissances, cible, qi, attr)
                resultats[bruit][scenario][attr] = res
        del cible
        print("✓")
    
    fig, axes = plt.subplots(1, len(attributs), figsize=(7 * len(attributs), 6), sharey=True)
    if len(attributs) == 1:
        axes = [axes]
    
    colors = plt.cm.RdYlGn_r(np.linspace(0.1, 0.9, len(niveaux_affiches)))
    
    for ax, attribut in zip(axes, attributs):
        for idx, bruit in enumerate(niveaux_affiches):
            taux_list, nb_vars_list = [], []
            for scenario in QUASI_IDENTIFIANTS.keys():
                if (scenario in resultats[bruit] and attribut in resultats[bruit][scenario] and
                    resultats[bruit][scenario][attribut]):
                    res = resultats[bruit][scenario][attribut]
                    taux_list.append(res['taux_inference_unanime'])
                    nb_vars_list.append(res['nb_vars'])
            if taux_list:
                ax.plot(nb_vars_list, taux_list, marker='o', lw=2.5, ms=7,
                       label=f'Bruit {bruit}%', color=colors[idx])
        ax.set_title(f'{attribut}')
        ax.set_xlabel('Nb variables connues')
        ax.set_ylim(0, 100)
    
    axes[0].set_ylabel("Taux d'inférence unanime (%)")
    axes[0].legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    
    plt.tight_layout()
    out = os.path.join(output_dir, f'inference_codes_unanime_{type_fichier}.png')
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✓ Sauvegardé: {out}")


def plot_entropie_codes(fichiers_chemins, connaissances, output_dir, type_fichier):
    print(f"\n📊 Entropie ({type_fichier})")
    
    premier_chemin = list(fichiers_chemins.values())[0]
    df_test = pd.read_csv(premier_chemin, sep='\t')
    attributs = [a for a in ATTRIBUTS_SECRETS if a in df_test.columns]
    del df_test
    
    if not attributs:
        return
    
    scenario_ref = 'Complet'
    niveaux_affiches = thin_out_levels(sorted(fichiers_chemins.keys()), 8)
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    for attribut in attributs:
        entropies = []
        for bruit in niveaux_affiches:
            cible = pd.read_csv(fichiers_chemins[bruit], sep='\t')
            res = attaque_inference_codes(connaissances, cible, QUASI_IDENTIFIANTS[scenario_ref], attribut)
            entropies.append(res['entropie_moyenne'] if res else np.nan)
            del cible
        ax.plot(niveaux_affiches, entropies, marker='o', lw=2.5, ms=7, label=attribut)
    
    ax.set_xlabel('Niveau de bruit (%)')
    ax.set_ylabel('Entropie moyenne')
    ax.set_title(f'Entropie des codes - {type_fichier}')
    ax.legend()
    
    plt.tight_layout()
    out = os.path.join(output_dir, f'inference_codes_entropie_{type_fichier}.png')
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✓ Sauvegardé: {out}")


def main():
    print("\n" + "="*70)
    print("  ANALYSE INFÉRENCE - VERSION GRAPHIQUES PROPRES")
    print("="*70)
    
    base_dir = '.'
    data_dir = os.path.join(base_dir, 'data')
    output_dir = os.path.join(base_dir, 'resultats_inference')
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n📂 Chargement des connaissances...")
    connaissances_path = os.path.join(data_dir, 'connaissances_externes.txt')
    if not os.path.exists(connaissances_path):
        print(f"❌ Fichier non trouvé : {connaissances_path}")
        return
    
    connaissances = pd.read_csv(connaissances_path, sep='\t')
    print(f"  ✓ {len(connaissances)} séjours")
    
    out_direct_dir = os.path.join(data_dir, 'out_direct')
    out_sample_dir = os.path.join(data_dir, 'out_sample')
    
    fichiers_direct = charger_fichiers_chemins(out_direct_dir) if os.path.exists(out_direct_dir) else {}
    fichiers_sample = charger_fichiers_chemins(out_sample_dir) if os.path.exists(out_sample_dir) else {}
    
    if not fichiers_direct and not fichiers_sample:
        print("❌ Aucun fichier trouvé")
        return
    
    if fichiers_direct:
        print("\n" + "─"*70)
        print("  OUT_DIRECT")
        plot_inference_codes_unanime(fichiers_direct, connaissances, output_dir, 'out_direct')
        plot_entropie_codes(fichiers_direct, connaissances, output_dir, 'out_direct')
    
    if fichiers_sample:
        print("\n" + "─"*70)
        print("  OUT_SAMPLE")
        plot_inference_codes_unanime(fichiers_sample, connaissances, output_dir, 'out_sample')
        plot_entropie_codes(fichiers_sample, connaissances, output_dir, 'out_sample')
    
    print("\n✅ Analyse terminée.")


if __name__ == "__main__":
    main()