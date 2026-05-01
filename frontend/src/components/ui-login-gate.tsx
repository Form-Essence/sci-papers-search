"use client";

import {
  createContext,
  type FormEvent,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { LogOutIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { fetchMe, loginUi, logoutUi } from "@/lib/api";

type Phase = "checking" | "login" | "ready";

type UiGateContextValue = {
  showSignOut: boolean;
  signOut: () => void;
};

const UiGateContext = createContext<UiGateContextValue | null>(null);

export function useUiGate(): UiGateContextValue | null {
  return useContext(UiGateContext);
}

export function UiLoginGate({ children }: { children: React.ReactNode }) {
  const [phase, setPhase] = useState<Phase>("checking");
  const [uiGateActive, setUiGateActive] = useState(false);
  const [showUnprotectedHint, setShowUnprotectedHint] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginBusy, setLoginBusy] = useState(false);

  const refreshSession = useCallback(async () => {
    const data = await fetchMe();
    if (data.authenticated) {
      setUiGateActive(data.ui_gate === true);
      setShowUnprotectedHint(data.ui_gate !== true);
      setPhase("ready");
      return true;
    }
    setShowUnprotectedHint(false);
    setPhase("login");
    return false;
  }, []);

  useEffect(() => {
    let cancelled = false;
    const id = window.setTimeout(() => {
      refreshSession().catch(() => {
        if (!cancelled) setPhase("login");
      });
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(id);
    };
  }, [refreshSession]);

  async function onLoginSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoginError(null);
    const form = e.currentTarget;
    const password = String(new FormData(form).get("password") ?? "");
    if (!password.trim()) {
      setLoginError("Enter the server password.");
      return;
    }
    setLoginBusy(true);
    try {
      await loginUi(password);
      form.reset();
      await refreshSession();
    } catch {
      setLoginError("Incorrect password.");
    } finally {
      setLoginBusy(false);
    }
  }

  async function handleSignOut() {
    await logoutUi();
    setUiGateActive(false);
    setPhase("login");
  }

  if (phase === "checking") {
    return (
      <div className="flex min-h-[50vh] flex-1 items-center justify-center text-sm text-muted-foreground">
        Checking access…
      </div>
    );
  }

  if (phase === "login") {
    return (
      <div className="flex min-h-screen flex-1 flex-col items-center justify-center gap-6 px-4 py-12">
        <Card className="w-full max-w-md shadow-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-xl tracking-tight">Paper Search</CardTitle>
            <CardDescription>Enter the server password to continue.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={onLoginSubmit}>
              <div className="space-y-2">
                <Label htmlFor="ui-password">Password</Label>
                <Input
                  id="ui-password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  disabled={loginBusy}
                  required
                />
              </div>
              {loginError ? (
                <p className="text-sm text-destructive" role="alert">
                  {loginError}
                </p>
              ) : null}
              <Button type="submit" className="w-full" disabled={loginBusy}>
                {loginBusy ? "Signing in…" : "Sign in"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <UiGateContext.Provider
      value={{ showSignOut: uiGateActive, signOut: () => void handleSignOut() }}
    >
      {showUnprotectedHint ? (
        <div
          className="border-b border-amber-500/35 bg-amber-500/10 px-4 py-2.5 text-center text-sm text-amber-950 dark:text-amber-50"
          role="status"
        >
          This deployment does not require a UI password yet. Ask whoever runs the server to turn on password protection if you need it.
        </div>
      ) : null}
      {children}
    </UiGateContext.Provider>
  );
}

export function UiSignOutButton() {
  const ctx = useUiGate();
  if (!ctx?.showSignOut) return null;
  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      className="gap-1.5"
      onClick={ctx.signOut}
    >
      <LogOutIcon className="size-4" />
      Sign out
    </Button>
  );
}
