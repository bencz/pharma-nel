"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { User, FileText, Pill, ChevronRight, Loader2, Mail } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useProfiles } from "@/hooks/use-profiles";
import type { ProfileSummary } from "@/types";

interface ProfilesGridProps {
  limit?: number;
}

function ProfileCard({
  profile,
  index,
  onSelect,
}: {
  profile: ProfileSummary;
  index: number;
  onSelect: (id: string) => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
    >
      <button
        onClick={() => onSelect(profile.key)}
        className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors text-left group"
      >
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-500/10 flex-shrink-0">
          <User className="h-4 w-4 text-blue-600" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium truncate">
              {profile.full_name ?? "Unknown"}
            </span>
            {profile.credentials.length > 0 && (
              <Badge variant="secondary" className="text-xs">
                {profile.credentials[0]}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs text-muted-foreground mt-0.5">
            <span className="flex items-center gap-1">
              <FileText className="h-3 w-3" />
              {profile.extraction_count} resumes
            </span>
            <span className="flex items-center gap-1">
              <Pill className="h-3 w-3" />
              {profile.substance_count} substances
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
          <Skeleton className="h-9 w-9 rounded-full" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-24" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function ProfilesGrid({ limit = 10 }: ProfilesGridProps) {
  const router = useRouter();
  const { data, isLoading, error } = useProfiles(limit);

  const profiles = data?.data?.profiles ?? [];

  const handleSelectProfile = (profileId: string) => {
    router.push(`/profile/${profileId}`);
  };

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error || !data?.success) {
    return (
      <p className="text-sm text-muted-foreground text-center py-8">
        Failed to load profiles
      </p>
    );
  }

  if (profiles.length === 0) {
    return (
      <div className="text-center py-8">
        <User className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
        <p className="text-sm text-muted-foreground">No professionals yet</p>
        <p className="text-xs text-muted-foreground mt-1">Upload resumes to build profiles</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {profiles.map((profile, index) => (
        <ProfileCard
          key={profile.key}
          profile={profile}
          index={index}
          onSelect={handleSelectProfile}
        />
      ))}
    </div>
  );
}
