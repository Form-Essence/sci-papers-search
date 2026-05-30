"""Pydantic schemas for the paper-search backend HTTP API.

These models intentionally mirror the shape of `paper_search_mcp.paper.Paper.to_dict()`
so that the FastAPI wrapper can pass results through unchanged.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string.")
    sources: List[str] = Field(
        default_factory=lambda: ["arxiv"],
        description=(
            "List of source keys, e.g. ['arxiv', 'pubmed']. "
            "Use ['all'] to query every configured source."
        ),
    )
    max_results_per_source: int = Field(
        default=5, ge=1, le=50, description="Max results fetched from each source."
    )
    year: Optional[str] = Field(
        default=None,
        description="Optional year filter (only honored by Semantic Scholar).",
    )


class Paper(BaseModel):
    paper_id: str = ""
    title: str = ""
    authors: str = ""
    abstract: str = ""
    doi: str = ""
    published_date: str = ""
    pdf_url: str = ""
    url: str = ""
    source: str = ""
    updated_date: str = ""
    categories: str = ""
    keywords: str = ""
    citations: int = 0
    references: str = ""
    extra: str = ""


class SearchResponse(BaseModel):
    query: str
    sources_requested: List[str]
    sources_used: List[str]
    source_results: Dict[str, int]
    errors: Dict[str, str]
    papers: List[Dict[str, Any]]
    total: int
    raw_total: int = 0


class DownloadRequest(BaseModel):
    source: str = Field(..., description="Source key (e.g. 'arxiv', 'biorxiv', 'semantic').")
    paper_id: str = Field(..., description="Source-native paper identifier.")
    doi: str = ""
    title: str = ""
    use_scihub: bool = Field(
        default=False,
        description="Whether to attempt Sci-Hub after all OA fallbacks fail.",
    )


class DownloadResponse(BaseModel):
    ok: bool
    message: str
    path: Optional[str] = None


class SourceInfo(BaseModel):
    key: str
    label: str
    note: Optional[str] = None


class SourcesResponse(BaseModel):
    sources: List[SourceInfo]


class McpClientSnippet(BaseModel):
    id: str
    label: str
    language: Literal["json", "bash", "python", "javascript"]
    filename: Optional[str] = None
    instructions: str
    snippet: str


class McpConfigResponse(BaseModel):
    public_url: str
    mcp_url: str
    clients: List[McpClientSnippet]


class LoginRequest(BaseModel):
    password: str = Field(..., min_length=1)
