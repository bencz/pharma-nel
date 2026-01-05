"use client";

import { X, User, Mail, Phone, Linkedin, FileText, Pill, Building2, Syringe, AlertTriangle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useProfileById } from "@/hooks/use-profiles";
import type { ProfileSubstanceSummary, ProfileExtractionSummary } from "@/types";

interface ProfileDetailPanelProps {
  profileId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onSelectSubstance?: (substanceId: string) => void;
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-16 w-16 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-4 w-24" />
        </div>
      </div>
      <Skeleton className="h-20 w-full" />
      <div className="space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>
    </div>
  );
}

function ExtractionCard({ extraction }: { extraction: ProfileExtractionSummary }) {
  const statusColors: Record<string, string> = {
    completed: "bg-emerald-500/10 text-emerald-700 border-emerald-500/20",
    processing: "bg-blue-500/10 text-blue-700 border-blue-500/20",
    failed: "bg-red-500/10 text-red-700 border-red-500/20",
  };

  return (
    <Card className="bg-muted/30">
      <CardContent className="p-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            <span className="text-sm font-medium truncate">{extraction.filename}</span>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <Badge variant="outline" className={statusColors[extraction.status] ?? ""}>
              {extraction.status}
            </Badge>
            <Badge variant="secondary" className="text-xs">
              {extraction.total_entities} entities
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function SubstanceCard({
  substance,
  onSelect,
}: {
  substance: ProfileSubstanceSummary;
  onSelect?: (id: string) => void;
}) {
  return (
    <Card
      className={`bg-muted/30 ${onSelect ? "cursor-pointer hover:bg-muted/50 transition-colors" : ""}`}
      onClick={() => onSelect?.(substance.key)}
    >
      <CardContent className="p-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <Pill className="h-4 w-4 text-emerald-600 flex-shrink-0" />
              <span className="font-medium truncate capitalize">{substance.name}</span>
              {substance.is_enriched && (
                <Badge variant="secondary" className="text-xs">Enriched</Badge>
              )}
            </div>

            {substance.pharm_classes.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {substance.pharm_classes.slice(0, 3).map((pc) => (
                  <Badge key={pc.key} variant="outline" className="text-xs">
                    {pc.name}
                  </Badge>
                ))}
                {substance.pharm_classes.length > 3 && (
                  <Badge variant="secondary" className="text-xs">
                    +{substance.pharm_classes.length - 3}
                  </Badge>
                )}
              </div>
            )}

            <div className="flex flex-wrap gap-2 mt-2 text-xs text-muted-foreground">
              {substance.routes.length > 0 && (
                <div className="flex items-center gap-1">
                  <Syringe className="h-3 w-3" />
                  {substance.routes.map((r) => r.name).join(", ")}
                </div>
              )}
              {substance.manufacturers.length > 0 && substance.manufacturers[0] && (
                <div className="flex items-center gap-1">
                  <Building2 className="h-3 w-3" />
                  {substance.manufacturers[0].name}
                  {substance.manufacturers.length > 1 && ` +${substance.manufacturers.length - 1}`}
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function ProfileDetailPanel({
  profileId,
  isOpen,
  onClose,
  onSelectSubstance,
}: ProfileDetailPanelProps) {
  const { data, isLoading, error } = useProfileById(profileId);

  const profileData = data?.data;

  return (
    <AnimatePresence>
      {isOpen && profileId && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
            onClick={onClose}
          />
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 z-50 h-full w-full max-w-2xl border-l bg-background shadow-2xl lg:top-16 lg:h-[calc(100vh-4rem)]"
          >
            <div className="flex h-full flex-col">
              <div className="flex items-center justify-between border-b px-6 py-4">
                <h2 className="text-lg font-semibold">Professional Profile</h2>
                <Button variant="ghost" size="icon" onClick={onClose}>
                  <X className="h-5 w-5" />
                </Button>
              </div>

              <ScrollArea className="flex-1 overflow-y-auto">
                {isLoading ? (
                  <LoadingSkeleton />
                ) : error ? (
                  <div className="flex flex-col items-center justify-center p-6 text-center">
                    <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
                    <p className="text-lg font-medium">Failed to load profile</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Please try again later
                    </p>
                  </div>
                ) : profileData ? (
                  <div className="p-6 space-y-6">
                    <div className="flex items-start gap-4">
                      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-500/10 flex-shrink-0">
                        <User className="h-8 w-8 text-blue-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-2xl font-bold">
                          {profileData.profile.full_name ?? "Unknown"}
                        </h3>
                        {profileData.profile.credentials.length > 0 && (
                          <div className="flex gap-1 mt-1 flex-wrap">
                            {profileData.profile.credentials.map((cred) => (
                              <Badge key={cred} variant="secondary">
                                {cred}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      {profileData.profile.email && (
                        <div className="flex items-center gap-2 text-sm">
                          <Mail className="h-4 w-4 text-muted-foreground" />
                          <a
                            href={`mailto:${profileData.profile.email}`}
                            className="text-blue-600 hover:underline truncate"
                          >
                            {profileData.profile.email}
                          </a>
                        </div>
                      )}
                      {profileData.profile.phone && (
                        <div className="flex items-center gap-2 text-sm">
                          <Phone className="h-4 w-4 text-muted-foreground" />
                          <span>{profileData.profile.phone}</span>
                        </div>
                      )}
                      {profileData.profile.linkedin && (
                        <div className="flex items-center gap-2 text-sm col-span-2">
                          <Linkedin className="h-4 w-4 text-muted-foreground" />
                          <a
                            href={profileData.profile.linkedin}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline truncate"
                          >
                            {profileData.profile.linkedin}
                          </a>
                        </div>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <Card className="bg-blue-500/5 border-blue-500/20">
                        <CardContent className="p-4 text-center">
                          <p className="text-3xl font-bold text-blue-600">
                            {profileData.stats.total_extractions}
                          </p>
                          <p className="text-sm text-muted-foreground">Resumes Analyzed</p>
                        </CardContent>
                      </Card>
                      <Card className="bg-emerald-500/5 border-emerald-500/20">
                        <CardContent className="p-4 text-center">
                          <p className="text-3xl font-bold text-emerald-600">
                            {profileData.stats.total_substances}
                          </p>
                          <p className="text-sm text-muted-foreground">Substances</p>
                        </CardContent>
                      </Card>
                    </div>

                    <Separator />

                    {profileData.extractions.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                          <FileText className="h-4 w-4" />
                          Analyzed Resumes ({profileData.extractions.length})
                        </h4>
                        <div className="space-y-2">
                          {profileData.extractions.map((extraction) => (
                            <ExtractionCard key={extraction.key} extraction={extraction} />
                          ))}
                        </div>
                      </div>
                    )}

                    {profileData.substances.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                          <Pill className="h-4 w-4" />
                          Pharmaceutical Experience ({profileData.substances.length})
                        </h4>
                        <div className="space-y-2">
                          {profileData.substances.map((substance) => (
                            <SubstanceCard
                              key={substance.key}
                              substance={substance}
                              onSelect={onSelectSubstance}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : null}
              </ScrollArea>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
