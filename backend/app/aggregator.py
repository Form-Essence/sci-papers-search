"""Per-source-timeout aggregator for the web UI's ``/api/search`` endpoint.

The upstream :func:`paper_search_mcp.server.search_papers` uses
``asyncio.gather`` without any per-task timeout, so a single slow or
rate-limited source (e.g. Semantic Scholar doing 429 retries for ~15 s)
delays the HTTP response for *every* other source — even ones that
already have results.

This module replicates the upstream dispatch table but wraps each task
with :func:`asyncio.wait_for` so that:

- A slow/failed source never blocks faster ones beyond ``timeout`` seconds.
- Timeouts and exceptions are recorded in ``errors`` instead of propagating.
- The merged/deduplicated result shape is identical to the upstream one.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

from paper_search_mcp import server as mcp_server

logger = logging.getLogger("paper_search.aggregator")


def _build_task(
    source: str,
    query: str,
    max_results: int,
    year: Optional[str],
) -> Optional[Awaitable[List[Dict[str, Any]]]]:
    """Return the awaitable for ``source`` or ``None`` if unsupported."""
    match source:
        case "arxiv":
            return mcp_server.search_arxiv(query, max_results)
        case "pubmed":
            return mcp_server.search_pubmed(query, max_results)
        case "biorxiv":
            return mcp_server.search_biorxiv(query, max_results)
        case "medrxiv":
            return mcp_server.search_medrxiv(query, max_results)
        case "google_scholar":
            return mcp_server.search_google_scholar(query, max_results)
        case "iacr":
            return mcp_server.search_iacr(query, max_results, fetch_details=False)
        case "semantic":
            return mcp_server.search_semantic(query, year=year, max_results=max_results)
        case "crossref":
            return mcp_server.search_crossref(query, max_results=max_results)
        case "openalex":
            return mcp_server.search_openalex(query, max_results)
        case "pmc":
            return mcp_server.search_pmc(query, max_results)
        case "core":
            return mcp_server.search_core(query, max_results)
        case "europepmc":
            return mcp_server.search_europepmc(query, max_results)
        case "dblp":
            return mcp_server.search_dblp(query, max_results)
        case "openaire":
            return mcp_server.search_openaire(query, max_results)
        case "citeseerx":
            return mcp_server.search_citeseerx(query, max_results)
        case "doaj":
            return mcp_server.search_doaj(query, max_results)
        case "base":
            return mcp_server.search_base(query, max_results)
        case "zenodo":
            return mcp_server.search_zenodo(query, max_results)
        case "hal":
            return mcp_server.search_hal(query, max_results)
        case "ssrn":
            return mcp_server.search_ssrn(query, max_results)
        case "unpaywall":
            return mcp_server.search_unpaywall(query, max_results)
        case "ieee":
            if mcp_server.ieee_searcher is not None:
                return mcp_server.async_search(
                    mcp_server.ieee_searcher, query, max_results
                )
        case "acm":
            if mcp_server.acm_searcher is not None:
                return mcp_server.async_search(
                    mcp_server.acm_searcher, query, max_results
                )
    return None


async def _run_with_timeout(
    source: str,
    coro: Awaitable[List[Dict[str, Any]]],
    timeout: float,
) -> tuple[str, Any]:
    """Await ``coro`` with a timeout, returning ``(source, result_or_exc)``."""
    try:
        result = await asyncio.wait_for(coro, timeout=timeout)
        return source, result
    except asyncio.TimeoutError:
        logger.warning("Source %s timed out after %.1fs", source, timeout)
        return source, TimeoutError(
            f"No response after {int(timeout)}s — the source may be slow "
            "or rate-limited. Other sources finished normally."
        )
    except Exception as exc:  # noqa: BLE001 — we want to surface anything
        logger.warning("Source %s failed: %s", source, exc)
        return source, exc


def _resolve_sources_list(requested: List[str]) -> List[str]:
    """Normalise the UI's source list into upstream-recognised keys."""
    if not requested:
        return list(mcp_server.ALL_SOURCES)
    lowered = [s.strip().lower() for s in requested if s and s.strip()]
    if not lowered or "all" in lowered:
        return list(mcp_server.ALL_SOURCES)
    return [s for s in lowered if s in mcp_server.ALL_SOURCES]


async def search_papers_with_timeout(
    query: str,
    sources: List[str],
    max_results_per_source: int,
    year: Optional[str],
    per_source_timeout: float,
) -> Dict[str, Any]:
    """Aggregate per-source searches with an individual timeout per source."""
    selected = _resolve_sources_list(sources)
    sources_requested_str = ",".join(selected) if selected else "all"

    if not selected:
        return {
            "query": query,
            "sources_requested": sources_requested_str,
            "sources_used": [],
            "source_results": {},
            "errors": {"sources": "No valid sources selected."},
            "papers": [],
            "total": 0,
            "raw_total": 0,
        }

    wrapped: List[Awaitable[tuple[str, Any]]] = []
    used_sources: List[str] = []
    errors: Dict[str, str] = {}

    for source in selected:
        coro = _build_task(source, query, max_results_per_source, year)
        if coro is None:
            errors[source] = "Source not available in this deployment."
            continue
        used_sources.append(source)
        wrapped.append(_run_with_timeout(source, coro, per_source_timeout))

    outputs = await asyncio.gather(*wrapped) if wrapped else []

    source_results: Dict[str, int] = {}
    merged_papers: List[Dict[str, Any]] = []

    for source_name, output in outputs:
        if isinstance(output, BaseException):
            errors[source_name] = str(output) or output.__class__.__name__
            source_results[source_name] = 0
            continue
        papers = output or []
        source_results[source_name] = len(papers)
        for paper in papers:
            if not paper.get("source"):
                paper["source"] = source_name
            merged_papers.append(paper)

    deduped = mcp_server._dedupe_papers(merged_papers)

    return {
        "query": query,
        "sources_requested": sources_requested_str,
        "sources_used": used_sources,
        "source_results": source_results,
        "errors": errors,
        "papers": deduped,
        "total": len(deduped),
        "raw_total": len(merged_papers),
    }


__all__ = ["search_papers_with_timeout"]
