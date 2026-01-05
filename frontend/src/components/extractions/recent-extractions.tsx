"use client";

import { motion } from "framer-motion";
import { FileText, User, Clock, Pill, ChevronRight, Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useExtractions } from "@/hooks/use-extractions";
import type { ExtractionSummary } from "@/types/api";

interface RecentExtractionsProps {
  onSelectExtraction: (extractionId: string) => void;
}

function ExtractionCard({
  extraction,
  index,
  onSelect,
}: {
  extraction: ExtractionSummary;
  index: number;
  onSelect: (id: string) => void;
}) {
  const statusColors: Record<string, string> = {
    completed: "bg-emerald-500/10 text-emerald-700 border-emerald-500/20",
    processing: "bg-blue-500/10 text-blue-700 border-blue-500/20",
    failed: "bg-red-500/10 text-red-700 border-red-500/20",
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Card
        className="group cursor-pointer transition-all duration-200 hover:shadow-md hover:border-emerald-500/50"
        onClick={() => onSelect(extraction.key)}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3 flex-1 min-w-0">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted flex-shrink-0">
                <FileText className="h-5 w-5 text-muted-foreground" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <p className="font-medium truncate">{extraction.filename}</p>
                  <Badge
                    variant="outline"
                    className={statusColors[extraction.status] ?? ""}
                  >
                    {extraction.status}
                  </Badge>
                </div>

                {extraction.profile?.full_name && (
                  <div className="flex items-center gap-1 text-sm text-muted-foreground mb-1">
                    <User className="h-3 w-3" />
                    <span className="truncate">{extraction.profile.full_name}</span>
                    {extraction.profile.credentials.length > 0 && (
                      <span className="text-xs">
                        ({extraction.profile.credentials.join(", ")})
                      </span>
                    )}
                  </div>
                )}

                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDate(extraction.created_at)}
                  </div>
                  <div className="flex items-center gap-1">
                    <Pill className="h-3 w-3" />
                    {extraction.total_entities} entities
                  </div>
                  {extraction.therapeutic_areas.length > 0 && (
                    <Badge variant="secondary" className="text-xs">
                      {extraction.therapeutic_areas[0]}
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            <Button
              variant="ghost"
              size="icon"
              className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-3">
      {[...Array(3)].map((_, i) => (
        <Card key={i}>
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Skeleton className="h-10 w-10 rounded-lg" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-3 w-32" />
                <Skeleton className="h-3 w-24" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export function RecentExtractions({ onSelectExtraction }: RecentExtractionsProps) {
  const { data, isLoading, error } = useExtractions(20);

  const extractions = data?.data?.extractions ?? [];

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          <h3 className="text-lg font-semibold">Loading recent resumes...</h3>
        </div>
        <LoadingSkeleton />
      </div>
    );
  }

  if (error || !data?.success) {
    return null;
  }

  if (extractions.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Recent Resumes</h3>
        <span className="text-sm text-muted-foreground">
          {extractions.length} {extractions.length === 1 ? "resume" : "resumes"}
        </span>
      </div>
      <div className="space-y-3">
        {extractions.map((extraction, index) => (
          <ExtractionCard
            key={extraction.key}
            extraction={extraction}
            index={index}
            onSelect={onSelectExtraction}
          />
        ))}
      </div>
    </div>
  );
}
