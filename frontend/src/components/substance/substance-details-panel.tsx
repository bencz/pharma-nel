"use client";

import { X, ExternalLink, AlertTriangle, Pill, Building2, Syringe, Package, FileText, Zap, Activity } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { MoleculeViewer } from "./molecule-viewer";
import { useSubstance } from "@/hooks/use-substance";
import { useExtractionStore } from "@/store/extraction-store";
import type { SubstanceProfileData, DrugLabelInfo } from "@/types/api";

function LoadingSkeleton() {
  return (
    <div className="space-y-6 p-6">
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-32" />
      </div>
      <Skeleton className="h-[200px] w-full" />
      <div className="space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
      </div>
    </div>
  );
}

function ChemicalIdentifiers({ substance }: { substance: SubstanceProfileData }) {
  const identifiers = [
    { label: "UNII", value: substance.unii },
    { label: "RxCUI", value: substance.rxcui },
    { label: "CAS", value: substance.cas_number },
    { label: "PubChem", value: substance.pubchem_id },
    { label: "InChI Key", value: substance.inchi_key },
  ].filter((id) => id.value);

  if (identifiers.length === 0) return null;

  return (
    <div className="grid grid-cols-2 gap-3">
      {identifiers.map((id) => (
        <div key={id.label} className="space-y-1">
          <p className="text-xs text-muted-foreground">{id.label}</p>
          <p className="text-sm font-mono">{id.value}</p>
        </div>
      ))}
    </div>
  );
}

function MolecularProperties({ substance }: { substance: SubstanceProfileData }) {
  const properties = [
    { label: "Formula", value: substance.formula },
    { label: "Molecular Weight", value: substance.molecular_weight ? `${substance.molecular_weight} g/mol` : null },
    { label: "Class", value: substance.substance_class },
    { label: "Stereochemistry", value: substance.stereochemistry },
  ].filter((p) => p.value);

  if (properties.length === 0) return null;

  return (
    <div className="grid grid-cols-2 gap-3">
      {properties.map((prop) => (
        <div key={prop.label} className="space-y-1">
          <p className="text-xs text-muted-foreground">{prop.label}</p>
          <p className="text-sm">{prop.value}</p>
        </div>
      ))}
    </div>
  );
}

function DrugsList({ drugs }: { drugs: SubstanceProfileData["drugs"] }) {
  if (drugs.length === 0) {
    return <p className="text-sm text-muted-foreground">No drug products found</p>;
  }

  return (
    <div className="space-y-3">
      {drugs.slice(0, 10).map((drug) => (
        <Card key={drug.key} className="bg-muted/30">
          <CardContent className="p-3">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <p className="font-medium truncate">
                  {drug.brand_names[0] ?? drug.generic_names[0] ?? drug.key}
                </p>
                {drug.generic_names.length > 0 && drug.brand_names.length > 0 && (
                  <p className="text-sm text-muted-foreground truncate">
                    {drug.generic_names[0]}
                  </p>
                )}
              </div>
              <div className="flex gap-1 flex-shrink-0">
                {drug.drug_type && (
                  <Badge variant="outline" className="text-xs">
                    {drug.drug_type}
                  </Badge>
                )}
                {drug.is_enriched && (
                  <Badge variant="secondary" className="text-xs">
                    Enriched
                  </Badge>
                )}
              </div>
            </div>
            {drug.sponsor_name && (
              <p className="text-xs text-muted-foreground mt-1">
                {drug.sponsor_name}
              </p>
            )}
          </CardContent>
        </Card>
      ))}
      {drugs.length > 10 && (
        <p className="text-sm text-muted-foreground text-center">
          +{drugs.length - 10} more drugs
        </p>
      )}
    </div>
  );
}

function LabelSection({ label }: { label: DrugLabelInfo }) {
  const sections = [
    { key: "description", title: "Description", content: label.description },
    { key: "indications", title: "Indications & Usage", content: label.indications_and_usage },
    { key: "dosage", title: "Dosage & Administration", content: label.dosage_and_administration },
    { key: "contraindications", title: "Contraindications", content: label.contraindications },
    { key: "warnings", title: "Warnings & Cautions", content: label.warnings_and_cautions },
    { key: "boxed_warning", title: "Boxed Warning", content: label.boxed_warning },
    { key: "adverse", title: "Adverse Reactions", content: label.adverse_reactions },
    { key: "interactions", title: "Drug Interactions", content: label.drug_interactions },
    { key: "mechanism", title: "Mechanism of Action", content: label.mechanism_of_action },
    { key: "pharmacology", title: "Clinical Pharmacology", content: label.clinical_pharmacology },
  ].filter((s) => s.content);

  if (sections.length === 0) {
    return <p className="text-sm text-muted-foreground">No label information available</p>;
  }

  return (
    <Accordion type="multiple" className="w-full">
      {sections.map((section) => (
        <AccordionItem key={section.key} value={section.key}>
          <AccordionTrigger className="text-sm">
            {section.key === "boxed_warning" && (
              <AlertTriangle className="h-4 w-4 text-destructive mr-2" />
            )}
            {section.title}
          </AccordionTrigger>
          <AccordionContent>
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                {section.content}
              </p>
            </div>
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  );
}

function InteractionsList({ interactions }: { interactions: SubstanceProfileData["interactions"] }) {
  if (interactions.length === 0) {
    return <p className="text-sm text-muted-foreground">No interactions found</p>;
  }

  const severityColors: Record<string, string> = {
    high: "bg-red-500/10 text-red-700 border-red-500/20",
    moderate: "bg-amber-500/10 text-amber-700 border-amber-500/20",
    low: "bg-blue-500/10 text-blue-700 border-blue-500/20",
  };

  return (
    <div className="space-y-3">
      {interactions.slice(0, 15).map((interaction) => (
        <Card key={interaction.key} className="bg-muted/30">
          <CardContent className="p-3">
            <div className="flex items-start gap-2">
              {interaction.severity && (
                <Badge
                  variant="outline"
                  className={severityColors[interaction.severity.toLowerCase()] ?? ""}
                >
                  {interaction.severity}
                </Badge>
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">
                  {interaction.source_drug_name} + {interaction.target_drug_name}
                </p>
                {interaction.description && (
                  <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                    {interaction.description}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
      {interactions.length > 15 && (
        <p className="text-sm text-muted-foreground text-center">
          +{interactions.length - 15} more interactions
        </p>
      )}
    </div>
  );
}

function ReactionsList({ reactions }: { reactions: SubstanceProfileData["reactions"] }) {
  if (reactions.length === 0) {
    return <p className="text-sm text-muted-foreground">No adverse reactions found</p>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {reactions.slice(0, 30).map((reaction) => (
        <Badge key={reaction.key} variant="outline" className="text-xs">
          {reaction.name}
        </Badge>
      ))}
      {reactions.length > 30 && (
        <Badge variant="secondary" className="text-xs">
          +{reactions.length - 30} more
        </Badge>
      )}
    </div>
  );
}

export function SubstanceDetailsPanel() {
  const { selectedSubstanceId, isDetailsPanelOpen, closeDetailsPanel } = useExtractionStore();
  const { data, isLoading, error } = useSubstance(selectedSubstanceId);

  const substance = data?.data;

  return (
    <AnimatePresence>
      {isDetailsPanelOpen && selectedSubstanceId && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
            onClick={closeDetailsPanel}
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
                <h2 className="text-lg font-semibold">Substance Details</h2>
                <Button variant="ghost" size="icon" onClick={closeDetailsPanel}>
                  <X className="h-5 w-5" />
                </Button>
              </div>

              <ScrollArea className="flex-1 overflow-y-auto">
                {isLoading ? (
                  <LoadingSkeleton />
                ) : error ? (
                  <div className="flex flex-col items-center justify-center p-6 text-center">
                    <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
                    <p className="text-lg font-medium">Failed to load substance</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Please try again later
                    </p>
                  </div>
                ) : substance ? (
                  <div className="p-6 space-y-6">
                    <div>
                      <h3 className="text-2xl font-bold capitalize">{substance.name}</h3>
                      <div className="flex items-center gap-2 mt-2">
                        {substance.is_enriched && (
                          <Badge className="bg-emerald-500/10 text-emerald-700 border-emerald-500/20">
                            Enriched
                          </Badge>
                        )}
                        {substance.substance_class && (
                          <Badge variant="outline">{substance.substance_class}</Badge>
                        )}
                      </div>
                    </div>

                    {substance.smiles && (
                      <MoleculeViewer
                        smiles={substance.smiles}
                        name={substance.name}
                        width={400}
                        height={250}
                      />
                    )}

                    <Tabs defaultValue="overview" className="w-full">
                      <TabsList className="w-full grid grid-cols-4">
                        <TabsTrigger value="overview">Overview</TabsTrigger>
                        <TabsTrigger value="drugs">
                          Drugs ({substance.drugs.length})
                        </TabsTrigger>
                        <TabsTrigger value="labels">Labels</TabsTrigger>
                        <TabsTrigger value="safety">Safety</TabsTrigger>
                      </TabsList>

                      <TabsContent value="overview" className="mt-4 space-y-6">
                        <div>
                          <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                            <Package className="h-4 w-4" />
                            Chemical Identifiers
                          </h4>
                          <ChemicalIdentifiers substance={substance} />
                        </div>

                        <Separator />

                        <div>
                          <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                            <Activity className="h-4 w-4" />
                            Molecular Properties
                          </h4>
                          <MolecularProperties substance={substance} />
                        </div>

                        {substance.pharm_classes.length > 0 && (
                          <>
                            <Separator />
                            <div>
                              <h4 className="text-sm font-medium mb-3">
                                Pharmacological Classes
                              </h4>
                              <div className="flex flex-wrap gap-2">
                                {substance.pharm_classes.map((pc) => (
                                  <Badge key={pc.key} variant="secondary">
                                    {pc.name}
                                    {pc.class_type && (
                                      <span className="ml-1 text-xs opacity-70">
                                        ({pc.class_type})
                                      </span>
                                    )}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          </>
                        )}

                        {substance.routes.length > 0 && (
                          <>
                            <Separator />
                            <div>
                              <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                                <Syringe className="h-4 w-4" />
                                Administration Routes
                              </h4>
                              <div className="flex flex-wrap gap-2">
                                {substance.routes.map((route) => (
                                  <Badge key={route.key} variant="outline">
                                    {route.name}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          </>
                        )}

                        {substance.dosage_forms.length > 0 && (
                          <>
                            <Separator />
                            <div>
                              <h4 className="text-sm font-medium mb-3">Dosage Forms</h4>
                              <div className="flex flex-wrap gap-2">
                                {substance.dosage_forms.map((form) => (
                                  <Badge key={form.key} variant="outline">
                                    {form.name}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          </>
                        )}

                        {substance.manufacturers.length > 0 && (
                          <>
                            <Separator />
                            <div>
                              <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                                <Building2 className="h-4 w-4" />
                                Manufacturers
                              </h4>
                              <div className="flex flex-wrap gap-2">
                                {substance.manufacturers.slice(0, 10).map((mfr) => (
                                  <Badge key={mfr.key} variant="outline">
                                    {mfr.name}
                                  </Badge>
                                ))}
                                {substance.manufacturers.length > 10 && (
                                  <Badge variant="secondary">
                                    +{substance.manufacturers.length - 10} more
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </>
                        )}
                      </TabsContent>

                      <TabsContent value="drugs" className="mt-4">
                        <div className="flex items-center gap-2 mb-4">
                          <Pill className="h-4 w-4" />
                          <h4 className="text-sm font-medium">
                            Commercial Drug Products
                          </h4>
                        </div>
                        <DrugsList drugs={substance.drugs} />
                      </TabsContent>

                      <TabsContent value="labels" className="mt-4">
                        <div className="flex items-center gap-2 mb-4">
                          <FileText className="h-4 w-4" />
                          <h4 className="text-sm font-medium">
                            Drug Labels / Package Inserts
                          </h4>
                        </div>
                        {substance.labels.length > 0 ? (
                          <div className="space-y-4">
                            {substance.labels.slice(0, 3).map((label) => (
                              <Card key={label.key}>
                                <CardHeader className="pb-2">
                                  <CardTitle className="text-sm flex items-center justify-between">
                                    <span>SPL ID: {label.spl_id ?? "N/A"}</span>
                                    {label.effective_time && (
                                      <Badge variant="outline" className="text-xs">
                                        {label.effective_time}
                                      </Badge>
                                    )}
                                  </CardTitle>
                                </CardHeader>
                                <CardContent>
                                  <LabelSection label={label} />
                                </CardContent>
                              </Card>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-muted-foreground">
                            No drug labels available
                          </p>
                        )}
                      </TabsContent>

                      <TabsContent value="safety" className="mt-4 space-y-6">
                        <div>
                          <div className="flex items-center gap-2 mb-4">
                            <Zap className="h-4 w-4" />
                            <h4 className="text-sm font-medium">
                              Drug Interactions ({substance.interactions.length})
                            </h4>
                          </div>
                          <InteractionsList interactions={substance.interactions} />
                        </div>

                        <Separator />

                        <div>
                          <div className="flex items-center gap-2 mb-4">
                            <AlertTriangle className="h-4 w-4" />
                            <h4 className="text-sm font-medium">
                              Adverse Reactions ({substance.reactions.length})
                            </h4>
                          </div>
                          <ReactionsList reactions={substance.reactions} />
                        </div>
                      </TabsContent>
                    </Tabs>
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
