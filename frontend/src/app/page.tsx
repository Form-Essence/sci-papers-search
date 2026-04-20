"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { ResultsGrid } from "@/components/results-grid";
import { SearchForm, type SearchFormValues } from "@/components/search-form";
import {
  fetchSources,
  searchPapers,
  type SearchResponse,
  type SourceInfo,
} from "@/lib/api";

export default function Home() {
  const [availableSources, setAvailableSources] = useState<SourceInfo[]>([]);
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchSources()
      .then((res) => {
        if (!cancelled) setAvailableSources(res.sources);
      })
      .catch((err) => {
        toast.error("Could not reach backend", {
          description:
            err instanceof Error
              ? err.message
              : "Is the paper-search server running?",
        });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function onSubmit(values: SearchFormValues) {
    setLoading(true);
    setResponse(null);
    try {
      const res = await searchPapers({
        query: values.query,
        sources: values.sources,
        max_results_per_source: values.maxResultsPerSource,
        year: values.year || null,
      });
      setResponse(res);
      if (res.total === 0) {
        toast.warning("No results", {
          description: `No papers matched "${values.query}" on the selected sources.`,
        });
      }
    } catch (err) {
      toast.error("Search failed", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-6 py-10">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold tracking-tight">Paper Search</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Manual search interface for the{" "}
          <a
            href="https://github.com/openags/paper-search-mcp"
            target="_blank"
            rel="noreferrer"
            className="underline underline-offset-2"
          >
            paper-search-mcp
          </a>{" "}
          server. The same backend library also exposes an MCP server so any
          MCP-capable LLM client (Claude, LM Studio, OpenAI, Cursor) can use
          these sources as tools.
        </p>
      </header>

      <SearchForm
        availableSources={availableSources}
        loading={loading}
        onSubmit={onSubmit}
      />

      <ResultsGrid loading={loading} response={response} />
    </main>
  );
}
