"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { FileText, Sparkles, Database, Zap, Users, Clock } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileDropzone } from "@/components/upload/file-dropzone";
import { RecentExtractionsCompact } from "@/components/extractions/recent-extractions-compact";
import { ProfilesGrid } from "@/components/profiles/profiles-grid";
import { useExtract } from "@/hooks/use-extract";

const features = [
  {
    icon: FileText,
    title: "PDF Processing",
    description: "Advanced OCR",
  },
  {
    icon: Sparkles,
    title: "AI-Powered NER",
    description: "LLM Recognition",
  },
  {
    icon: Database,
    title: "Knowledge Graph",
    description: "FDA & RxNorm",
  },
  {
    icon: Zap,
    title: "Enrichment",
    description: "Molecular Data",
  },
];

export function UploadPage() {
  const router = useRouter();
  const { mutate: extract, isPending } = useExtract();

  const handleFileSelect = useCallback(
    (file: File) => {
      extract(file, {
        onSuccess: (response) => {
          if (response.success && response.data) {
            toast.success("Extraction complete", {
              description: `Found ${response.data.entities.length} entities`,
            });
            router.push(`/extraction/${response.data.extraction_id}`);
          } else {
            toast.error("Extraction failed", {
              description: response.error?.message ?? "Unknown error",
            });
          }
        },
        onError: (error) => {
          toast.error("Extraction failed", {
            description: error.message,
          });
        },
      });
    },
    [extract, router]
  );

  return (
    <div className="min-h-[calc(100vh-8rem)]">
      <div className="mx-auto w-full max-w-screen-xl px-4 md:px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          <div className="text-center">
            <h1 className="text-3xl font-bold tracking-tight">
              Pharmaceutical Entity
              <span className="bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
                {" "}Intelligence
              </span>
            </h1>
            <p className="mt-2 text-muted-foreground max-w-2xl mx-auto">
              Upload resumes to extract and analyze pharmaceutical entities with AI-powered NER/NEL.
            </p>
          </div>

          <Card>
            <CardContent className="p-6">
              <FileDropzone onFileSelect={handleFileSelect} isUploading={isPending} />
            </CardContent>
          </Card>

          <div className="grid grid-cols-4 gap-3">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 + index * 0.05 }}
                className="flex flex-col items-center text-center p-3 rounded-lg border bg-card"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10 mb-2">
                  <feature.icon className="h-5 w-5 text-emerald-600" />
                </div>
                <p className="text-xs font-medium">{feature.title}</p>
                <p className="text-xs text-muted-foreground">{feature.description}</p>
              </motion.div>
            ))}
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Clock className="h-4 w-4 text-emerald-600" />
                  Recent Extractions
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <RecentExtractionsCompact limit={6} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Users className="h-4 w-4 text-blue-600" />
                  All Professionals
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <ProfilesGrid limit={6} />
              </CardContent>
            </Card>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
