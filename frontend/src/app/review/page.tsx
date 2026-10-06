"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ReviewCenter } from "@/components/mastery/ReviewCenter";

export default function ReviewPage() {
  return (
    <div className="container mx-auto p-6 max-w-7xl space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/knowledge">
          <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-slate-600">
            <ArrowLeft className="h-4 w-4" /> Back to Knowledge Dashboard
          </Button>
        </Link>
      </div>
      <ReviewCenter />
    </div>
  );
}
