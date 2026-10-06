"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import { ConceptDetailView } from "@/components/mastery/ConceptDetailView";

export default function ConceptDetailPage() {
  const params = useParams();
  const conceptId = (params?.id as string) || "";

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <ConceptDetailView conceptId={conceptId} />
    </div>
  );
}
