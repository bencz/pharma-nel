"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { Search, Loader2, Pill } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SubstanceDetailsPanel } from "@/components/substance/substance-details-panel";
import { useSearch } from "@/hooks/use-search";
import { useExtractionStore } from "@/store/extraction-store";
import { useDebounce } from "@/hooks/use-debounce";

export function SearchPage() {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 300);
  const { data, isLoading } = useSearch(debouncedQuery);
  const { setSelectedSubstanceId } = useExtractionStore();

  const handleSelect = useCallback(
    (key: string) => {
      setSelectedSubstanceId(key);
    },
    [setSelectedSubstanceId]
  );

  const results = data?.data ?? [];

  return (
    <div className="min-h-[calc(100vh-8rem)]">
      <div className="container max-w-screen-xl px-4 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          <div className="text-center space-y-4">
            <h1 className="text-4xl font-bold tracking-tight">
              Search
              <span className="bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
                {" "}
                Entities
              </span>
            </h1>
            <p className="mx-auto max-w-xl text-muted-foreground">
              Search the knowledge graph for drugs, substances, and pharmaceutical entities
            </p>
          </div>

          <div className="mx-auto max-w-xl">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search for drugs, substances..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="h-14 pl-12 pr-4 text-lg rounded-xl border-2 focus-visible:ring-emerald-500"
              />
              {isLoading && (
                <Loader2 className="absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2 animate-spin text-muted-foreground" />
              )}
            </div>
          </div>

          {debouncedQuery.length >= 2 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-4"
            >
              {results.length > 0 ? (
                <>
                  <p className="text-sm text-muted-foreground">
                    Found {results.length} results for "{debouncedQuery}"
                  </p>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {results.map((result, index) => (
                      <motion.div
                        key={result.key}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.03 }}
                      >
                        <Card
                          className="cursor-pointer transition-all hover:border-emerald-500/50 hover:shadow-md"
                          onClick={() => handleSelect(result.key)}
                        >
                          <CardContent className="p-4">
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex items-center gap-3">
                                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10">
                                  <Pill className="h-5 w-5 text-emerald-600" />
                                </div>
                                <div>
                                  <p className="font-medium">{result.name}</p>
                                  <p className="text-sm text-muted-foreground">
                                    {result.key}
                                  </p>
                                </div>
                              </div>
                              <Badge variant="outline">{result.type}</Badge>
                            </div>
                          </CardContent>
                        </Card>
                      </motion.div>
                    ))}
                  </div>
                </>
              ) : !isLoading ? (
                <div className="text-center py-12">
                  <p className="text-muted-foreground">
                    No results found for "{debouncedQuery}"
                  </p>
                </div>
              ) : null}
            </motion.div>
          )}
        </motion.div>
      </div>

      <SubstanceDetailsPanel />
    </div>
  );
}
