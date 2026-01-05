"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { FileText, User, Clock, Pill, ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useExtractions } from "@/hooks/use-extractions";
import type { ExtractionSummary } from "@/types";

interface RecentExtractionsCompactProps {
  onSelectExtraction?: (extractionId: string) => void;
  limit?: number;
}

function ExtractionRow({
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
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03 }}
    >
      <button
        onClick={() => onSelect(extraction.key)}
        className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors text-left group"
      >
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-muted flex-shrink-0">
          <FileText className="h-4 w-4 text-muted-foreground" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium truncate">{extraction.filename}</span>
            <Badge
              variant="outline"
              className={`text-xs ${statusColors[extraction.status] ?? ""}`}
            >
              {extraction.status}
            </Badge>
          </div>
          <div className="flex items-center gap-3 text-xs text-muted-foreground mt-0.5">
            {extraction.profile?.full_name && (
              <span className="flex items-center gap-1">
                <User className="h-3 w-3" />
                {extraction.profile.full_name}
              </span>
            )}
            <span className="flex items-center gap-1">
              <Pill className="h-3 w-3" />
              {extraction.total_entities}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatDate(extraction.created_at)}
            </span>
          </div>
        </div>

        <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
      </button>
    </motion.div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-2">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-3">
          <Skeleton className="h-9 w-9 rounded-md" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-3 w-32" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function RecentExtractionsCompact({ onSelectExtraction, limit = 10 }: RecentExtractionsCompactProps) {
  const router = useRouter();
  const { data, isLoading, error } = useExtractions(limit);

  const extractions = data?.data?.extractions ?? [];

  const handleSelect = (extractionId: string) => {
    if (onSelectExtraction) {
      onSelectExtraction(extractionId);
    } else {
      router.push(`/extraction/${extractionId}`);
    }
  };

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error || !data?.success) {
    return (
      <p className="text-sm text-muted-foreground text-center py-8">
        Failed to load recent extractions
      </p>
    );
  }

  if (extractions.length === 0) {
    return (
      <div className="text-center py-8">
        <FileText className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
        <p className="text-sm text-muted-foreground">No extractions yet</p>
        <p className="text-xs text-muted-foreground mt-1">Upload a resume to get started</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {extractions.map((extraction, index) => (
        <ExtractionRow
          key={extraction.key}
          extraction={extraction}
          index={index}
          onSelect={handleSelect}
        />
      ))}
    </div>
  );
}
