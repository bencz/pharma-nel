"use client";

import { FlaskConical, Github } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "./theme-toggle";
import { HeaderSearch } from "./header-search";
import { useExtractionStore } from "@/store/extraction-store";

export function Header() {
  const reset = useExtractionStore((state) => state.reset);

  const handleLogoClick = () => {
    reset();
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex h-16 max-w-screen-2xl items-center justify-between px-4 md:px-8">
        <Link 
          href="/" 
          onClick={handleLogoClick}
          className="flex items-center gap-3 transition-opacity hover:opacity-80 flex-shrink-0"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 shadow-md">
            <FlaskConical className="h-5 w-5 text-white" />
          </div>
          <div className="hidden sm:flex flex-col">
            <span className="text-lg font-semibold tracking-tight">Pharma Knowledge</span>
            <span className="text-xs text-muted-foreground">NER/NEL Intelligence Platform</span>
          </div>
        </Link>

        <HeaderSearch />

        <nav className="flex items-center gap-2 flex-shrink-0">
          <ThemeToggle />
          <Button variant="outline" size="icon" className="h-9 w-9" asChild>
            <a
              href="https://github.com/bencz/pharma-nel"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="GitHub"
            >
              <Github className="h-4 w-4" />
            </a>
          </Button>
        </nav>
      </div>
    </header>
  );
}
