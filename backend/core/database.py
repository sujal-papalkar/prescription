"""
Hybrid Search Engine for Ayurvedic Clinical Guidelines
Combines ChromaDB Dense Vector Search with BM25Okapi Sparse Keyword Retrieval
Blended via Reciprocal Rank Fusion (RRF) with hard metadata pre-filtering.
"""

import os
import re
import pickle
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv
from google import genai

# Automatically load environment variables from backend/.env or root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
load_dotenv()

logger = logging.getLogger(__name__)


def tokenize_ayurvedic_text(text: str) -> List[str]:
    """
    Tokenizes medical and clinical text, preserving Sanskrit terminology,
    hyphenated compound terms, and dosage patterns.
    """
    clean_text = text.lower()
    # Normalize punctuation while keeping terms like 1-1-1 or shwas-kasa
    tokens = re.findall(r"\b[a-z0-9]+(?:-[a-z0-9]+)*\b", clean_text)
    return tokens


class HybridSearchEngine:
    """
    Local Hybrid Search Engine managing:
    1. Persistent ChromaDB collection with Google gemini-embedding-001 (768-dim) coordinates.
    2. BM25Okapi keyword index partitioned by disease_name for exact medical terms.
    3. Reciprocal Rank Fusion (RRF) rank blending.
    """

    def __init__(self, persist_dir: str = "./data/chroma_db", api_key: Optional[str] = None):
        self.persist_dir = os.path.abspath(persist_dir)
        os.makedirs(self.persist_dir, exist_ok=True)
        self.bm25_store_path = os.path.join(self.persist_dir, "bm25_store.pkl")

        # 1. Initialize Persistent ChromaDB Client
        self.chroma_client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.chroma_client.get_or_create_collection(
            name="ayurvedic_guidelines",
            metadata={"hnsw:space": "cosine"}
        )

        # 2. Setup Gemini Client for Embeddings (HttpOptions.timeout is in milliseconds)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.genai_client = None
        if self.api_key:
            try:
                self.genai_client = genai.Client(api_key=self.api_key, http_options={"timeout": 30000})
                logger.info("Initialized Google GenAI Client with 30s timeout (30,000ms).")
            except Exception as e:
                logger.warning(f"Failed to initialize GenAI client with provided key: {e}")

        # 3. In-memory BM25 indices partitioned by disease_name
        # Format: { disease_name: {"bm25": BM25Okapi, "chunks": List[Dict], "tokenized_corpus": List[List[str]]} }
        self.bm25_store: Dict[str, Dict[str, Any]] = {}
        self._load_bm25_store()

    def _load_bm25_store(self):
        """Loads cached BM25 data from disk if available and synchronizes with ChromaDB."""
        if os.path.exists(self.bm25_store_path):
            try:
                self._last_bm25_mtime = os.path.getmtime(self.bm25_store_path)
                with open(self.bm25_store_path, "rb") as f:
                    self.bm25_store = pickle.load(f)
                logger.info(f"Loaded BM25 indices for diseases: {list(self.bm25_store.keys())}")
                # Synchronize missing metadata fields (like page numbers) from ChromaDB
                try:
                    if self.collection.count() > 0:
                        all_ids = []
                        for disease_data in self.bm25_store.values():
                            for c in disease_data.get("chunks", []):
                                if "page" not in c.get("metadata", {}) or not c["metadata"]["page"]:
                                    all_ids.append(c["chunk_id"])
                        if all_ids:
                            records = self.collection.get(ids=all_ids)
                            if records and records.get("ids"):
                                id_to_meta = dict(zip(records["ids"], records.get("metadatas", [])))
                                for disease_data in self.bm25_store.values():
                                    for c in disease_data.get("chunks", []):
                                        if c["chunk_id"] in id_to_meta and id_to_meta[c["chunk_id"]]:
                                            c["metadata"].update(id_to_meta[c["chunk_id"]])
                                self._persist_bm25_store()
                except Exception as se:
                    logger.debug(f"BM25 metadata sync skipped: {se}")
            except Exception as e:
                logger.warning(f"Could not load BM25 store from disk: {e}. Starting fresh.")
                self.bm25_store = {}

    def _persist_bm25_store(self):
        """Persists BM25 indices to disk."""
        try:
            with open(self.bm25_store_path, "wb") as f:
                pickle.dump(self.bm25_store, f)
            if os.path.exists(self.bm25_store_path):
                self._last_bm25_mtime = os.path.getmtime(self.bm25_store_path)
            logger.info("Saved BM25 store to disk.")
        except Exception as e:
            logger.error(f"Failed to persist BM25 store: {e}")

    def _check_and_reload_bm25_if_updated(self):
        """Reloads bm25 store from disk if the file has been updated by another process or task."""
        try:
            if os.path.exists(self.bm25_store_path):
                mtime = os.path.getmtime(self.bm25_store_path)
                if getattr(self, "_last_bm25_mtime", 0) < mtime:
                    with open(self.bm25_store_path, "rb") as f:
                        self.bm25_store = pickle.load(f)
                    self._last_bm25_mtime = mtime
                    logger.info("Automatically reloaded fresh BM25 store from disk.")
        except Exception as e:
            logger.debug(f"BM25 reload error: {e}")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of strings using Google Gemini's text-embedding-004 model.
        Falls back to local normalized hash embeddings if API key is unconfigured.
        """
        if self.genai_client:
            try:
                # Gemini text-embedding-004 supports batch embedding
                embeddings_list = []
                batch_size = 20
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    response = self.genai_client.models.embed_content(
                        model="gemini-embedding-001",
                        contents=batch,
                        config={"output_dimensionality": 768}
                    )
                    # response.embeddings is a list of ContentEmbedding objects
                    for emb in response.embeddings:
                        embeddings_list.append(emb.values)
                return embeddings_list
            except Exception as e:
                logger.error(f"Gemini embed_content API call failed: {e}. Utilizing fallback vectors.")

        # Robust deterministic fallback vector generator for offline/local development
        logger.warning("Using local deterministic semantic coordinate generation.")
        return [self._generate_fallback_vector(t) for t in texts]

    def _generate_fallback_vector(self, text: str, dim: int = 768) -> List[float]:
        """Generates a deterministic 768-dim normalized pseudo-embedding."""
        import hashlib
        import math

        vector = [0.0] * dim
        tokens = tokenize_ayurvedic_text(text)
        if not tokens:
            tokens = ["empty"]

        for token in tokens:
            hash_val = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
            idx = hash_val % dim
            vector[idx] += 1.0

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    def ingest_chunks(self, chunks: List[Dict[str, Any]], disease_name: str) -> int:
        """
        Ingests parsed chunks into both ChromaDB and BM25 index.
        Applies metadata tags and updates indices.
        """
        if not chunks:
            logger.warning("No chunks provided to ingest.")
            return 0

        texts = [chunk["text"] for chunk in chunks]
        ids = [chunk["chunk_id"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        # 1. Embed and store in ChromaDB
        embeddings = self.embed_texts(texts)

        # Upsert into ChromaDB
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        # 2. Build / Update BM25 index for this specific disease
        tokenized_corpus = [tokenize_ayurvedic_text(t) for t in texts]
        bm25_instance = BM25Okapi(tokenized_corpus)

        self.bm25_store[disease_name] = {
            "bm25": bm25_instance,
            "chunks": chunks,
            "tokenized_corpus": tokenized_corpus
        }
        self._persist_bm25_store()

        logger.info(f"Successfully indexed {len(chunks)} chunks for disease '{disease_name}'")
        return len(chunks)

    def clear_all(self):
        """Wipes all documents and indices, ensuring a 100% clean state."""
        try:
            self.chroma_client.delete_collection("ayurvedic_guidelines")
        except Exception as e:
            logger.debug(f"Could not delete collection: {e}")
        self.collection = self.chroma_client.get_or_create_collection(
            name="ayurvedic_guidelines",
            metadata={"hnsw:space": "cosine"}
        )
        self.bm25_store = {}
        if os.path.exists(self.bm25_store_path):
            try:
                os.remove(self.bm25_store_path)
            except Exception as e:
                logger.warning(f"Could not remove bm25 store file: {e}")
        logger.info("Successfully wiped all documents and indices from database.")

    def _resolve_canonical_disease(self, target: Optional[str]) -> Optional[str]:
        """Resolves fuzzy disease name or taxomony string to the exact indexed partition key."""
        if not target or target.strip() in ("", "All", "Auto-Detect") or target.strip().lower() in ("both", "cross-document", "cross_document", "global"):
            return None
        indexed = self.get_indexed_diseases()
        if not indexed:
            return None
        if target in indexed:
            return target
        target_lower = target.lower()
        for d in indexed:
            d_lower = d.lower()
            if target_lower in d_lower or d_lower in target_lower:
                return d
            t_words = set(re.findall(r"\w+", target_lower)) - {"disease", "infections", "management", "protocol"}
            d_words = set(re.findall(r"\w+", d_lower)) - {"disease", "infections", "management", "protocol"}
            if t_words and len(t_words & d_words) >= 1:
                return d
        return None

    def hybrid_retrieve(
        self,
        query: str,
        disease_name: Optional[str] = None,
        top_k: int = 10,
        rrf_k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Dual-Engine Retrieval Matrix:
        1. Queries ChromaDB dense vector store (with optional metadata pre-filter).
        2. Queries partitioned BM25 index with tokenized exact terms.
        3. Blends rankings using Reciprocal Rank Fusion (RRF).
        """
        self._check_and_reload_bm25_if_updated()

        if self.collection.count() == 0:
            logger.info("ChromaDB is empty. No documents uploaded yet.")
            return []

        canonical_disease = self._resolve_canonical_disease(disease_name)

        dense_results: List[Dict[str, Any]] = []
        sparse_results: List[Dict[str, Any]] = []

        # --- Vector Search (Dense) ---
        query_vector = self.embed_texts([query])[0]
        try:
            query_kwargs: Dict[str, Any] = {
                "query_embeddings": [query_vector],
                "n_results": min(top_k * 3, self.collection.count())
            }
            if canonical_disease:
                query_kwargs["where"] = {"disease_name": canonical_disease}

            chroma_res = self.collection.query(**query_kwargs)

            if chroma_res and chroma_res["ids"] and len(chroma_res["ids"][0]) > 0:
                retrieved_ids = chroma_res["ids"][0]
                retrieved_docs = chroma_res["documents"][0]
                retrieved_meta = chroma_res["metadatas"][0]
                distances = chroma_res.get("distances", [[0.0] * len(retrieved_ids)])[0]

                for rank, (c_id, doc, meta, dist) in enumerate(zip(retrieved_ids, retrieved_docs, retrieved_meta, distances)):
                    dense_results.append({
                        "chunk_id": c_id,
                        "text": doc,
                        "metadata": meta,
                        "score": 1.0 - dist if dist is not None else 0.5,
                        "rank": rank + 1
                    })
        except Exception as e:
            logger.error(f"ChromaDB retrieval failed: {e}")

        # --- BM25 Keyword Search (Sparse) ---
        target_partitions = (
            [canonical_disease] if canonical_disease and canonical_disease in self.bm25_store
            else list(self.bm25_store.keys())
        )

        tokenized_query = tokenize_ayurvedic_text(query)
        if tokenized_query:
            for part in target_partitions:
                disease_data = self.bm25_store[part]
                bm25: BM25Okapi = disease_data["bm25"]
                stored_chunks: List[Dict[str, Any]] = disease_data["chunks"]

                bm25_scores = bm25.get_scores(tokenized_query)
                scored_indices = sorted(
                    range(len(bm25_scores)),
                    key=lambda i: bm25_scores[i],
                    reverse=True
                )

                for rank, idx in enumerate(scored_indices[: top_k * 2]):
                    if bm25_scores[idx] > 0:
                        c = stored_chunks[idx]
                        sparse_results.append({
                            "chunk_id": c["chunk_id"],
                            "text": c["text"],
                            "metadata": c["metadata"],
                            "score": float(bm25_scores[idx]),
                            "rank": rank + 1
                        })
        else:
            logger.warning(f"No BM25 partition found for disease '{disease_name}'")

        # --- Reciprocal Rank Fusion (RRF) Blending ---
        # Formula: RRF_Score = sum( 1 / (rrf_k + rank_i) )
        fused_scores: Dict[str, float] = {}
        chunk_map: Dict[str, Dict[str, Any]] = {}
        source_tags: Dict[str, List[str]] = {}

        # Process Dense Ranks
        for item in dense_results:
            cid = item["chunk_id"]
            rank = item["rank"]
            fused_scores[cid] = fused_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))
            chunk_map[cid] = item
            source_tags.setdefault(cid, []).append(f"Vector (Rank #{rank})")

        # Process Sparse Ranks
        for item in sparse_results:
            cid = item["chunk_id"]
            rank = item["rank"]
            fused_scores[cid] = fused_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))
            if cid not in chunk_map:
                chunk_map[cid] = item
            source_tags.setdefault(cid, []).append(f"BM25 (Rank #{rank})")

        # Universal query-aligned token boost: boost chunks that directly contain distinctive query keywords
        q_tokens = set(re.findall(r"\w+", query.lower())) - {
            "what", "are", "the", "recommended", "for", "patient", "with", "having", "score", "level",
            "from", "pdf", "document", "and", "in", "is", "a", "an", "to", "of", "does", "can"
        }
        if q_tokens:
            for cid, item in chunk_map.items():
                txt = item.get("text", "").lower()
                sec = str(item.get("metadata", {}).get("section", "")).lower()
                overlap = sum(1 for tok in q_tokens if tok in txt or tok in sec)
                if overlap > 0:
                    fused_scores[cid] = fused_scores.get(cid, 0.0) * (1.0 + 0.1 * min(overlap, 5))

        # Sort combined results by RRF score descending
        sorted_cids = sorted(fused_scores.keys(), key=lambda cid: fused_scores[cid], reverse=True)
        top_ids = sorted_cids[:top_k]

        # Retrieve canonical metadata from ChromaDB for the top candidates
        canonical_meta: Dict[str, Dict[str, Any]] = {}
        if top_ids:
            try:
                chroma_records = self.collection.get(ids=top_ids)
                if chroma_records and chroma_records.get("ids"):
                    for c_id, c_meta in zip(chroma_records["ids"], chroma_records.get("metadatas", [])):
                        if c_meta:
                            canonical_meta[c_id] = c_meta
            except Exception as e:
                logger.debug(f"Could not fetch canonical metadata from collection: {e}")

        final_chunks: List[Dict[str, Any]] = []
        for cid in top_ids:
            base = chunk_map[cid]
            merged_meta = dict(base.get("metadata") or {})
            if cid in canonical_meta:
                merged_meta.update(canonical_meta[cid])
            final_chunks.append({
                "chunk_id": cid,
                "text": base["text"],
                "metadata": merged_meta,
                "rrf_score": round(fused_scores[cid], 5),
                "matched_engines": source_tags[cid]
            })

        logger.info(f"Hybrid retrieved {len(final_chunks)} chunks for query: '{query[:40]}...'")
        return final_chunks

    def get_indexed_diseases(self) -> List[str]:
        """Returns list of all disease categories currently indexed."""
        self._check_and_reload_bm25_if_updated()
        diseases = set(self.bm25_store.keys())
        try:
            metas = self.collection.get().get("metadatas", [])
            for m in metas:
                if m and "disease_name" in m:
                    diseases.add(m["disease_name"])
        except Exception as e:
            logger.debug(f"Chroma disease scan exception: {e}")
        return sorted(list(diseases))
