"use client";

import { useCallback, useState } from "react";
import { Upload, FileText, X, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface FileDropzoneProps {
  onFileSelect: (file: File) => void;
  isUploading: boolean;
  accept?: string;
  maxSize?: number;
}

export function FileDropzone({
  onFileSelect,
  isUploading,
  accept = ".pdf",
  maxSize = 50 * 1024 * 1024,
}: FileDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validateFile = useCallback(
    (file: File): string | null => {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        return "Only PDF files are supported";
      }
      if (file.size > maxSize) {
        return `File size must be less than ${Math.round(maxSize / 1024 / 1024)}MB`;
      }
      return null;
    },
    [maxSize]
  );

  const handleFile = useCallback(
    (file: File) => {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }
      setError(null);
      setSelectedFile(file);
    },
    [validateFile]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLElement>) => {
      e.preventDefault();
      setIsDragging(false);

      const file = e.dataTransfer.files[0];
      if (file) {
        handleFile(file);
      }
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent<HTMLElement>) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLElement>) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        handleFile(file);
      }
    },
    [handleFile]
  );

  const handleRemoveFile = useCallback(() => {
    setSelectedFile(null);
    setError(null);
  }, []);

  const handleUpload = useCallback(() => {
    if (selectedFile) {
      onFileSelect(selectedFile);
    }
  }, [selectedFile, onFileSelect]);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  return (
    <div className="w-full space-y-4">
      <label
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={cn(
          "relative flex min-h-[280px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed transition-all duration-200",
          isDragging
            ? "border-emerald-500 bg-emerald-500/5"
            : "border-border hover:border-emerald-500/50 hover:bg-muted/50",
          isUploading && "pointer-events-none opacity-60"
        )}
      >
        <input
          type="file"
          accept={accept}
          onChange={handleInputChange}
          className="sr-only"
          disabled={isUploading}
        />

        <AnimatePresence mode="wait">
          {selectedFile ? (
            <motion.div
              key="file-selected"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="flex flex-col items-center gap-4 p-6"
            >
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10">
                <FileText className="h-8 w-8 text-emerald-600" />
              </div>
              <div className="text-center">
                <p className="font-medium text-foreground">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemoveFile();
                }}
                className="text-muted-foreground hover:text-destructive"
              >
                <X className="mr-1 h-4 w-4" />
                Remove
              </Button>
            </motion.div>
          ) : (
            <motion.div
              key="no-file"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="flex flex-col items-center gap-4 p-6"
            >
              <div
                className={cn(
                  "flex h-16 w-16 items-center justify-center rounded-2xl transition-colors",
                  isDragging ? "bg-emerald-500/20" : "bg-muted"
                )}
              >
                <Upload
                  className={cn(
                    "h-8 w-8 transition-colors",
                    isDragging ? "text-emerald-600" : "text-muted-foreground"
                  )}
                />
              </div>
              <div className="text-center">
                <p className="text-lg font-medium text-foreground">
                  {isDragging ? "Drop your file here" : "Drag & drop your PDF"}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  or click to browse from your computer
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className="rounded-md bg-muted px-2 py-1">PDF</span>
                <span>Max {Math.round(maxSize / 1024 / 1024)}MB</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </label>

      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="text-center text-sm text-destructive"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>

      {selectedFile && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex justify-center"
        >
          <Button
            onClick={handleUpload}
            disabled={isUploading}
            size="lg"
            className="min-w-[200px] bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700"
          >
            {isUploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Extract Entities
              </>
            )}
          </Button>
        </motion.div>
      )}
    </div>
  );
}
