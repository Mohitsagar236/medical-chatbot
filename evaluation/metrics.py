"""
Metric computation for the medical chatbot evaluation.
All models are loaded once at module level to avoid reloading per call.
"""
from __future__ import annotations

import numpy as np
from bert_score import BERTScorer
from sentence_transformers import SentenceTransformer, CrossEncoder

# ---------------------------------------------------------------------------
# Pricing constants — Groq llama-3.3-70b-versatile (per token)
# ---------------------------------------------------------------------------
GROQ_INPUT_PRICE  = 0.59 / 1_000_000
GROQ_OUTPUT_PRICE = 0.79 / 1_000_000

# ---------------------------------------------------------------------------
# Model singletons — loaded once
# ---------------------------------------------------------------------------
_bert_scorer: BERTScorer | None = None
_embedder: SentenceTransformer | None = None
_nli: CrossEncoder | None = None


def _get_bert_scorer() -> BERTScorer:
    global _bert_scorer
    if _bert_scorer is None:
        _bert_scorer = BERTScorer(model_type="distilbert-base-uncased", lang="en", rescale_with_baseline=False)
    return _bert_scorer


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def _get_nli() -> CrossEncoder:
    global _nli
    if _nli is None:
        _nli = CrossEncoder("cross-encoder/nli-deberta-v3-small")
    return _nli


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_label_accuracy(answer: str, ground_truth_label: str | None) -> bool | None:
    """Turn 1 only. True if the yes/no/maybe label appears as a word in the answer."""
    if not ground_truth_label:
        return None
    label = ground_truth_label.strip().lower()
    return label in answer.lower()


def compute_bert_score(answer: str, reference_answer: str) -> float:
    """BERTScore F1 between the model answer and the reference answer."""
    scorer = _get_bert_scorer()
    _, _, f1 = scorer.score([answer], [reference_answer])
    return round(float(f1[0]), 4)


# Phrases that unambiguously indicate the model declined to answer rather than
# making a factual claim. Checked before running NLI so that honest non-answers
# are not mis-scored as CONTRADICTION.
# Rules for adding a phrase here:
#   - Must be specific enough that it cannot appear in a genuine factual answer
#   - RAG refusals: model explicitly says the retrieved context lacks the info
#   - S1/S3 refusals: model says it doesn't know this particular study/data
_HEDGE_PHRASES = (
    # RAG context refusals (S2/S4)
    "provided context does not contain",
    "the context does not contain",
    "context does not have enough",
    "not available in the given context",
    "not available in the provided context",
    # "I don't know this specific study" refusals (S1/S3)
    "i'm not aware of the specific",
    "i am not aware of the specific",
    "i'm not aware of any specific",
    "i am not aware of any specific",
    # Clarification-request endings (always a full non-answer when present)
    "if you have a particular study in mind",
    "if you could provide more details",
    "could you please provide more information",
)


def compute_hallucination(answer: str, contexts: str) -> tuple[str, bool]:
    """
    NLI-based hallucination detection.
    premise = contexts (PubMed abstract), hypothesis = model answer.

    Returns (label, is_hallucination) where label is one of:
      HEDGED       — model declined to answer; not a hallucination
      ENTAILMENT   — answer is supported by the abstract
      NEUTRAL      — answer is unrelated to the abstract (no claim either way)
      CONTRADICTION — answer conflicts with the abstract; flagged as hallucination

    Honest non-answers (RAG refusals, "I don't know this study") are caught by
    the pre-filter and returned as HEDGED before the NLI model is invoked.
    """
    answer_lower = answer.lower()
    for phrase in _HEDGE_PHRASES:
        if phrase in answer_lower:
            return "HEDGED", False

    nli = _get_nli()
    # cross-encoder/nli-deberta-v3-small label order: CONTRADICTION, ENTAILMENT, NEUTRAL
    scores = nli.predict([(contexts, answer)])
    label_idx = int(np.argmax(scores[0]))
    label_map = {0: "CONTRADICTION", 1: "ENTAILMENT", 2: "NEUTRAL"}
    label = label_map[label_idx]
    return label, label == "CONTRADICTION"


def compute_context_recall(retrieved_chunks: list[str], contexts: str) -> float:
    """
    Recall-oriented: for each sentence in contexts, find the max cosine similarity
    to any retrieved chunk. Return the mean of those max sims.
    Range [0, 1] — higher means retrieval covered the reference context well.
    """
    if not retrieved_chunks or not contexts.strip():
        return 0.0
    embedder = _get_embedder()
    # Split contexts into sentences on semicolons or newlines
    ctx_sentences = [s.strip() for s in contexts.replace(";", "\n").split("\n") if s.strip()]
    if not ctx_sentences:
        return 0.0
    ctx_embs = embedder.encode(ctx_sentences, normalize_embeddings=True)
    chunk_embs = embedder.encode(retrieved_chunks, normalize_embeddings=True)
    # cosine sim matrix: (n_ctx_sentences × n_chunks)
    sim_matrix = ctx_embs @ chunk_embs.T
    # for each context sentence, best matching chunk
    max_sims = sim_matrix.max(axis=1)
    return round(float(max_sims.mean()), 4)


def compute_coherence(current_answer: str, previous_answer: str) -> float:
    """
    Cosine similarity between current and previous turn answers.
    High similarity = the conversation stayed on topic.
    Range [-1, 1].
    """
    embedder = _get_embedder()
    embs = embedder.encode([current_answer, previous_answer], normalize_embeddings=True)
    return round(float(embs[0] @ embs[1]), 4)


def compute_cost(prompt_tokens: int | None, completion_tokens: int | None) -> float | None:
    """Dollar cost for a single call based on Groq llama-3.3-70b pricing."""
    if prompt_tokens is None or completion_tokens is None:
        return None
    return round(prompt_tokens * GROQ_INPUT_PRICE + completion_tokens * GROQ_OUTPUT_PRICE, 8)
