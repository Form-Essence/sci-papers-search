"use client";

import { PaperCard } from "@/components/paper-card";
import { Skeleton } from "@/components/ui/skeleton";
import type { Paper, SearchResponse } from "@/lib/api";

type Props = {
  loading: boolean;
  response: SearchResponse | null;
};

function SkeletonCard() {
  return (
    <div className="flex h-full flex-col gap-3 rounded-xl border bg-card p-5 shadow-sm">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-5 w-4/5" />
      <Skeleton className="h-4 w-2/3" />
      <div className="mt-2 space-y-2">
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-5/6" />
        <Skeleton className="h-3 w-4/6" />
      </div>
      <div className="mt-auto flex gap-2 pt-4">
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-8 w-24" />
      </div>
    </div>
  );
}

export function ResultsGrid({ loading, response }: Props) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (!response) {
    return (
      <div className="flex h-48 items-center justify-center rounded-xl border border-dashed text-sm text-muted-foreground">
        Enter a query above to search across the selected academic sources.
      </div>
    );
  }

  if (response.papers.length === 0) {
    return (
      <div className="flex h-48 flex-col items-center justify-center gap-2 rounded-xl border border-dashed text-sm text-muted-foreground">
        <p>No results for &quot;{response.query}&quot;.</p>
        {Object.keys(response.errors).length > 0 ? (
          <p className="text-xs">
            Errors on: {Object.keys(response.errors).join(", ")}
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <span>
          {response.total} deduplicated result
          {response.total === 1 ? "" : "s"}
          {response.raw_total !== response.total
            ? ` (of ${response.raw_total} total)`
            : ""}
        </span>
        {response.sources_used.map((src) => (
          <span
            key={src}
            className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px]"
          >
            {src}: {response.source_results[src] ?? 0}
          </span>
        ))}
        {Object.entries(response.errors).map(([src, err]) => (
          <span
            key={src}
            className="rounded bg-destructive/10 px-1.5 py-0.5 text-[10px] text-destructive"
            title={err}
          >
            {src}: error
          </span>
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {response.papers.map((paper: Paper, idx) => (
          <PaperCard
            key={`${paper.source}:${paper.paper_id || paper.doi || idx}`}
            paper={paper}
          />
        ))}
      </div>
    </div>
  );
}
