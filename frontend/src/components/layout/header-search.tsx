"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Search, Loader2, Pill } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useSearch } from "@/hooks/use-search";
import { useDebounce } from "@/hooks/use-debounce";
import { useExtractionStore } from "@/store/extraction-store";

export function HeaderSearch() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const debouncedQuery = useDebounce(query, 300);
  const { data, isLoading } = useSearch(debouncedQuery);
  const { setSelectedSubstanceId } = useExtractionStore();
  const containerRef = useRef<HTMLDivElement>(null);

  const results = data?.data ?? [];

  const handleSelect = useCallback(
    (key: string) => {
      setSelectedSubstanceId(key);
      setQuery("");
      setIsOpen(false);
      router.push("/");
    },
    [setSelectedSubstanceId, router]
  );

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} className="relative flex-1 max-w-md mx-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="search"
          placeholder="Search drugs, substances..."
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          className="h-9 pl-9 pr-4 w-full bg-muted/50 border-transparent focus:border-emerald-500/50 focus:bg-background"
        />
        {isLoading && (
          <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-muted-foreground" />
        )}
      </div>

      {isOpen && debouncedQuery.length >= 2 && (
        <Card className="absolute top-full left-0 right-0 mt-2 z-50 max-h-80 overflow-auto shadow-lg">
          <CardContent className="p-2">
            {results.length > 0 ? (
              <div className="space-y-1">
                {results.slice(0, 8).map((result) => (
                  <button
                    key={result.key}
                    onClick={() => handleSelect(result.key)}
                    className="flex items-center gap-3 w-full p-2 rounded-md hover:bg-muted transition-colors text-left"
                  >
                    <div className="flex h-8 w-8 items-center justify-center rounded-md bg-emerald-500/10 flex-shrink-0">
                      <Pill className="h-4 w-4 text-emerald-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{result.name}</p>
                      <p className="text-xs text-muted-foreground truncate">{result.key}</p>
                    </div>
                    <Badge variant="outline" className="text-xs flex-shrink-0">
                      {result.type}
                    </Badge>
                  </button>
                ))}
              </div>
            ) : !isLoading ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No results found for "{debouncedQuery}"
              </p>
            ) : null}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
