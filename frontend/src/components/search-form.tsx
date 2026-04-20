"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import type { SourceInfo } from "@/lib/api";

export type SearchFormValues = {
  query: string;
  sources: string[];
  maxResultsPerSource: number;
  year: string;
};

type Props = {
  availableSources: SourceInfo[];
  loading: boolean;
  onSubmit: (values: SearchFormValues) => void;
};

const DEFAULT_SOURCES = new Set([
  "arxiv",
  "semantic",
  "openalex",
  "crossref",
]);

export function SearchForm({ availableSources, loading, onSubmit }: Props) {
  const [query, setQuery] = useState("");
  const [sources, setSources] = useState<string[]>([]);
  const [maxResultsPerSource, setMaxResultsPerSource] = useState(5);
  const [year, setYear] = useState("");

  useEffect(() => {
    if (availableSources.length === 0) return;
    setSources((prev) => {
      if (prev.length > 0) return prev;
      const preferred = availableSources
        .map((s) => s.key)
        .filter((k) => DEFAULT_SOURCES.has(k));
      return preferred.length > 0
        ? preferred
        : [availableSources[0]?.key].filter(Boolean);
    });
  }, [availableSources]);

  function toggleSource(key: string, checked: boolean) {
    setSources((prev) =>
      checked ? [...new Set([...prev, key])] : prev.filter((k) => k !== key),
    );
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    onSubmit({
      query: query.trim(),
      sources,
      maxResultsPerSource,
      year: year.trim(),
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-5 rounded-xl border bg-card p-5 shadow-sm"
    >
      <div className="flex flex-col gap-2">
        <Label htmlFor="query">Query</Label>
        <Input
          id="query"
          placeholder="e.g. transformer attention mechanism"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <div className="flex flex-col gap-2">
          <Label htmlFor="max-results">Results / source</Label>
          <Input
            id="max-results"
            type="number"
            min={1}
            max={50}
            value={maxResultsPerSource}
            onChange={(e) =>
              setMaxResultsPerSource(
                Math.max(1, Math.min(50, Number(e.target.value) || 1)),
              )
            }
          />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="year">
            Year <span className="text-muted-foreground">(Semantic only)</span>
          </Label>
          <Input
            id="year"
            placeholder="2020 or 2019-2023"
            value={year}
            onChange={(e) => setYear(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-2 sm:col-span-1 col-span-2">
          <Label>Selected</Label>
          <div className="flex min-h-9 flex-wrap items-center gap-1 rounded-md border bg-background px-3 py-1.5 text-sm">
            {sources.length === 0 ? (
              <span className="text-muted-foreground">none</span>
            ) : (
              sources.map((s) => (
                <Badge key={s} variant="secondary" className="text-xs">
                  {s}
                </Badge>
              ))
            )}
          </div>
        </div>
      </div>

      <Separator />

      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <Label>Sources</Label>
          <div className="flex gap-2 text-xs">
            <button
              type="button"
              className="text-muted-foreground hover:text-foreground"
              onClick={() =>
                setSources(availableSources.map((s) => s.key))
              }
            >
              Select all
            </button>
            <span className="text-muted-foreground">·</span>
            <button
              type="button"
              className="text-muted-foreground hover:text-foreground"
              onClick={() => setSources([])}
            >
              Clear
            </button>
          </div>
        </div>
        <ScrollArea className="h-56 rounded-md border">
          <div className="grid grid-cols-1 gap-x-4 gap-y-2 p-3 sm:grid-cols-2 lg:grid-cols-3">
            {availableSources.map((source) => {
              const checked = sources.includes(source.key);
              return (
                <label
                  key={source.key}
                  className="flex cursor-pointer items-start gap-2 rounded px-2 py-1.5 text-sm hover:bg-accent"
                >
                  <Checkbox
                    checked={checked}
                    onCheckedChange={(value) =>
                      toggleSource(source.key, Boolean(value))
                    }
                    className="mt-0.5"
                  />
                  <span className="flex flex-col">
                    <span className="font-medium leading-tight">
                      {source.label}
                    </span>
                    {source.note ? (
                      <span className="text-xs text-muted-foreground leading-tight">
                        {source.note}
                      </span>
                    ) : null}
                  </span>
                </label>
              );
            })}
          </div>
        </ScrollArea>
      </div>

      <div className="flex items-center justify-end gap-3">
        <span className="text-xs text-muted-foreground">
          {availableSources.length} source
          {availableSources.length === 1 ? "" : "s"} available
        </span>
        <Button
          type="submit"
          disabled={loading || !query.trim() || sources.length === 0}
        >
          {loading ? "Searching..." : "Search"}
        </Button>
      </div>
    </form>
  );
}
