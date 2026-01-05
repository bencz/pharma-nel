"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { AlertCircle, Maximize2, Download, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface MoleculeViewerProps {
  smiles: string;
  name?: string;
  width?: number;
  height?: number;
  className?: string;
}

export function MoleculeViewer({
  smiles,
  name,
  width = 300,
  height = 200,
  className,
}: MoleculeViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [imageUrl, setImageUrl] = useState<string | null>(null);

  const renderMolecule = useCallback(async () => {
    if (!smiles) {
      setError("No SMILES provided");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const pubchemUrl = `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/${encodeURIComponent(smiles)}/PNG?image_size=${width}x${height}`;
      
      const response = await fetch(pubchemUrl);
      if (!response.ok) {
        throw new Error("Failed to render molecule");
      }
      
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setImageUrl(url);
      setIsLoading(false);
    } catch (err) {
      console.error("Molecule rendering error:", err);
      setError("Could not render molecule structure");
      setIsLoading(false);
    }
  }, [smiles, width, height]);

  useEffect(() => {
    renderMolecule();
    return () => {
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
      }
    };
  }, [renderMolecule]);

  const handleCopySmiles = useCallback(async () => {
    await navigator.clipboard.writeText(smiles);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [smiles]);

  const handleDownload = useCallback(() => {
    if (imageUrl) {
      const link = document.createElement("a");
      link.href = imageUrl;
      link.download = `${name ?? "molecule"}.png`;
      link.click();
    }
  }, [imageUrl, name]);

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="flex flex-col items-center justify-center p-6 text-center">
          <AlertCircle className="h-8 w-8 text-muted-foreground mb-2" />
          <p className="text-sm text-muted-foreground">{error}</p>
          <p className="text-xs text-muted-foreground mt-2 font-mono break-all max-w-full">
            {smiles.length > 50 ? `${smiles.slice(0, 50)}...` : smiles}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardContent className="p-4">
        <div className="relative">
          {isLoading ? (
            <div
              className="flex items-center justify-center bg-muted/50 rounded-lg animate-pulse"
              style={{ width, height }}
            >
              <div className="text-sm text-muted-foreground">Loading structure...</div>
            </div>
          ) : imageUrl ? (
            <div className="relative group">
              <img
                src={imageUrl}
                alt={`Molecular structure of ${name ?? "compound"}`}
                className="rounded-lg bg-white"
                style={{ width, height, objectFit: "contain" }}
              />
              <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="secondary"
                        size="icon"
                        className="h-7 w-7"
                        onClick={handleDownload}
                      >
                        <Download className="h-3.5 w-3.5" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Download PNG</TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            </div>
          ) : null}
          <canvas ref={canvasRef} className="hidden" />
        </div>

        <div className="mt-3 flex items-center justify-between gap-2">
          <code className="flex-1 text-xs text-muted-foreground font-mono truncate bg-muted/50 px-2 py-1 rounded">
            {smiles.length > 40 ? `${smiles.slice(0, 40)}...` : smiles}
          </code>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 flex-shrink-0"
                  onClick={handleCopySmiles}
                >
                  {copied ? (
                    <Check className="h-3.5 w-3.5 text-emerald-600" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>{copied ? "Copied!" : "Copy SMILES"}</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </CardContent>
    </Card>
  );
}
