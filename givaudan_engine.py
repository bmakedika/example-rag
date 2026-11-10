"""Moteur de recommandation hybride Givaudan (Wintchers - Équipe 09).

Combine :
1. Recherche vectorielle sémantique (Ollama nomic-embed-text + ChromaDB)
2. Filtrage déterministe strict (Application, Certifications, pH, Thermorésistance)
3. Détection des cas limites / hors-catalogue -> Aiguillage vers l'Écran 5 (Relais Expert)
4. Explicabilité sensorielle (Radar de goût & justification technique)
5. Synthèse LLM (Ollama qwen2.5:1.5b) avec prompt Consultant Arômes Givaudan
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import chromadb
import ollama

import config
import rag

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CATALOG_PATH = DATA_DIR / "givaudan_catalog.json"
COLLECTION_NAME = "givaudan_flavors"

# Seuils de confiance
SIMILARITY_THRESHOLD = 0.58  # Similarité cosinus minimale pour considérer un match valide
FALLBACK_EXPERT_ID = "EXPERT_FALLBACK"

SYSTEM_PROMPT_RECOMMENDER = """Tu es un Consultant Expert en Arômes et Solutions Sensorielles chez Givaudan (Taste & Wellbeing).
Ton rôle est de recommander la meilleure référence d'arôme pour le projet d'un client B2B à partir des références trouvées dans le catalogue.

Règles strictes :
1. Réponds UNIQUEMENT sur la base des références du catalogue Givaudan fournies dans le contexte.
2. N'invente AUCUN prix contractuel ni délai ferme : indique que les conditions commerciales et échantillons finaux sont validés par le Key Account Manager.
3. Explique précisément POURQUOI la référence répond au besoin du client (profil gustatif, compatibilité applicative et masquage d'arrière-goût si pertinent).
4. Fournis une recommandation de dosage indicatif.
5. Sois chaleureux, professionnel et concis (style B2B haut de gamme).
"""

SYSTEM_PROMPT_EXPERT_RELAY = """Tu es le système de qualification de briefs chez Givaudan.
La demande du client dépasse le catalogue standard ou présente des contraintes techniques/réglementaires particulières.
Rédige une fiche de transmission claire et professionnelle destinée à l'Aromaticien R&D et au Commercial Givaudan :
- Synthèse du besoin client
- Points de complexité détectés (ex. température extrême, brevet, application spéciale, volume)
- Recommandation d'action pour le commercial (ex. prise de contact, étude faisabilité laboratoire).
"""


class GivaudanHybridEngine:
    def __init__(self, catalog_path: Path = CATALOG_PATH):
        self.catalog_path = catalog_path
        self.catalog: list[dict[str, Any]] = []
        self.catalog_by_id: dict[str, dict[str, Any]] = {}
        self.chroma_client = rag.get_chroma_client()
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine", "embed_model": config.EMBED_MODEL},
        )
        self.load_catalog()

    def load_catalog(self) -> None:
        if self.catalog_path.exists():
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                self.catalog = json.load(f)
            self.catalog_by_id = {item["id"]: item for item in self.catalog}

    def index_catalog(self, force: bool = False) -> int:
        """Indexe le catalogue Givaudan dans ChromaDB."""
        if not self.catalog:
            self.load_catalog()

        if self.collection.count() > 0 and not force:
            return self.collection.count()

        if force and self.collection.count() > 0:
            self.chroma_client.delete_collection(COLLECTION_NAME)
            self.collection = self.chroma_client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine", "embed_model": config.EMBED_MODEL},
            )

        ids = []
        documents = []
        metadatas = []

        for item in self.catalog:
            ids.append(item["id"])
            # Texte enrichi pour maximiser la recherche sémantique
            doc_text = (
                f"{item['name']} - {item['family']} ({item['category']})\n"
                f"Description : {item['description']}\n"
                f"Notes de tête : {item['sensory_notes']['head']}. "
                f"Notes de cœur : {item['sensory_notes']['heart']}. "
                f"Notes de fond : {item['sensory_notes']['base']}.\n"
                f"Applications compatibles : {', '.join(item['application'])}.\n"
                f"Solubilité : {item['solubility']}. Plage pH : {item['ph_min']} à {item['ph_max']}. "
                f"Résistance chaleur : {'Oui' if item['heat_resistant'] else 'Non'}. "
                f"Certifications : {', '.join(item['certifications'])}."
            )
            documents.append(doc_text)
            metadatas.append({
                "id": item["id"],
                "name": item["name"],
                "family": item["family"],
                "category": item["category"],
                "solubility": item["solubility"],
                "ph_min": float(item["ph_min"]),
                "ph_max": float(item["ph_max"]),
                "heat_resistant": bool(item["heat_resistant"]),
                "applications": ",".join(item["application"]),
                "certifications": ",".join(item["certifications"]),
                "dosage_recommended": item["dosage_recommended"],
            })

        embeddings = rag.embed_documents(documents)
        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
        return self.collection.count()

    def detect_edge_case(self, query: str, filters: dict[str, Any] | None = None) -> tuple[bool, str]:
        """Détecte les cas aberrants, hors limites physiques, ou nécessitant impérativement un aromaticien."""
        q_lower = query.lower()
        filters = filters or {}

        # 1. Commande ferme de volume industriel en direct (sécurité métier)
        if any(term in q_lower for term in ["50 000 kg", "50 tonnes", "commande ferme", "débité sur notre compte"]):
            return True, "Sécurité ERP : Les commandes industrielles fermes de volume nécessitent l'accord du Key Account Manager."

        # 2. Demande de molécules captives concurrentes / brevets
        if any(term in q_lower for term in ["firmenich", "brevetée concurrente", "voler la formule", "contrefaçon", "captif"]):
            return True, "Propriété intellectuelle : Givaudan respecte les brevets et propose uniquement des créations propriétaires."

        # 3. Phénomènes physiques ou chimiques impossibles dans le catalogue standard
        if filters.get("ph") is not None and filters["ph"] < 2.0:
            return True, f"Alerte sécurité alimentaire : Un pH de {filters['ph']} est corrosif et hors des normes de formulation standard."

        if "280°c" in q_lower or "300°c" in q_lower or "autoclave à 280" in q_lower:
            return True, "Contrainte thermique extrême : Nécessite une technologie d'encapsulation R&D sur-mesure."

        if any(w in q_lower for w in ["liposoluble", "huileux", "huile"]) and any(w in q_lower for w in ["sans émulsifiant", "eau claire", "sans stabilisant", "sans aucun trouble", "solution aqueuse"]):
            return True, "Incompatibilité physico-chimique (huile/eau sans émulsifiant) : Nécessite une émulsion spéciale développée en laboratoire."

        # 4. Requêtes insolites hors catalogue alimentaire
        if any(term in q_lower for term in ["orchidée bleue", "sang frais", "chair humaine", "goût de fer et de sang"]):
            return True, "Matière première hors catalogue standard : Faisabilité à qualifier par l'équipe R&D."

        # 5. Conflit d'application dangereux (ingestion de produit parfumerie)
        if "buvable" in q_lower and ("parfum corporel" in q_lower or "diffuseur" in q_lower):
            return True, "Conflit réglementaire : Un parfum corporel ne peut pas être homologué pour la consommation alimentaire."

        # 6. Absence de viabilité commerciale (budget nul / gratuité impossible)
        if any(term in q_lower for term in ["gratuitement", "zéro euro", "0 euro", "sans budget", "bénévolement", "association étudiante"]):
            return True, "Demande hors cadre commercial standard : Orientation vers le service partenariats."

        # 7. Bruit, saisie aléatoire ou texte incompréhensible
        words = q_lower.split()
        if any(re.search(r"[bcdfghjklmnpqrstvwxz]{4,}", w) for w in words) or any(re.search(r"(.)\1{3,}", w) for w in words):
            return True, "Requête non intelligible : Détection de saisie aléatoire, orientation vers l'assistance."

        clean_text = re.sub(r"[^a-zA-Z0-9\s]", "", q_lower).strip()
        if len(clean_text) > 10 and not any(v in clean_text for v in ["a", "e", "i", "o", "u", "y", "é", "è"]):
            return True, "Requête non intelligible : Orientation vers le support client."

        return False, ""

    def search_hybrid(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        top_k: int = 3,
    ) -> dict[str, Any]:
        """Exécute la recherche hybride (Vectorielle + Filtrage déterministe + Explicabilité)."""
        filters = filters or {}

        # Vérification préalable des cas limites métier
        is_edge, edge_reason = self.detect_edge_case(query, filters)
        if is_edge:
            return {
                "status": "EXPERT_RELAY",
                "reason": edge_reason,
                "matches": [],
                "top_match": FALLBACK_EXPERT_ID,
                "is_expert_relay": True,
            }

        # 1. Calcul de l'embedding de requête et recherche vectorielle
        query_embedding = rag.embed_query(query)
        raw_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(10, self.collection.count()),
        )

        candidates = []
        for doc, meta, dist in zip(
            raw_results["documents"][0], raw_results["metadatas"][0], raw_results["distances"][0]
        ):
            item_id = meta["id"]
            item_data = self.catalog_by_id.get(item_id, {})
            similarity = round(1 - dist, 4)

            # 2. Filtrage déterministe
            passes_filters = True
            rejection_reasons = []

            # Filtre application
            req_app = filters.get("application")
            if req_app and req_app not in item_data.get("application", []):
                # Tolérance si plant_protein dans un cadre beverage
                if not (req_app == "plant_protein" and "beverage" in item_data.get("application", [])):
                    passes_filters = False
                    rejection_reasons.append(f"Incompatible application {req_app}")

            # Filtre certifications (Bio, Vegan, Halal, etc.)
            req_certs = filters.get("certifications", [])
            for c in req_certs:
                if c not in item_data.get("certifications", []):
                    passes_filters = False
                    rejection_reasons.append(f"Certification manquante : {c}")

            # Filtre thermorésistance
            if filters.get("heat_resistant") and not item_data.get("heat_resistant", False):
                passes_filters = False
                rejection_reasons.append("Non résistant aux hautes températures")

            # Filtre pH
            req_ph = filters.get("ph")
            if req_ph is not None:
                if req_ph < item_data.get("ph_min", 0) or req_ph > item_data.get("ph_max", 14):
                    passes_filters = False
                    rejection_reasons.append(f"pH {req_ph} hors de la plage [{item_data.get('ph_min')}-{item_data.get('ph_max')}]")

            candidates.append({
                "item": item_data,
                "similarity": similarity,
                "passes_filters": passes_filters,
                "rejection_reasons": rejection_reasons,
            })

        # Trier d'abord les candidats valides selon similarité
        valid_candidates = [c for c in candidates if c["passes_filters"]]

        # Si aucun candidat ne passe les filtres stricts, ou si la meilleure similarité est trop basse
        if not valid_candidates or valid_candidates[0]["similarity"] < SIMILARITY_THRESHOLD:
            # Si le meilleur score est vraiment bas (bruit / inconnu), renvoi expert
            max_sim = candidates[0]["similarity"] if candidates else 0.0
            if max_sim < SIMILARITY_THRESHOLD:
                return {
                    "status": "EXPERT_RELAY",
                    "reason": f"Aucune référence standard ne correspond avec certitude (meilleure similarité {max_sim:.2f} < seuil {SIMILARITY_THRESHOLD}). Brief transmis à l'Aromaticien.",
                    "matches": [],
                    "top_match": FALLBACK_EXPERT_ID,
                    "is_expert_relay": True,
                }
            # Si le produit vectoriel existait mais a été bloqué par les filtres stricts
            first_rejected = candidates[0]
            return {
                "status": "EXPERT_RELAY",
                "reason": f"Conflit technique : la référence la plus proche ({first_rejected['item'].get('name')}) ne respecte pas vos contraintes : {', '.join(first_rejected['rejection_reasons'])}. Relais vers la formulation sur-mesure.",
                "matches": [],
                "top_match": FALLBACK_EXPERT_ID,
                "is_expert_relay": True,
            }

        # Sélectionner les Top-K
        top_matches = valid_candidates[:top_k]

        return {
            "status": "SUCCESS",
            "reason": "Recommandation catalogue validée",
            "matches": [
                {
                    "id": m["item"]["id"],
                    "name": m["item"]["name"],
                    "family": m["item"]["family"],
                    "similarity": m["similarity"],
                    "dosage": m["item"]["dosage_recommended"],
                    "sensory_radar": m["item"]["sensory_radar"],
                    "sample_available": m["item"]["sample_available"],
                    "description": m["item"]["description"],
                    "certifications": m["item"]["certifications"],
                }
                for m in top_matches
            ],
            "top_match": top_matches[0]["item"]["id"],
            "is_expert_relay": False,
        }

    def generate_recommendation_pitch(self, query: str, search_result: dict[str, Any]) -> str:
        """Génère le texte explicatif et valorisant via Ollama LLM."""
        if search_result.get("is_expert_relay"):
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT_EXPERT_RELAY},
                {"role": "user", "content": f"Demande client : {query}\nRaison du basculement : {search_result.get('reason')}"},
            ]
        else:
            refs_summary = "\n\n".join(
                f"- Référence : {m['name']} (ID: {m['id']})\n"
                f"  Famille : {m['family']}\n"
                f"  Profil sensoriel : {m['description']}\n"
                f"  Dosage conseillé : {m['dosage']}\n"
                f"  Certifications : {', '.join(m['certifications'])}"
                for m in search_result.get("matches", [])
            )
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT_RECOMMENDER},
                {"role": "user", "content": f"Brief client : {query}\n\nRéférences trouvées :\n{refs_summary}\n\nRédige la recommandation pour le client."},
            ]

        try:
            return rag.chat(messages)
        except Exception as e:
            return f"Recommandation système : {search_result.get('reason')} (Détails disponibles dans la fiche technique)."
