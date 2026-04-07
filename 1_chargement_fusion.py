# ============================================================
# ÉTAPE 2 : Chargement et Fusion des 3 fichiers
# PFE - Prévision des Charges de Sinistres Auto
# ============================================================

import pandas as pd
import numpy as np
from datetime import date

# ─────────────────────────────────────────────────────────────
# 1. CHARGEMENT DES 3 FICHIERS EXCEL
# ─────────────────────────────────────────────────────────────

print("=" * 60)
print("  ÉTAPE 1 : CHARGEMENT DES FICHIERS")
print("=" * 60)

# Fichier 1 - Sinistres Technisys (2019 - 2023) → ancien système
technisys = pd.read_excel("data/sinistres_technisys.xlsx")
print(f"✅ Technisys chargé     : {technisys.shape[0]} lignes, {technisys.shape[1]} colonnes")

# Fichier 2 - Sinistres SAGA (2024) → nouveau système
saga = pd.read_excel("data/sinistres_saga.xlsx")
print(f"✅ SAGA chargé          : {saga.shape[0]} lignes, {saga.shape[1]} colonnes")

# Fichier 3 - Production cumulée (2019 - 2024) → infos contrat + véhicule
production = pd.read_excel("data/production_cumulee.xlsx")
print(f"✅ Production chargé    : {production.shape[0]} lignes, {production.shape[1]} colonnes")


# ─────────────────────────────────────────────────────────────
# 2. HARMONISATION DES 2 FICHIERS SINISTRES
#    (les rendre compatibles avant de les fusionner)
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("  ÉTAPE 2 : HARMONISATION DES FICHIERS SINISTRES")
print("=" * 60)

# ── 2.1 Calculer Charge Brute dans SAGA (absente dans ce fichier)
# Charge Brute = Montant Règlement + Reserve actuelle - Recours encaissé
saga["Charge Brute"] = (
    saga["Montant Règlement"].fillna(0) +
    saga["Reserve actuelle"].fillna(0) -
    saga["Recours encaissé"].fillna(0)
)
print("✅ Charge Brute calculée pour SAGA")

# ── 2.2 Calculer Age conducteur dans SAGA (absent, mais date naissance présente)
saga["DATE_naissance conducteur"] = pd.to_datetime(
    saga["DATE_naissance conducteur"], errors="coerce"
)
aujourd_hui = pd.Timestamp(date.today())
saga["Age conducteur"] = (
    (aujourd_hui - saga["DATE_naissance conducteur"]).dt.days // 365
)
print("✅ Age conducteur calculé pour SAGA")

# ── 2.3 Uniformiser le nom de la colonne agence
# Technisys → "Cd_Agence" | SAGA → "CODE_AGENCE"
technisys.rename(columns={"Cd_Agence": "CODE_AGENCE"}, inplace=True)
print("✅ Colonne agence uniformisée")

# ── 2.4 Ajouter colonnes manquantes dans Technisys
# Technisys n'a pas le sexe conducteur → on met "Inconnu"
technisys["Sexe CONDUCTEUR"] = "Inconnu"
technisys["SEXE ASSURE"]     = "Inconnu"
print("✅ Colonnes sexe ajoutées dans Technisys")

# ── 2.5 Ajouter colonnes manquantes dans SAGA
# SAGA n'a pas STATUT_OP dans Technisys → on aligne
if "STATUT_OP" not in technisys.columns:
    technisys["STATUT_OP"] = "Inconnu"
if "TYPE_OP" not in technisys.columns:
    technisys["TYPE_OP"] = "Inconnu"
print("✅ Colonnes STATUT_OP / TYPE_OP vérifiées")

# ── 2.6 Garder uniquement les colonnes communes + importantes
colonnes_communes = [
    "Id_contrat",
    "id_sinistre",
    "dt_survenance",
    "dt_ouverture",
    "dt_deb_im",
    "ds_etat_sin",
    "ds_cause",
    "cd_motif",
    "ds_type_sin",
    "cd_garantie",
    "Lib_garantie",
    "cd_reserve",
    "ds_reserve",
    "ds_type_mvt",
    "Reserve d'ouverture",
    "Reserve actuelle",
    "Montant Règlement",
    "Recours encaissé",
    "Charge Brute",
    "Age conducteur",
    "Sexe CONDUCTEUR",
    "CODE_AGENCE",
    "STATUT_OP",
    "TYPE_OP",
]

# Garder seulement les colonnes qui existent dans chaque fichier
technisys_clean = technisys[[c for c in colonnes_communes if c in technisys.columns]].copy()
saga_clean      = saga[[c for c in colonnes_communes if c in saga.columns]].copy()

print(f"\n✅ Technisys après sélection : {technisys_clean.shape[1]} colonnes")
print(f"✅ SAGA après sélection      : {saga_clean.shape[1]} colonnes")


# ─────────────────────────────────────────────────────────────
# 3. EMPILEMENT DES 2 FICHIERS SINISTRES
#    (Technisys 2019-2023 + SAGA 2024 → un seul fichier)
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("  ÉTAPE 3 : EMPILEMENT DES 2 FICHIERS SINISTRES")
print("=" * 60)

sinistres = pd.concat([technisys_clean, saga_clean], ignore_index=True)

print(f"✅ Technisys  : {len(technisys_clean)} lignes (2019-2023)")
print(f"✅ SAGA       : {len(saga_clean)} lignes (2024)")
print(f"✅ Total      : {len(sinistres)} lignes après empilement")


# ─────────────────────────────────────────────────────────────
# 4. JOINTURE AVEC LE FICHIER PRODUCTION CUMULÉE
#    (ajouter infos véhicule + contrat + assuré)
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("  ÉTAPE 4 : JOINTURE AVEC PRODUCTION CUMULÉE")
print("=" * 60)

# Colonnes utiles du fichier production
colonnes_production = [
    "N_POLICE",
    "Age assuré",
    "Sexe",
    "LIEU",
    "PRIME",
    "P01 (Responsabilité civile)",
    "P02 (Dommage tous accident)",
    "P03 (Incendie)",
    "P04 (Vol)",
    "P05 (Bris de glace)",
    "CVE_MARCA",
    "CVE_MODELO",
    "VALEUR VENALE",
    "Segment",
    "ENERGIE",
    "CATEGORIE",
    "PUISSACE FICSALE",
    "NOMBRE_PLACES",
    "Age véhicule",
    "Valeur véhicule neuf",
    "CLASS_VALEUR_VENALE",
    "CLASS_PUISSANCE_FISCALE",
    "CLASS_AGE_VEHICULE",
    "CLASS_AGE_ASSURE",
    "DATE_EFFET_CT",
    "DATE_ECHEANCE_CT",
]

production_clean = production[
    [c for c in colonnes_production if c in production.columns]
].copy()

# Jointure sur Id_contrat (sinistres) ↔ N_POLICE (production)
df = pd.merge(
    sinistres,
    production_clean,
    left_on  = "Id_contrat",
    right_on = "N_POLICE",
    how      = "left"
)

print(f"✅ Après jointure avec Production : {df.shape[0]} lignes, {df.shape[1]} colonnes")


# ─────────────────────────────────────────────────────────────
# 5. FILTRAGE DES SINISTRES FERMÉS
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("  ÉTAPE 5 : FILTRAGE DES SINISTRES FERMÉS")
print("=" * 60)

# Afficher les valeurs uniques pour vérifier
print(f"\nValeurs uniques de ds_etat_sin :")
print(df["ds_etat_sin"].value_counts())

# Filtrer les sinistres fermés
# ⚠️ Si la valeur exacte est différente (ex: "FERME", "Clos"), adapte ici
df_ferme = df[df["ds_etat_sin"].str.lower().str.contains("ferm", na=False)].copy()

print(f"\n✅ Sinistres totaux  : {len(df)}")
print(f"✅ Sinistres fermés  : {len(df_ferme)}")
print(f"✅ Sinistres ouverts : {len(df) - len(df_ferme)}")


# ─────────────────────────────────────────────────────────────
# 6. NETTOYAGE FINAL — Supprimer colonnes inutiles
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("  ÉTAPE 6 : SUPPRESSION COLONNES INUTILES")
print("=" * 60)

# Colonnes à supprimer (identifiants, redondances, data leakage)
colonnes_a_supprimer = [
    "id_sinistre",          # identifiant technique
    "N_POLICE",             # redondant avec Id_contrat
    "Lib_garantie",         # redondant avec cd_garantie
    "Montant Règlement",    # data leakage !
    "Recours encaissé",     # data leakage !
    "Reserve actuelle",     # data leakage !
]

colonnes_existantes = [c for c in colonnes_a_supprimer if c in df_ferme.columns]
df_final = df_ferme.drop(columns=colonnes_existantes)

print(f"✅ Colonnes supprimées : {colonnes_existantes}")
print(f"✅ Dataset final       : {df_final.shape[0]} lignes, {df_final.shape[1]} colonnes")


# ─────────────────────────────────────────────────────────────
# 7. SAUVEGARDE DU DATASET FINAL
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("  ÉTAPE 7 : SAUVEGARDE")
print("=" * 60)

df_final.to_csv("data/dataset_final.csv", index=False)

print(f"✅ Dataset sauvegardé → data/dataset_final.csv")
print(f"   Lignes   : {df_final.shape[0]}")
print(f"   Colonnes : {df_final.shape[1]}")
print(f"\n{'=' * 60}")
print("  ✅ ÉTAPE 2 TERMINÉE — Prêt pour l'EDA !")
print("=" * 60)
