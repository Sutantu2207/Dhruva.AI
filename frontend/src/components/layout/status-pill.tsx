import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { Activity, AlertTriangle } from "lucide-react";

interface StatusPillProps {
  isOnline: boolean;
  statusText?: string;
}

export function StatusPill({ isOnline, statusText }: StatusPillProps) {
  if (isOnline) {
    return (
      <Badge variant="success" className="flex items-center space-x-1.5 py-1 px-3">
        <Activity className="h-3 w-3 animate-pulse text-emerald-600" />
        <span className="font-mono text-xs">{statusText || "Backend Connected"}</span>
      </Badge>
    );
  }

  return (
    <Badge variant="warning" className="flex items-center space-x-1.5 py-1 px-3">
      <AlertTriangle className="h-3 w-3 text-amber-600" />
      <span className="font-mono text-xs">{statusText || "Awaiting Backend Link"}</span>
    </Badge>
  );
}
