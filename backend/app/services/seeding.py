"""
PubMed seeding logic — 20 PubMedQA domains, ~55 queries, 200 results each.
Shared by seed_db.py (CLI) and main.py (auto-seed on cold start).

Progress is tracked in module-level _state and readable via get_state().
"""
import time
import requests
from Bio import Entrez

# ---------------------------------------------------------------------------
# Seed state — updated in-place by run_seed(), read by the status endpoint
# ---------------------------------------------------------------------------

_state: dict = {
    "status": "idle",       # idle | seeding | ready | error
    "chunks_stored": 0,
    "queries_done": 0,
    "total_queries": 0,
    "message": "DB not yet seeded.",
}


def get_state() -> dict:
    return dict(_state)


# ---------------------------------------------------------------------------
# Domain queries — 20 PubMedQA domains weighted by frequency
# ---------------------------------------------------------------------------

DOMAIN_QUERIES: list[str] = [
    # Oncology & Cancer (14.4%) — 4 queries
    "cancer chemotherapy treatment outcomes",
    "tumor immunotherapy checkpoint inhibitor",
    "cancer screening diagnosis biomarkers",
    "cancer radiation therapy survival",
    # Surgery & Perioperative Care (13.6%) — 4 queries
    "surgical complications postoperative outcomes",
    "laparoscopic minimally invasive surgery",
    "perioperative care management outcomes",
    "surgical site infection prevention",
    # Gastroenterology & Hepatology (11.1%) — 3 queries
    "inflammatory bowel disease Crohn's colitis treatment",
    "liver cirrhosis hepatitis treatment",
    "colorectal cancer gastrointestinal endoscopy",
    # Obstetrics, Gynecology & Neonatology (10.9%) — 3 queries
    "pregnancy complications preeclampsia outcomes",
    "preterm birth neonatal intensive care outcomes",
    "gynecologic cancer ovarian cervical treatment",
    # Cardiovascular Disease (9.2%) — 3 queries
    "heart failure treatment management outcomes",
    "coronary artery disease myocardial infarction",
    "atrial fibrillation stroke prevention anticoagulation",
    # Pediatrics (8.7%) — 3 queries
    "pediatric respiratory infection treatment",
    "childhood cancer leukemia treatment",
    "neonatal sepsis infection outcomes",
    # Metabolic & Endocrine (8.3%) — 3 queries
    "type 2 diabetes mellitus insulin treatment",
    "thyroid disease hypothyroidism hyperthyroidism",
    "obesity metabolic syndrome intervention",
    # Neurology & Psychiatry (6.5%) — 3 queries
    "Alzheimer dementia treatment cognitive decline",
    "stroke cerebrovascular treatment rehabilitation",
    "depression anxiety antidepressant treatment",
    # Orthopedics & Musculoskeletal (6.0%) — 2 queries
    "joint replacement arthroplasty outcomes",
    "osteoporosis fracture bone density treatment",
    # Infectious Disease & Immunology (5.7%) — 2 queries
    "antibiotic resistance infection treatment",
    "HIV AIDS antiretroviral therapy outcomes",
    # Radiology & Imaging (5.1%) — 2 queries
    "MRI CT diagnostic imaging accuracy",
    "cancer imaging detection screening radiology",
    # Urology & Nephrology (4.1%) — 2 queries
    "chronic kidney disease renal failure treatment",
    "prostate cancer urinary tract treatment",
    # Medical Education & Training (3.2%) — 2 queries
    "medical education clinical training simulation",
    "surgical training resident education outcomes",
    # Pulmonary & Respiratory (2.9%) — 2 queries
    "COPD chronic obstructive pulmonary disease treatment",
    "asthma bronchial treatment management",
    # Health Systems & Primary Care (2.1%) — 2 queries
    "primary care preventive medicine outcomes",
    "healthcare quality improvement patient safety",
    # Pharmacology & Drug Therapy (1.5%) — 2 queries
    "drug adverse effects interaction pharmacokinetics",
    "clinical pharmacology drug efficacy randomized trial",
    # Ophthalmology (1.1%) — 2 queries
    "glaucoma treatment intraocular pressure",
    "diabetic retinopathy macular degeneration treatment",
    # Anaesthesia & Pain (1.0%) — 2 queries
    "anesthesia perioperative complications management",
    "chronic pain management opioid treatment",
    # Haematology & Transfusion (0.9%) — 2 queries
    "blood transfusion anemia treatment outcomes",
    "leukemia lymphoma hematologic malignancy treatment",
    # Dermatology (0.8%) — 2 queries
    "melanoma skin cancer treatment immunotherapy",
    "psoriasis eczema dermatitis treatment",
]

MAX_RESULTS_PER_QUERY = 100

def _get_splitter():
    from langchain_text_splitters import RecursiveCharacterTextSplitter  # lazy
    return RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " "],
    )


# ---------------------------------------------------------------------------
# PubMed fetch helpers
# ---------------------------------------------------------------------------

def _search(query: str, max_results: int) -> list[str]:
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]


def _fetch_full_text(pmid: str) -> dict | None:
    url = (
        "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/"
        f"pmcoa.cgi/BioC_json/{pmid}/unicode"
    )
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        parts = []
        for doc in r.json().get("documents", []):
            for passage in doc.get("passages", []):
                section = passage.get("infons", {}).get("section_type", "unknown")
                text = passage.get("text", "").strip()
                if text:
                    parts.append(f"[{section}] {text}")
        if not parts:
            return None
        return {
            "pmid": pmid,
            "full_text": "\n\n".join(parts),
            "source": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "is_full_text": True,
        }
    except Exception:
        return None


def _fetch_abstract(pmid: str) -> dict | None:
    try:
        handle = Entrez.efetch(db="pubmed", id=pmid, rettype="abstract", retmode="xml")
        records = Entrez.read(handle)
        handle.close()
        article = records["PubmedArticle"][0]
        medline = article["MedlineCitation"]
        title = str(medline["Article"]["ArticleTitle"])
        abstract_texts = medline["Article"].get("Abstract", {}).get("AbstractText", [])
        abstract = " ".join(str(a) for a in abstract_texts)
        if not abstract:
            return None
        return {
            "pmid": pmid,
            "full_text": f"[TITLE] {title}\n\n[ABSTRACT] {abstract}",
            "source": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "is_full_text": False,
        }
    except Exception:
        return None


def _chunk(doc: dict) -> list[dict]:
    splitter = _get_splitter()
    chunks = []
    for i, text in enumerate(splitter.split_text(doc["full_text"])):
        chunks.append({
            "text": text,
            "metadata": {
                "pmid": doc["pmid"],
                "source": doc["source"],
                "is_full_text": doc["is_full_text"],
                "chunk_index": i,
            },
        })
    return chunks


# ---------------------------------------------------------------------------
# Main seeding entry point
# ---------------------------------------------------------------------------

def run_seed(vector_store, email: str, ncbi_api_key: str = "") -> int:
    """
    Seed the vector store with PubMed abstracts across all 20 domains.
    Stores batches incrementally so partial progress survives an interruption.
    Returns total chunk count in the collection when done.
    """
    global _state

    Entrez.email = email
    if ncbi_api_key:
        Entrez.api_key = ncbi_api_key

    sleep_s = 0.1 if ncbi_api_key else 0.4
    total_q = len(DOMAIN_QUERIES)
    est_min = int(total_q * MAX_RESULTS_PER_QUERY * sleep_s / 60)

    _state.update({
        "status": "seeding",
        "chunks_stored": 0,
        "queries_done": 0,
        "total_queries": total_q,
        "message": f"Seeding started — {total_q} queries, ~{est_min} min estimated",
    })

    seen: set[str] = set()

    try:
        for qi, query in enumerate(DOMAIN_QUERIES):
            pmids = _search(query, MAX_RESULTS_PER_QUERY)
            new_pmids = [p for p in pmids if p not in seen]
            seen.update(new_pmids)

            docs_added = 0
            chunks_added = 0
            for pmid in new_pmids:
                doc = _fetch_full_text(pmid) or _fetch_abstract(pmid)
                if doc:
                    chunks = _chunk(doc)
                    if chunks:
                        # store one document at a time — keeps peak memory low
                        vector_store.add_texts(
                            texts=[c["text"] for c in chunks],
                            metadatas=[c["metadata"] for c in chunks],
                            ids=[
                                f"{c['metadata']['pmid']}_chunk_{c['metadata']['chunk_index']}"
                                for c in chunks
                            ],
                        )
                        chunks_added += len(chunks)
                        docs_added += 1
                time.sleep(sleep_s)

            _state["queries_done"] = qi + 1
            _state["chunks_stored"] = vector_store._collection.count()
            _state["message"] = (
                f"Query {qi + 1}/{total_q}: '{query}' "
                f"— {docs_added} docs, {chunks_added} chunks "
                f"(total: {_state['chunks_stored']})"
            )

        total = vector_store._collection.count()
        _state.update({
            "status": "ready",
            "chunks_stored": total,
            "message": f"Seeding complete — {total} chunks across {total_q} queries.",
        })
        return total

    except Exception as exc:
        _state.update({
            "status": "error",
            "message": f"Seeding failed at query {_state['queries_done'] + 1}: {exc}",
        })
        raise
