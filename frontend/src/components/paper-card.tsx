"use client";

import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { downloadPaper, type Paper } from "@/lib/api";

type Props = {
  paper: Paper;
};

function formatAuthors(authors: string): string {
  if (!authors) return "Unknown authors";
  const parts = authors.split(";").map((s) => s.trim()).filter(Boolean);
  if (parts.length <= 4) return parts.join(", ");
  return `${parts.slice(0, 4).join(", ")} +${parts.length - 4} more`;
}

function formatDate(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso.slice(0, 10);
  return d.toISOString().slice(0, 10);
}

export function PaperCard({ paper }: Props) {
  const [downloading, setDownloading] = useState(false);

  async function handleDownload() {
    setDownloading(true);
    const toastId = toast.loading(
      `Downloading "${paper.title.slice(0, 60)}..."`,
    );
    try {
      const res = await downloadPaper({
        source: paper.source,
        paper_id: paper.paper_id,
        doi: paper.doi,
        title: paper.title,
        use_scihub: false,
      });
      if (res.ok) {
        toast.success("Saved", {
          id: toastId,
          description: res.path ?? res.message,
        });
      } else {
        toast.error("Download failed", {
          id: toastId,
          description: res.message,
        });
      }
    } catch (err) {
      toast.error("Download error", {
        id: toastId,
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setDownloading(false);
    }
  }

  const date = formatDate(paper.published_date);

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline" className="text-xs uppercase tracking-wide">
            {paper.source || "unknown"}
          </Badge>
          {date ? (
            <span className="text-xs text-muted-foreground">{date}</span>
          ) : null}
          {paper.citations ? (
            <Badge variant="secondary" className="text-xs">
              {paper.citations} citations
            </Badge>
          ) : null}
        </div>
        <CardTitle className="text-base leading-snug">{paper.title}</CardTitle>
        <p className="text-xs text-muted-foreground">
          {formatAuthors(paper.authors)}
        </p>
      </CardHeader>
      <CardContent className="flex-1">
        <p className="line-clamp-6 text-sm text-muted-foreground">
          {paper.abstract || "No abstract available."}
        </p>
        {paper.doi ? (
          <p className="mt-3 text-[11px] font-mono text-muted-foreground break-all">
            DOI: {paper.doi}
          </p>
        ) : null}
      </CardContent>
      <CardFooter className="flex flex-wrap gap-2">
        {paper.url ? (
          <a
            href={paper.url}
            target="_blank"
            rel="noreferrer"
            className={buttonVariants({ variant: "outline", size: "sm" })}
          >
            View page
          </a>
        ) : null}
        {paper.pdf_url ? (
          <a
            href={paper.pdf_url}
            target="_blank"
            rel="noreferrer"
            className={buttonVariants({ variant: "outline", size: "sm" })}
          >
            Open PDF
          </a>
        ) : null}
        <Button
          size="sm"
          onClick={handleDownload}
          disabled={downloading || !paper.paper_id}
        >
          {downloading ? "Downloading..." : "Save PDF locally"}
        </Button>
      </CardFooter>
    </Card>
  );
}
