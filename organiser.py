#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ORGANISATION DES FICHIERS - Projet M2 MIAS
===========================================
Crée une structure de dossiers claire et déplace :
  - les fichiers de données (.txt)
  - les figures produites (.png)

Structure cible :
  projet/
  ├── data/
  │   ├── connaissances_externes.txt
  │   ├── out_direct/
  │   │   ├── out_direct_0.txt
  │   │   └── out_direct_5.txt
  │   └── out_sample/
  │       ├── out_sample_0.txt
  │       └── out_sample_5.txt
  └── resultats/
      ├── individualisation/
      │   ├── out_direct/
      │   └── out_sample/
      ├── inference/
      │   ├── out_direct/
      │   └── out_sample/
      └── correlation/
          ├── out_direct/
          └── out_sample/
"""

import os
import shutil
import glob

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
# Répertoire racine du projet (là où vous lancez le script)
RACINE = '.'

# Dossiers de destination
STRUCTURE = {
    'data/connaissances': 'data',
    'data/out_direct':    'data/out_direct',
    'data/out_sample':    'data/out_sample',
    'resultats/individualisation/out_direct':  'resultats/individualisation/out_direct',
    'resultats/individualisation/out_sample':  'resultats/individualisation/out_sample',
    'resultats/individualisation/comparatif':  'resultats/individualisation/comparatif',
    'resultats/inference/out_direct':          'resultats/inference/out_direct',
    'resultats/inference/out_sample':          'resultats/inference/out_sample',
    'resultats/inference/comparatif':          'resultats/inference/comparatif',
    'resultats/correlation/out_direct':        'resultats/correlation/out_direct',
    'resultats/correlation/out_sample':        'resultats/correlation/out_sample',
    'resultats/correlation/comparatif':        'resultats/correlation/comparatif',
}


def creer_structure():
    """Crée tous les dossiers nécessaires."""
    print("📁 Création de la structure de dossiers...")
    for dossier in STRUCTURE.values():
        chemin = os.path.join(RACINE, dossier)
        os.makedirs(chemin, exist_ok=True)
        print(f"  ✓ {chemin}")


def deplacer_donnees():
    """Déplace les fichiers .txt de données dans les bons dossiers."""
    print("\n📂 Organisation des fichiers de données...")

    # connaissances_externes
    for f in glob.glob(os.path.join(RACINE, 'connaissances_externes.txt')):
        dest = os.path.join(RACINE, 'data', os.path.basename(f))
        if not os.path.exists(dest):
            shutil.copy2(f, dest)
            print(f"  → {os.path.basename(f)} → data/")
        else:
            print(f"  (déjà présent) {os.path.basename(f)}")

    # out_direct
    for f in glob.glob(os.path.join(RACINE, 'out_direct_*.txt')):
        dest = os.path.join(RACINE, 'data', 'out_direct', os.path.basename(f))
        if not os.path.exists(dest):
            shutil.copy2(f, dest)
            print(f"  → {os.path.basename(f)} → data/out_direct/")
        else:
            print(f"  (déjà présent) {os.path.basename(f)}")

    # out_sample
    for f in glob.glob(os.path.join(RACINE, 'out_sample_*.txt')):
        dest = os.path.join(RACINE, 'data', 'out_sample', os.path.basename(f))
        if not os.path.exists(dest):
            shutil.copy2(f, dest)
            print(f"  → {os.path.basename(f)} → data/out_sample/")
        else:
            print(f"  (déjà présent) {os.path.basename(f)}")


def deplacer_figures():
    """
    Déplace les figures .png produites par les scripts d'analyse.
    Les figures sont identifiées par leur préfixe :
      indiv_*    → individualisation/
      inference_* → inference/
      corr_*     → correlation/
    Et par leur suffixe :
      *out_direct* → .../out_direct/
      *out_sample* → .../out_sample/
      *comparatif* → .../comparatif/
    """
    print("\n🖼️  Organisation des figures...")

    # Chercher dans les dossiers de résultats actuels
    dossiers_source = [
        'resultats_individualisation',
        'resultats_inference',
        'resultats_correlation',
    ]

    for dossier_src in dossiers_source:
        chemin_src = os.path.join(RACINE, dossier_src)
        if not os.path.exists(chemin_src):
            continue

        for f in glob.glob(os.path.join(chemin_src, '*.png')):
            nom = os.path.basename(f)
            dest = _trouver_destination_figure(nom)
            if dest:
                os.makedirs(dest, exist_ok=True)
                chemin_dest = os.path.join(dest, nom)
                if not os.path.exists(chemin_dest):
                    shutil.copy2(f, chemin_dest)
                    print(f"  → {nom}")
                    print(f"     → {dest}/")
                else:
                    print(f"  (déjà présent) {nom}")

    # Chercher aussi dans le répertoire courant
    for f in glob.glob(os.path.join(RACINE, '*.png')):
        nom = os.path.basename(f)
        dest = _trouver_destination_figure(nom)
        if dest:
            os.makedirs(dest, exist_ok=True)
            chemin_dest = os.path.join(dest, nom)
            if not os.path.exists(chemin_dest):
                shutil.copy2(f, chemin_dest)
                print(f"  → {nom} → {dest}/")


def _trouver_destination_figure(nom_fichier):
    """
    Détermine le dossier de destination d'une figure selon son nom.
    Retourne None si le fichier ne correspond à aucune règle.
    """
    nom = nom_fichier.lower()

    # Déterminer le type d'analyse
    if nom.startswith('indiv_'):
        analyse = 'individualisation'
    elif nom.startswith('inference_'):
        analyse = 'inference'
    elif nom.startswith('corr_'):
        analyse = 'correlation'
    else:
        return None

    # Déterminer le sous-dossier
    if 'comparatif' in nom:
        sous_dossier = 'comparatif'
    elif 'out_direct' in nom:
        sous_dossier = 'out_direct'
    elif 'out_sample' in nom or 'sample' in nom:
        sous_dossier = 'out_sample'
    else:
        sous_dossier = 'comparatif'  # par défaut

    return os.path.join(RACINE, 'resultats', analyse, sous_dossier)


def afficher_arborescence():
    """Affiche l'arborescence finale du projet."""
    print("\n📊 Structure finale du projet :")
    print("=" * 50)

    for racine_dir, dossiers, fichiers in os.walk(RACINE):
        # Ignorer les dossiers cachés et __pycache__
        dossiers[:] = [d for d in sorted(dossiers)
                       if not d.startswith('.') and d != '__pycache__'
                       and d not in ('resultats_individualisation',
                                     'resultats_inference',
                                     'resultats_correlation')]

        niveau = racine_dir.replace(RACINE, '').count(os.sep)
        indent = '  ' * niveau
        nom_dossier = os.path.basename(racine_dir) or '.'
        print(f"{indent}📁 {nom_dossier}/")

        sous_indent = '  ' * (niveau + 1)
        for fichier in sorted(fichiers):
            if fichier.endswith(('.txt', '.png', '.py', '.csv')):
                icone = '🖼️ ' if fichier.endswith('.png') else \
                        '📄' if fichier.endswith('.txt') else \
                        '🐍' if fichier.endswith('.py') else '📄'
                print(f"{sous_indent}{icone} {fichier}")


def main():
    print("\n" + "=" * 60)
    print("  ORGANISATION DU PROJET — M2 MIAS")
    print("=" * 60)

    creer_structure()
    deplacer_donnees()
    deplacer_figures()
    afficher_arborescence()

    print("\n✅ Organisation terminée !")
    print("""
💡 Pour relancer les analyses avec la nouvelle structure,
   modifiez data_dir dans chaque script :

   # individualisation.py, inference.py, correlation.py
   data_dir = './data'          # au lieu de '.'
   output_dir = './resultats/individualisation'  # etc.
""")


if __name__ == "__main__":
    main()
