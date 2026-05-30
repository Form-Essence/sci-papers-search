"use client";

import { useEffect, useRef, useState } from "react";
import { CheckIcon, CopyIcon, PlugIcon } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Tabs, TabsList, TabsPanel, TabsTab } from "@/components/ui/tabs";
import { fetchMcpConfig, type McpConfigResponse } from "@/lib/api";

export function ConnectMcpDialog() {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<McpConfigResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const requestedRef = useRef(false);

  useEffect(() => {
    if (!open || requestedRef.current) return;
    requestedRef.current = true;
    setLoading(true);
    setError(null);
    fetchMcpConfig()
      .then((res) => {
        setData(res);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : String(err));
        requestedRef.current = false;
      })
      .finally(() => {
        setLoading(false);
      });
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={
          <Button variant="outline" size="sm">
            <PlugIcon />
            Connect to MCP
          </Button>
        }
      />
      <DialogContent className="w-[92vw] max-w-3xl gap-5 overflow-hidden">
        <DialogHeader>
          <DialogTitle>Connect to the Paper Search MCP</DialogTitle>
          <DialogDescription>
            Pick your client below and copy the ready-to-use snippet.
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <p className="text-sm text-muted-foreground">Loading configuration…</p>
        ) : error ? (
          <p className="text-sm text-destructive">
            Could not load configuration: {error}
          </p>
        ) : data ? (
          <ConnectTabs data={data} />
        ) : null}
      </DialogContent>
    </Dialog>
  );
}

function ConnectTabs({ data }: { data: McpConfigResponse }) {
  const [activeId, setActiveId] = useState(data.clients[0]?.id ?? "");

  return (
    <div className="flex min-w-0 flex-col gap-4">
      <p className="text-xs text-muted-foreground">
        Endpoint:{" "}
        <code className="rounded bg-muted px-1 py-0.5 font-mono">
          {data.mcp_url}
        </code>
      </p>

      <Tabs
        value={activeId}
        onValueChange={(value) => setActiveId(String(value))}
      >
        <TabsList className="h-auto flex-wrap gap-1">
          {data.clients.map((client) => (
            <TabsTab key={client.id} value={client.id}>
              {client.label}
            </TabsTab>
          ))}
        </TabsList>
        {data.clients.map((client) => (
          <TabsPanel key={client.id} value={client.id} className="min-w-0">
            <SnippetView client={client} />
          </TabsPanel>
        ))}
      </Tabs>
    </div>
  );
}

function SnippetView({
  client,
}: {
  client: McpConfigResponse["clients"][number];
}) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(client.snippet);
      setCopied(true);
      toast.success(`Copied ${client.label} snippet`);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      toast.error("Copy failed", {
        description: err instanceof Error ? err.message : String(err),
      });
    }
  }

  return (
    <div className="flex min-w-0 flex-col gap-2">
      <p className="min-h-16 text-sm text-muted-foreground">
        {client.instructions}
      </p>
      <div className="flex min-w-0 items-center justify-between gap-2 text-xs text-muted-foreground">
        <span className="min-w-0 truncate font-mono">
          {client.filename ?? ""}
        </span>
        <Button variant="ghost" size="xs" onClick={copy}>
          {copied ? <CheckIcon /> : <CopyIcon />}
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>
      <pre className="h-80 w-full overflow-auto whitespace-pre-wrap break-words rounded-lg border border-border bg-muted/60 p-3 text-xs leading-relaxed">
        <code className="font-mono">{client.snippet}</code>
      </pre>
    </div>
  );
}
