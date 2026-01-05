"use client";

import { motion } from "framer-motion";
import { User, Pill, ArrowRight, ExternalLink, Sparkles, AlertCircle, Mail, Phone, FileText, Hash } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useExtractionStore } from "@/store/extraction-store";
import type { ExtractAndEnrichDataResponse, EntityNELResponse } from "@/types";

interface ExtractionResultsProps {
  data: ExtractAndEnrichDataResponse;
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
  index,
  onSelect,
  isSelected,
}: {
  entity: EntityNELResponse;
  index: number;
  onSelect: (entity: EntityNELResponse) => void;
  isSelected: boolean;
}) {
  const hasSubstance = !!entity.substance_id;
  const isClickable = hasSubstance;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Card
        className={`group transition-all duration-200 ${
          isClickable ? "cursor-pointer hover:shadow-md" : "cursor-default"
        } ${
          isSelected
            ? "ring-2 ring-emerald-500 shadow-lg"
            : isClickable ? "hover:border-emerald-500/50" : ""
        }`}
        onClick={() => isClickable && onSelect(entity)}
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

              <h3 className="font-semibold text-foreground truncate">{entity.name}</h3>

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

              {!hasSubstance && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Detailed information not available for this entity
                </p>
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
    </motion.div>
  );
}

export function ExtractionResults({ data }: ExtractionResultsProps) {
  const { selectedEntity, setSelectedEntity } = useExtractionStore();

  const groupedEntities = data.entities.reduce(
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

  const enrichedCount = data.entities.filter((e) => e.substance_id).length;

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-3">
        {data.profile && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="lg:col-span-1"
          >
            <Card className="h-full">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <User className="h-4 w-4 text-blue-600" />
                  Professional
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-500/10 flex-shrink-0">
                    <User className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold truncate">
                      {data.profile.full_name ?? "Unknown"}
                    </p>
                    {data.profile.credentials.length > 0 && (
                      <div className="flex gap-1 mt-1 flex-wrap">
                        {data.profile.credentials.map((cred) => (
                          <Badge key={cred} variant="secondary" className="text-xs">
                            {cred}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <Separator />

                <div className="space-y-2 text-sm">
                  {data.profile.email && (
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Mail className="h-3.5 w-3.5 flex-shrink-0" />
                      <span className="truncate">{data.profile.email}</span>
                    </div>
                  )}
                  {data.profile.phone && (
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Phone className="h-3.5 w-3.5 flex-shrink-0" />
                      <span>{data.profile.phone}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Hash className="h-3.5 w-3.5 flex-shrink-0" />
                    <span className="font-mono text-xs">{data.extraction_id.slice(0, 12)}...</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className={data.profile ? "lg:col-span-2" : "lg:col-span-3"}
        >
          <Card className="h-full">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Pill className="h-4 w-4 text-emerald-600" />
                  Pharmaceutical Experience
                </CardTitle>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Badge variant="outline">{data.entities.length} entities</Badge>
                  <Badge variant="secondary" className="gap-1">
                    <Sparkles className="h-3 w-3" />
                    {enrichedCount} enriched
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 sm:grid-cols-2">
                {Object.entries(groupedEntities).map(([type, entities]) => (
                  <div key={type} className="flex items-center justify-between p-2 rounded-md bg-muted/50">
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className={`${entityTypeColors[type] ?? "bg-gray-500/10 text-gray-700"} text-xs`}
                      >
                        {type}
                      </Badge>
                    </div>
                    <span className="text-sm font-medium">{entities.length}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Extracted Entities</h2>
        <span className="text-sm text-muted-foreground">
          Click on enriched entities to view details
        </span>
      </div>

      <div className="space-y-6">
        {Object.entries(groupedEntities).map(([type, entities]) => (
          <div key={type} className="space-y-3">
            <div className="flex items-center gap-2">
              <Badge
                variant="outline"
                className={`${entityTypeColors[type] ?? "bg-gray-500/10 text-gray-700"} text-sm`}
              >
                {type}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {entities.length} {entities.length === 1 ? "entity" : "entities"}
              </span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {entities.map((entity, index) => (
                <EntityCard
                  key={`${entity.name}-${index}`}
                  entity={entity}
                  index={index}
                  onSelect={setSelectedEntity}
                  isSelected={selectedEntity?.name === entity.name}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
