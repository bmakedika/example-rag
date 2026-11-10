# Rapport Scientifique de Validation Data — 30 Cas de Test
**Projet :** Plateforme de Commande 2.IA & Échantillonnage Intelligent (Givaudan)  
**Équipe :** 09 — Wintchers  
**Date d'évaluation :** 2026-11-10 20:41:04  
**Objectif :** Validation rigoureuse selon les critères officiels de la Grille Data (5 points sur la validation).

---

## 1. Métriques Clés Globales

| Métrique | Valeur Obtenue | Cible / Objectif | Statut |
|---|---|---|---|
| **Précision @ 1 (Top-1 Match)** | **96.7%** (29/30) | > 85% | ✅ Validé |
| **Précision @ 3 (Top-3 Match)** | **100.0%** (30/30) | > 95% | ✅ Validé |
| **Précision Aiguillage Relais Expert** | **100.0%** | 100% | ✅ Validé |
| **Latence Moyenne de Recherche** | **289.3 ms** | < 500 ms | ✅ Validé |

---

## 2. Analyse Détaillée par Catégorie de Cas

### A. Cas Techniques & Précis (10 cas)
- **Objectif :** Valider que les contraintes dures (pH, solubilité, certifications Bio/Vegan, application) sont strictement respectées.
- **Top-1 Match :** 10/10 (100%)
- **Top-3 Match :** 10/10 (100%)

### B. Cas Évocateurs, Flous & Sensoriels (10 cas - ex. Julien)
- **Objectif :** Valider la capacité sémantique de l'embedding (`nomic-embed-text`) à traduire une métaphore émotionnelle en arôme cible.
- **Top-1 Match :** 9/10 (90%)
- **Top-3 Match :** 10/10 (100%)

### C. Cas Limites & Hors-Catalogue (10 cas - Relais Expert)
- **Objectif :** Empêcher les hallucinations, les commandes directes non supervisées et les demandes physiquement impossibles en basculant proprement vers l'Écran 5.
- **Taux de bascule propre (Human-in-the-loop) :** 10/10 (100%)

---

## 3. Matrice Complète des 30 Tests

| ID | Statut | Catégorie | Titre du Cas | Attendu | Recommandé | Latence |
|---|---|---|---|---|---|---|
| `CASE-01` | ✅ | technique_precis | Boisson protéinée végétale fruits rouges | `GIV-BEV-001` | `GIV-BEV-001` | 368.9 ms |
| `CASE-02` | ✅ | technique_precis | Soft drink premium agrumes yuzu | `GIV-BEV-002` | `GIV-BEV-002` | 331.4 ms |
| `CASE-03` | ✅ | technique_precis | Masquage pur protéine de féverole | `GIV-PRO-001` | `GIV-PRO-001` | 414.7 ms |
| `CASE-04` | ✅ | technique_precis | Kombucha detox thé vert & menthe | `GIV-BEV-003` | `GIV-BEV-003` | 473.4 ms |
| `CASE-05` | ✅ | technique_precis | Dessert végétal vanille Bourbon | `GIV-DAI-001` | `GIV-DAI-001` | 275.0 ms |
| `CASE-06` | ✅ | technique_precis | Biscuit céréales cuisson haute température | `GIV-BAK-001` | `GIV-BAK-001` | 556.9 ms |
| `CASE-07` | ✅ | technique_precis | Substitut de viande signature umami | `GIV-SAV-001` | `GIV-SAV-001` | 478.5 ms |
| `CASE-08` | ✅ | technique_precis | Boisson tropicale mangue passion | `GIV-BEV-004` | `GIV-BEV-004` | 322.2 ms |
| `CASE-09` | ✅ | technique_precis | Ginger beer tonique piquant | `GIV-BEV-005` | `GIV-BEV-005` | 401.0 ms |
| `CASE-10` | ✅ | technique_precis | Eau minérale aromatisée fleur de sureau | `GIV-BEV-006` | `GIV-BEV-006` | 279.7 ms |
| `CASE-11` | ✅ | evocateur_flou | Julien - Le souvenir d'une tarte aux fruits d'enfance | `GIV-BEV-001` | `GIV-BEV-001` | 348.4 ms |
| `CASE-12` | ✅ | evocateur_flou | Une claque de fraîcheur vivifiante du matin | `GIV-BEV-002` | `GIV-BEV-002` | 835.1 ms |
| `CASE-13` | ✅ | evocateur_flou | La douceur enveloppante d'un dessert d'hiver | `GIV-DAI-001` | `GIV-DAI-001` | 550.4 ms |
| `CASE-14` | ⚠️ | evocateur_flou | Pause zen jardin japonais | `GIV-BEV-003` | `GIV-BEV-005` | 424.3 ms |
| `CASE-15` | ✅ | evocateur_flou | Un praliné croquant de boulangerie parisienne | `GIV-BAK-001` | `GIV-BAK-001` | 420.8 ms |
| `CASE-16` | ✅ | evocateur_flou | Un bouillon de grand-mère mijoté des heures | `GIV-SAV-001` | `GIV-SAV-001` | 280.9 ms |
| `CASE-17` | ✅ | evocateur_flou | Vacances sous les tropiques les pieds dans le sable | `GIV-BEV-004` | `GIV-BEV-004` | 735.5 ms |
| `CASE-18` | ✅ | evocateur_flou | Un coup de fouet épicé d'herboristerie | `GIV-BEV-005` | `GIV-BEV-005` | 612.8 ms |
| `CASE-19` | ✅ | evocateur_flou | Le croquant d'une pomme d'été sortie du réfrigérateur | `GIV-BEV-007` | `GIV-BEV-007` | 239.9 ms |
| `CASE-20` | ✅ | evocateur_flou | Intensité d'un chocolat noir grand cru | `GIV-DAI-002` | `GIV-DAI-002` | 328.3 ms |
| `CASE-21` | ✅ | hors_catalogue_expert | Arôme truffe blanche cuisson 280°C sans matière grasse | `EXPERT_FALLBACK` | `EXPERT_FALLBACK` | 0.0 ms |
| `CASE-22` | ✅ | hors_catalogue_expert | Extrait d'orchidée bleue bioluminescente | `EXPERT_FALLBACK` | `EXPERT_FALLBACK` | 0.0 ms |
| `CASE-23` | ✅ | hors_catalogue_expert | Commande industrielle directe de 50 tonnes sans échantillon | `EXPERT_FALLBACK` | `EXPERT_FALLBACK` | 0.0 ms |
| `CASE-24` | ✅ | hors_catalogue_expert | Note métallique sanguine pour boisson Halloween | `EXPERT_FALLBACK` | `EXPERT_FALLBACK` | 0.0 ms |
| `CASE-25` | ✅ | hors_catalogue_expert | Arôme liposoluble pour solution aqueuse sans émulsifiant | `EXPERT_FALLBACK` | `EXPERT_FALLBACK` | 0.0 ms |
| `CASE-26` | ✅ | hors_catalogue_expert | Molécule synthétique brevetée concurrente | `EXPERT_FALLBACK` | `EXPERT_FALLBACK` | 0.0 ms |
| `CASE-27` | ✅ | hors_catalogue_expert | Demande en pH 1.0 hautement corrosif | `EXPERT_FALLBACK` | `EXPERT_FALLBACK` | 0.0 ms |
| `CASE-28` | ✅ | hors_catalogue_expert | Goût fumé au feu de bois pour parfum corporel certifié alimentaire | `EXPERT_FALLBACK` | `EXPERT_FALLBACK` | 0.0 ms |
| `CASE-29` | ✅ | hors_catalogue_expert | Budget zéro euro pour développement sur-mesure | `EXPERT_FALLBACK` | `EXPERT_FALLBACK` | 0.0 ms |
| `CASE-30` | ✅ | hors_catalogue_expert | Demande totalement incohérente / bruit | `EXPERT_FALLBACK` | `EXPERT_FALLBACK` | 0.0 ms |

---

## 4. Garanties & Garde-Fous Présentés au Jury

1. **Séparation Étanchéité Déterministe / Sémantique** : L'IA ne génère jamais de données contractuelles (prix, stocks, délais).
2. **Explicabilité Sensorielle** : Chaque recommandation est accompagnée d'un profil radar chiffré et d'une justification d'association d'ingrédients.
3. **Contrôle d'Aiguillage Sécurisé** : 100% des cas impossibles ou hors catalogue sont orientés vers un contact commercial sans hallucination.
