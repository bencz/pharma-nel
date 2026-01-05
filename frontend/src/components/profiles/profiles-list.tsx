"use client";

import { motion } from "framer-motion";
import { User, FileText, Pill, ChevronRight, Loader2, Mail } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useProfiles } from "@/hooks/use-profiles";
import type { ProfileSummary } from "@/types";

interface ProfilesListProps {
  onSelectProfile: (profileId: string) => void;
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
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Card
        className="group cursor-pointer transition-all duration-200 hover:shadow-md hover:border-blue-500/50"
        onClick={() => onSelect(profile.key)}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3 flex-1 min-w-0">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-500/10 flex-shrink-0">
                <User className="h-5 w-5 text-blue-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">
                  {profile.full_name ?? "Unknown"}
                </p>

                {profile.credentials.length > 0 && (
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {profile.credentials.map((cred) => (
                      <Badge key={cred} variant="secondary" className="text-xs">
                        {cred}
                      </Badge>
                    ))}
                  </div>
                )}

                {profile.email && (
                  <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                    <Mail className="h-3 w-3" />
                    <span className="truncate">{profile.email}</span>
                  </div>
                )}

                <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <FileText className="h-3 w-3" />
                    {profile.extraction_count} {profile.extraction_count === 1 ? "resume" : "resumes"}
                  </div>
                  <div className="flex items-center gap-1">
                    <Pill className="h-3 w-3" />
                    {profile.substance_count} substances
                  </div>
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
              <Skeleton className="h-10 w-10 rounded-full" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-24" />
                <Skeleton className="h-3 w-40" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export function ProfilesList({ onSelectProfile }: ProfilesListProps) {
  const { data, isLoading, error } = useProfiles(50);

  const profiles = data?.data?.profiles ?? [];

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          <h3 className="text-lg font-semibold">Loading professionals...</h3>
        </div>
        <LoadingSkeleton />
      </div>
    );
  }

  if (error || !data?.success) {
    return null;
  }

  if (profiles.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <User className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold">Pharmaceutical Professionals</h3>
        </div>
        <span className="text-sm text-muted-foreground">
          {profiles.length} {profiles.length === 1 ? "profile" : "profiles"}
        </span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {profiles.map((profile, index) => (
          <ProfileCard
            key={profile.key}
            profile={profile}
            index={index}
            onSelect={onSelectProfile}
          />
        ))}
      </div>
    </div>
  );
}
