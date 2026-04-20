"""Human-readable labels for the sources exposed by paper-search-mcp."""

from __future__ import annotations

from typing import Dict, List

from .schemas import SourceInfo

SOURCE_LABELS: Dict[str, Dict[str, str]] = {
    "arxiv": {"label": "arXiv", "note": "Open API, full-text available."},
    "pubmed": {"label": "PubMed", "note": "Metadata only."},
    "biorxiv": {"label": "bioRxiv", "note": "Category filter, last 30 days."},
    "medrxiv": {"label": "medRxiv", "note": "Category filter, last 30 days."},
    "google_scholar": {
        "label": "Google Scholar",
        "note": "May be blocked by bot-detection; set PAPER_SEARCH_MCP_GOOGLE_SCHOLAR_PROXY_URL.",
    },
    "iacr": {"label": "IACR ePrint", "note": "Cryptography-focused."},
    "semantic": {
        "label": "Semantic Scholar",
        "note": "Optional key improves rate limits.",
    },
    "crossref": {"label": "Crossref", "note": "DOI metadata only."},
    "openalex": {"label": "OpenAlex", "note": "Broad open metadata source."},
    "pmc": {"label": "PubMed Central", "note": "Open-access biomedical full-text."},
    "core": {"label": "CORE", "note": "Free API key recommended."},
    "europepmc": {"label": "Europe PMC", "note": "Open-access biomedical full-text."},
    "dblp": {"label": "dblp", "note": "Computer-science bibliography."},
    "openaire": {"label": "OpenAIRE", "note": "European OA aggregator."},
    "citeseerx": {"label": "CiteSeerX", "note": "Intermittent upstream availability."},
    "doaj": {"label": "DOAJ", "note": "Directory of Open Access Journals."},
    "base": {"label": "BASE", "note": "Requires institutional IP for full results."},
    "zenodo": {"label": "Zenodo", "note": "Open repository."},
    "hal": {"label": "HAL", "note": "French open archive."},
    "ssrn": {"label": "SSRN", "note": "Metadata-only; no PDF download."},
    "unpaywall": {
        "label": "Unpaywall",
        "note": "DOI lookup only; requires PAPER_SEARCH_MCP_UNPAYWALL_EMAIL.",
    },
    "ieee": {"label": "IEEE Xplore", "note": "Requires PAPER_SEARCH_MCP_IEEE_API_KEY."},
    "acm": {"label": "ACM DL", "note": "Requires PAPER_SEARCH_MCP_ACM_API_KEY."},
}


def build_source_list(available: List[str]) -> List[SourceInfo]:
    """Merge runtime-available source keys with their human-readable metadata."""
    out: List[SourceInfo] = []
    for key in available:
        meta = SOURCE_LABELS.get(key, {"label": key, "note": None})
        out.append(SourceInfo(key=key, label=meta.get("label", key), note=meta.get("note")))
    return out
