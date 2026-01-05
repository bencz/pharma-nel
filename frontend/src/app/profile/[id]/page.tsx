"use client";

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  User,
  Mail,
  Phone,
  Linkedin,
  FileText,
  Pill,
  Building2,
  Syringe,
  ArrowLeft,
  AlertTriangle,
  Sparkles,
  ChevronRight,
  FlaskConical,
  Activity,
  Beaker,
  Factory,
  Target,
  Menu,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { SubstanceDetailsPanel } from "@/components/substance/substance-details-panel";
import { useProfileById } from "@/hooks/use-profiles";
import { useExtractionStore } from "@/store/extraction-store";
import type { ProfileSubstanceSummary, ProfileExtractionSummary } from "@/types";

interface PageProps {
  params: Promise<{ id: string }>;
}

function LoadingSkeleton() {
  return (
    <div className="flex h-[calc(100vh-4rem)]">
      <div className="w-72 border-r p-4 space-y-4">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
      <div className="flex-1 p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-48" />
          ))}
        </div>
      </div>
    </div>
  );
}

function ExtractionItem({ extraction }: { extraction: ProfileExtractionSummary }) {
  const statusColors: Record<string, string> = {
    completed: "text-emerald-600",
    processing: "text-blue-600",
    failed: "text-red-600",
  };

  return (
    <div className="flex items-center gap-2 p-2 rounded-md hover:bg-muted/50 transition-colors text-sm">
      <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="truncate font-medium">{extraction.filename}</p>
        <p className="text-xs text-muted-foreground">
          {extraction.total_entities} entities
        </p>
      </div>
      <div className={`w-2 h-2 rounded-full ${statusColors[extraction.status] ? "bg-current " + statusColors[extraction.status] : "bg-gray-400"}`} />
    </div>
  );
}

function SubstanceRow({
  substance,
  onSelect,
}: {
  substance: ProfileSubstanceSummary;
  onSelect: (id: string) => void;
}) {
  const drugCount = substance.drugs?.length ?? 0;
  const manufacturerCount = substance.manufacturers?.length ?? 0;

  return (
    <Card
      className="cursor-pointer hover:shadow-md hover:border-emerald-500/30 transition-all"
      onClick={() => onSelect(substance.key)}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10 flex-shrink-0">
              <FlaskConical className="h-5 w-5 text-emerald-600" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold capitalize truncate">{substance.name}</h3>
                {substance.is_enriched && (
                  <Badge variant="secondary" className="gap-1 text-xs flex-shrink-0">
                    <Sparkles className="h-3 w-3" />
                    Enriched
                  </Badge>
                )}
              </div>
              
              {substance.unii && (
                <p className="text-xs text-muted-foreground font-mono mt-0.5">
                  UNII: {substance.unii}
                </p>
              )}

              {substance.pharm_classes.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {substance.pharm_classes.slice(0, 2).map((pc) => (
                    <Badge key={pc.key} variant="outline" className="text-xs max-w-full">
                      <span className="truncate">{pc.name}</span>
                    </Badge>
                  ))}
                  {substance.pharm_classes.length > 2 && (
                    <Badge variant="secondary" className="text-xs">
                      +{substance.pharm_classes.length - 2}
                    </Badge>
                  )}
                </div>
              )}
            </div>
          </div>

          <ChevronRight className="h-5 w-5 text-muted-foreground flex-shrink-0" />
        </div>

        <Separator className="my-3" />

        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <p className="text-lg font-bold">{drugCount}</p>
            <p className="text-xs text-muted-foreground">Drugs</p>
          </div>
          <div>
            <p className="text-lg font-bold">{substance.routes.length}</p>
            <p className="text-xs text-muted-foreground">Routes</p>
          </div>
          <div>
            <p className="text-lg font-bold">{substance.dosage_forms.length}</p>
            <p className="text-xs text-muted-foreground">Forms</p>
          </div>
          <div>
            <p className="text-lg font-bold">{manufacturerCount}</p>
            <p className="text-xs text-muted-foreground">Mfrs</p>
          </div>
        </div>

        {(substance.routes.length > 0 || substance.manufacturers.length > 0) && (
          <div className="mt-3 space-y-1 text-xs text-muted-foreground">
            {substance.routes.length > 0 && (
              <div className="flex items-center gap-1">
                <Syringe className="h-3 w-3 flex-shrink-0" />
                <span className="truncate">{substance.routes.map((r) => r.name).join(", ")}</span>
              </div>
            )}
            {substance.manufacturers.length > 0 && substance.manufacturers[0] && (
              <div className="flex items-center gap-1">
                <Building2 className="h-3 w-3 flex-shrink-0" />
                <span className="truncate">
                  {substance.manufacturers[0].name}
                  {substance.manufacturers.length > 1 && ` +${substance.manufacturers.length - 1}`}
                </span>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function ProfilePage({ params }: PageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { data, isLoading, error } = useProfileById(id);
  const { setSelectedSubstanceId, setSelectedExtractionId } = useExtractionStore();

  const profileData = data?.data;

  const handleSelectSubstance = (substanceId: string) => {
    setSelectedSubstanceId(substanceId);
  };

  const handleExtractionClick = (extractionKey: string) => {
    router.push(`/extraction/${extractionKey}`);
  };

  if (isLoading) {
    return (
      <div className="min-h-[calc(100vh-8rem)]">
        <div className="mx-auto w-full max-w-screen-xl px-4 md:px-8 py-8">
          <LoadingSkeleton />
        </div>
      </div>
    );
  }

  if (error || !profileData) {
    return (
      <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center">
        <div className="text-center space-y-4">
          <AlertTriangle className="h-16 w-16 text-destructive mx-auto" />
          <h1 className="text-2xl font-bold">Profile Not Found</h1>
          <p className="text-muted-foreground">The requested profile could not be loaded.</p>
          <Button onClick={() => router.push("/")}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Home
          </Button>
        </div>
      </div>
    );
  }

  const { profile, extractions, substances, stats } = profileData;

  const aggregatedData = {
    routes: [...new Set(substances.flatMap(s => s.routes.map(r => r.name)))],
    pharmClasses: [...new Set(substances.flatMap(s => s.pharm_classes.map(c => c.name)))],
    manufacturers: [...new Set(substances.flatMap(s => s.manufacturers.map(m => m.name)))],
    therapeuticAreas: [...new Set(extractions.flatMap(e => e.therapeutic_areas ?? []))],
    totalDrugs: substances.reduce((acc, s) => acc + (s.drugs?.length ?? 0), 0),
  };

  return (
    <div className="min-h-[calc(100vh-4rem)]">
      <div className="sticky top-16 z-10 bg-muted/95 backdrop-blur supports-[backdrop-filter]:bg-muted/60 border-b">
        <div className="px-4 py-3">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.back()}
              className="flex-shrink-0"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex-shrink-0">
              <User className="h-5 w-5 text-white" />
            </div>
            <div className="min-w-0 flex-1">
              <h1 className="font-bold truncate">
                {profile.full_name ?? "Unknown"}
              </h1>
              <div className="flex flex-wrap gap-1 mt-0.5">
                {profile.credentials.map((cred) => (
                  <Badge key={cred} variant="secondary" className="text-xs">
                    {cred}
                  </Badge>
                ))}
              </div>
            </div>
            <div className="hidden sm:flex items-center gap-4 text-sm text-muted-foreground">
              <div className="text-center">
                <p className="font-bold text-foreground">{stats.total_extractions}</p>
                <p className="text-xs">Docs</p>
              </div>
              <div className="text-center">
                <p className="font-bold text-foreground">{stats.total_substances}</p>
                <p className="text-xs">Substances</p>
              </div>
              <div className="text-center">
                <p className="font-bold text-foreground">{aggregatedData.totalDrugs}</p>
                <p className="text-xs">Drugs</p>
              </div>
            </div>

            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="lg:hidden flex-shrink-0">
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-[320px] sm:w-[400px]">
                <SheetHeader>
                  <SheetTitle>Profile Details</SheetTitle>
                </SheetHeader>
                <ScrollArea className="h-[calc(100vh-80px)] mt-4">
                  <div className="space-y-6 pr-4">
                    <div className="space-y-2 text-sm">
                      {profile.email && (
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <Mail className="h-3.5 w-3.5 flex-shrink-0" />
                          <span className="truncate">{profile.email}</span>
                        </div>
                      )}
                      {profile.phone && (
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <Phone className="h-3.5 w-3.5 flex-shrink-0" />
                          <span>{profile.phone}</span>
                        </div>
                      )}
                      {profile.linkedin && (
                        <a
                          href={profile.linkedin}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 text-blue-600 hover:underline"
                        >
                          <Linkedin className="h-3.5 w-3.5 flex-shrink-0" />
                          LinkedIn
                        </a>
                      )}
                    </div>

                    <Separator />

                    <div className="grid grid-cols-2 gap-2">
                      <div className="p-2 rounded-lg bg-muted border text-center">
                        <p className="text-lg font-bold">{stats.total_extractions}</p>
                        <p className="text-xs text-muted-foreground">Docs</p>
                      </div>
                      <div className="p-2 rounded-lg bg-muted border text-center">
                        <p className="text-lg font-bold">{stats.total_substances}</p>
                        <p className="text-xs text-muted-foreground">Substances</p>
                      </div>
                      <div className="p-2 rounded-lg bg-muted border text-center">
                        <p className="text-lg font-bold">{aggregatedData.totalDrugs}</p>
                        <p className="text-xs text-muted-foreground">Drugs</p>
                      </div>
                      <div className="p-2 rounded-lg bg-muted border text-center">
                        <p className="text-lg font-bold">{aggregatedData.manufacturers.length}</p>
                        <p className="text-xs text-muted-foreground">Mfrs</p>
                      </div>
                    </div>

                    {aggregatedData.therapeuticAreas.length > 0 && (
                      <>
                        <Separator />
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <Target className="h-4 w-4 text-rose-600" />
                            <span className="text-xs font-medium">Therapeutic Areas</span>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {aggregatedData.therapeuticAreas.map((area) => (
                              <Badge key={area} variant="outline" className="capitalize text-xs bg-rose-500/5 text-rose-700 border-rose-500/20">
                                {area}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </>
                    )}

                    {aggregatedData.routes.length > 0 && (
                      <>
                        <Separator />
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <Syringe className="h-4 w-4 text-cyan-600" />
                            <span className="text-xs font-medium">Routes</span>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {aggregatedData.routes.map((route) => (
                              <Badge key={route} variant="outline" className="capitalize text-xs bg-cyan-500/5 text-cyan-700 border-cyan-500/20">
                                {route.toLowerCase()}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </>
                    )}

                    {aggregatedData.pharmClasses.length > 0 && (
                      <>
                        <Separator />
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <Beaker className="h-4 w-4 text-violet-600" />
                            <span className="text-xs font-medium">Pharm Classes</span>
                            <Badge variant="secondary" className="text-xs ml-auto">
                              {aggregatedData.pharmClasses.length}
                            </Badge>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {aggregatedData.pharmClasses.slice(0, 6).map((cls) => (
                              <Badge key={cls} variant="outline" className="text-xs bg-violet-500/5 text-violet-700 border-violet-500/20">
                                {cls.replace(/\s*\[.*?\]\s*/g, "")}
                              </Badge>
                            ))}
                            {aggregatedData.pharmClasses.length > 6 && (
                              <Badge variant="secondary" className="text-xs">
                                +{aggregatedData.pharmClasses.length - 6}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </>
                    )}

                    <Separator />

                    <div>
                      <h3 className="text-sm font-medium mb-2 flex items-center gap-2">
                        <FileText className="h-4 w-4 text-blue-600" />
                        Documents
                      </h3>
                      {extractions.length > 0 ? (
                        <div className="space-y-1">
                          {extractions.map((extraction) => (
                            <div
                              key={extraction.key}
                              onClick={() => handleExtractionClick(extraction.key)}
                              className="cursor-pointer"
                            >
                              <ExtractionItem extraction={extraction} />
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-muted-foreground">No documents</p>
                      )}
                    </div>
                  </div>
                </ScrollArea>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row">
        <aside className="hidden lg:flex w-[320px] xl:w-[380px] 2xl:w-[420px] flex-shrink-0 border-r bg-muted/20 flex-col h-[calc(100vh-4rem-73px)] sticky top-[137px]">
          <ScrollArea className="flex-1">
            <div className="p-4 space-y-6">
              <div className="space-y-2 text-sm">
                {profile.email && (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Mail className="h-3.5 w-3.5 flex-shrink-0" />
                    <span className="truncate">{profile.email}</span>
                  </div>
                )}
                {profile.phone && (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Phone className="h-3.5 w-3.5 flex-shrink-0" />
                    <span>{profile.phone}</span>
                  </div>
                )}
                {profile.linkedin && (
                  <a
                    href={profile.linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-blue-600 hover:underline"
                  >
                    <Linkedin className="h-3.5 w-3.5 flex-shrink-0" />
                    LinkedIn
                  </a>
                )}
              </div>

              <Separator />

              <div className="grid grid-cols-2 gap-2">
              <div className="p-2 rounded-lg bg-background border text-center">
                <p className="text-lg font-bold">{stats.total_extractions}</p>
                <p className="text-xs text-muted-foreground">Docs</p>
              </div>
              <div className="p-2 rounded-lg bg-background border text-center">
                <p className="text-lg font-bold">{stats.total_substances}</p>
                <p className="text-xs text-muted-foreground">Substances</p>
              </div>
              <div className="p-2 rounded-lg bg-background border text-center">
                <p className="text-lg font-bold">{aggregatedData.totalDrugs}</p>
                <p className="text-xs text-muted-foreground">Drugs</p>
              </div>
              <div className="p-2 rounded-lg bg-background border text-center">
                <p className="text-lg font-bold">{aggregatedData.manufacturers.length}</p>
                <p className="text-xs text-muted-foreground">Mfrs</p>
              </div>
            </div>

            {aggregatedData.therapeuticAreas.length > 0 && (
              <>
                <Separator />
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Target className="h-4 w-4 text-rose-600" />
                    <span className="text-xs font-medium">Therapeutic Areas</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {aggregatedData.therapeuticAreas.map((area) => (
                      <Badge key={area} variant="outline" className="capitalize text-xs bg-rose-500/5 text-rose-700 border-rose-500/20">
                        {area}
                      </Badge>
                    ))}
                  </div>
                </div>
              </>
            )}

            {aggregatedData.routes.length > 0 && (
              <>
                <Separator />
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Syringe className="h-4 w-4 text-cyan-600" />
                    <span className="text-xs font-medium">Routes</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {aggregatedData.routes.map((route) => (
                      <Badge key={route} variant="outline" className="capitalize text-xs bg-cyan-500/5 text-cyan-700 border-cyan-500/20">
                        {route.toLowerCase()}
                      </Badge>
                    ))}
                  </div>
                </div>
              </>
            )}

            {aggregatedData.pharmClasses.length > 0 && (
              <>
                <Separator />
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Beaker className="h-4 w-4 text-violet-600" />
                    <span className="text-xs font-medium">Pharm Classes</span>
                    <Badge variant="secondary" className="text-xs ml-auto">
                      {aggregatedData.pharmClasses.length}
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {aggregatedData.pharmClasses.slice(0, 4).map((cls) => (
                      <Badge key={cls} variant="outline" className="text-xs bg-violet-500/5 text-violet-700 border-violet-500/20">
                        {cls.replace(/\s*\[.*?\]\s*/g, "")}
                      </Badge>
                    ))}
                    {aggregatedData.pharmClasses.length > 4 && (
                      <Badge variant="secondary" className="text-xs">
                        +{aggregatedData.pharmClasses.length - 4}
                      </Badge>
                    )}
                  </div>
                </div>
              </>
            )}

              <Separator />

              <div>
                <h3 className="text-sm font-medium mb-2 flex items-center gap-2">
                  <FileText className="h-4 w-4 text-blue-600" />
                  Documents
                </h3>
                {extractions.length > 0 ? (
                  <div className="space-y-1">
                    {extractions.map((extraction) => (
                      <div
                        key={extraction.key}
                        onClick={() => handleExtractionClick(extraction.key)}
                        className="cursor-pointer"
                      >
                        <ExtractionItem extraction={extraction} />
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">No documents</p>
                )}
              </div>
            </div>
          </ScrollArea>
        </aside>

        <main className="flex-1 min-w-0">
          <div className="p-4 md:p-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    <Pill className="h-5 w-5 text-emerald-600" />
                    Pharmaceutical Experience
                  </h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    {substances.length} substances
                  </p>
                </div>
              </div>

              {substances.length > 0 ? (
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
                  {substances.map((substance) => (
                    <SubstanceRow
                      key={substance.key}
                      substance={substance}
                      onSelect={handleSelectSubstance}
                    />
                  ))}
                </div>
              ) : (
                <Card>
                  <CardContent className="py-12 text-center">
                    <Pill className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">No pharmaceutical experience recorded</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </motion.div>
          </div>
        </main>
      </div>

      <SubstanceDetailsPanel />
    </div>
  );
}
