"use client";

import { use } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  User,
  Mail,
  Phone,
  FileText,
  Pill,
  ArrowLeft,
  AlertTriangle,
  Sparkles,
  Hash,
  ArrowRight,
  ExternalLink,
  AlertCircle,
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
import { useExtractionById } from "@/hooks/use-extractions";
import { useExtractionStore } from "@/store/extraction-store";
import type { EntityNELResponse } from "@/types";

interface PageProps {
  params: Promise<{ id: string }>;
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-32 w-full" />
      <div className="grid grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
    </div>
  );
}

const entityTypeColors: Record<string, string> = {
  BRAND: "bg-blue-500/10 text-blue-700 border-blue-500/20",
  GENERIC: "bg-emerald-500/10 text-emerald-700 border-emerald-500/20",
  INGREDIENT: "bg-purple-500/10 text-purple-700 border-purple-500/20",
  CODE: "bg-amber-500/10 text-amber-700 border-amber-500/20",
};

const relationshipLabels: Record<string, string> = {
  IS_ACTIVE_INGREDIENT: "Active Ingredient",
  IS_BRAND_OF: "Brand Of",
  IS_GENERIC_OF: "Generic Of",
  CONTAINS: "Contains",
  SAME_AS: "Same As",
};

function EntityCard({
  entity,
  onSelect,
  isSelected,
}: {
  entity: EntityNELResponse;
  onSelect: (entity: EntityNELResponse) => void;
  isSelected: boolean;
}) {
  const hasSubstance = !!entity.substance_id;

  return (
    <Card
      className={`group transition-all duration-200 ${
        hasSubstance ? "cursor-pointer hover:shadow-md hover:border-emerald-500/50" : ""
      } ${isSelected ? "ring-2 ring-emerald-500 shadow-lg" : ""}`}
      onClick={() => hasSubstance && onSelect(entity)}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <Badge
                variant="outline"
                className={entityTypeColors[entity.type] ?? "bg-gray-500/10 text-gray-700"}
              >
                {entity.type}
              </Badge>
              {hasSubstance ? (
                <Badge variant="secondary" className="gap-1">
                  <Sparkles className="h-3 w-3" />
                  Enriched
                </Badge>
              ) : (
                <Badge variant="outline" className="gap-1 bg-amber-500/10 text-amber-700 border-amber-500/20">
                  <AlertCircle className="h-3 w-3" />
                  Not Available
                </Badge>
              )}
            </div>

            <h3 className="font-semibold truncate">{entity.name}</h3>

            {entity.linked_to && (
              <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
                <ArrowRight className="h-3 w-3 flex-shrink-0" />
                <span className="truncate">{entity.linked_to}</span>
                {entity.relationship && (
                  <Badge variant="outline" className="text-xs flex-shrink-0">
                    {relationshipLabels[entity.relationship] ?? entity.relationship}
                  </Badge>
                )}
              </div>
            )}
          </div>

          {hasSubstance && (
            <Button
              variant="ghost"
              size="icon"
              className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <ExternalLink className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function ExtractionPage({ params }: PageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { data, isLoading, error } = useExtractionById(id);
  const { setSelectedSubstanceId, selectedEntity, setSelectedEntity } = useExtractionStore();

  const extractionData = data?.data;

  const handleSelectEntity = (entity: EntityNELResponse) => {
    setSelectedEntity(entity);
    if (entity.substance_id) {
      setSelectedSubstanceId(entity.substance_id);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-[calc(100vh-4rem)]">
        <div className="mx-auto max-w-screen-2xl px-4 md:px-8 py-6">
          <LoadingSkeleton />
        </div>
      </div>
    );
  }

  if (error || !extractionData) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="text-center space-y-4">
          <AlertTriangle className="h-16 w-16 text-destructive mx-auto" />
          <h1 className="text-2xl font-bold">Extraction Not Found</h1>
          <p className="text-muted-foreground">The requested extraction could not be loaded.</p>
          <Button onClick={() => router.push("/")}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Home
          </Button>
        </div>
      </div>
    );
  }

  const { extraction_id, profile, entities } = extractionData;

  const groupedEntities = entities.reduce(
    (acc, entity) => {
      const type = entity.type;
      if (!acc[type]) {
        acc[type] = [];
      }
      acc[type].push(entity);
      return acc;
    },
    {} as Record<string, EntityNELResponse[]>
  );

  const enrichedCount = entities.filter((e) => e.substance_id).length;

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
            {profile && (
              <>
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
              </>
            )}
            {!profile && (
              <div className="min-w-0 flex-1">
                <h1 className="font-bold">Extraction Results</h1>
              </div>
            )}
            <div className="hidden sm:flex items-center gap-4 text-sm text-muted-foreground">
              <div className="text-center">
                <p className="font-bold text-foreground">{entities.length}</p>
                <p className="text-xs">Entities</p>
              </div>
              <div className="text-center">
                <p className="font-bold text-foreground">{enrichedCount}</p>
                <p className="text-xs">Enriched</p>
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
                  <SheetTitle>Extraction Details</SheetTitle>
                </SheetHeader>
                <ScrollArea className="h-[calc(100vh-80px)] mt-4">
                  <div className="space-y-6 pr-4">
                    {profile && (
                      <>
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
                        </div>
                        <Separator />
                      </>
                    )}

                    <div className="grid grid-cols-2 gap-2">
                      <div className="p-2 rounded-lg bg-muted border text-center">
                        <p className="text-lg font-bold">{entities.length}</p>
                        <p className="text-xs text-muted-foreground">Entities</p>
                      </div>
                      <div className="p-2 rounded-lg bg-muted border text-center">
                        <p className="text-lg font-bold">{enrichedCount}</p>
                        <p className="text-xs text-muted-foreground">Enriched</p>
                      </div>
                    </div>

                    <Separator />

                    <div>
                      <h3 className="text-xs font-medium mb-2 flex items-center gap-2">
                        <Hash className="h-3.5 w-3.5 text-muted-foreground" />
                        Extraction ID
                      </h3>
                      <p className="font-mono text-xs text-muted-foreground break-all">
                        {extraction_id}
                      </p>
                    </div>

                    <Separator />

                    <div>
                      <h3 className="text-xs font-medium mb-2">Entity Types</h3>
                      <div className="space-y-2">
                        {Object.entries(groupedEntities).map(([type, typeEntities]) => (
                          <div key={type} className="flex items-center justify-between">
                            <Badge
                              variant="outline"
                              className={`${entityTypeColors[type] ?? "bg-gray-500/10 text-gray-700"} text-xs`}
                            >
                              {type}
                            </Badge>
                            <span className="text-sm font-medium">{typeEntities.length}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </ScrollArea>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row">
        <aside className="hidden lg:flex w-[280px] xl:w-[320px] flex-shrink-0 border-r bg-muted/20 flex-col h-[calc(100vh-4rem-73px)] sticky top-[137px]">
          <ScrollArea className="flex-1">
            <div className="p-4 space-y-6">
              {profile && (
                <>
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
                  </div>
                  <Separator />
                </>
              )}

              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 rounded-lg bg-background border text-center">
                  <p className="text-lg font-bold">{entities.length}</p>
                  <p className="text-xs text-muted-foreground">Entities</p>
                </div>
                <div className="p-2 rounded-lg bg-background border text-center">
                  <p className="text-lg font-bold">{enrichedCount}</p>
                  <p className="text-xs text-muted-foreground">Enriched</p>
                </div>
              </div>

              <Separator />

              <div>
                <h3 className="text-xs font-medium mb-2 flex items-center gap-2">
                  <Hash className="h-3.5 w-3.5 text-muted-foreground" />
                  Extraction ID
                </h3>
                <p className="font-mono text-xs text-muted-foreground break-all">
                  {extraction_id}
                </p>
              </div>

              <Separator />

              <div>
                <h3 className="text-xs font-medium mb-2">Entity Types</h3>
                <div className="space-y-2">
                  {Object.entries(groupedEntities).map(([type, typeEntities]) => (
                    <div key={type} className="flex items-center justify-between">
                      <Badge
                        variant="outline"
                        className={`${entityTypeColors[type] ?? "bg-gray-500/10 text-gray-700"} text-xs`}
                      >
                        {type}
                      </Badge>
                      <span className="text-sm font-medium">{typeEntities.length}</span>
                    </div>
                  ))}
                </div>
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
                    <FileText className="h-5 w-5 text-blue-600" />
                    Extracted Entities
                  </h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    Click on enriched entities to view details
                  </p>
                </div>
              </div>

              <div className="space-y-6">
                {Object.entries(groupedEntities).map(([type, typeEntities]) => (
                  <div key={type} className="space-y-3">
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className={`${entityTypeColors[type] ?? "bg-gray-500/10 text-gray-700"} text-sm`}
                      >
                        {type}
                      </Badge>
                      <span className="text-sm text-muted-foreground">
                        {typeEntities.length} {typeEntities.length === 1 ? "entity" : "entities"}
                      </span>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
                      {typeEntities.map((entity, index) => (
                        <EntityCard
                          key={`${entity.name}-${index}`}
                          entity={entity}
                          onSelect={handleSelectEntity}
                          isSelected={selectedEntity?.name === entity.name}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
          </div>
        </main>
      </div>

      <SubstanceDetailsPanel />
    </div>
  );
}
