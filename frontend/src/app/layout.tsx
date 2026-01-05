import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import { QueryProvider } from "@/providers/query-provider";
import { ThemeProvider } from "@/providers/theme-provider";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Pharma Knowledge | NER/NEL Intelligence Platform",
  description:
    "Extract and analyze pharmaceutical entities from documents using AI-powered Named Entity Recognition and Linking technology.",
  keywords: [
    "pharmaceutical",
    "NER",
    "NEL",
    "drug",
    "substance",
    "FDA",
    "RxNorm",
    "knowledge graph",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <ThemeProvider>
          <QueryProvider>
            <div className="relative flex min-h-screen flex-col">
              <Header />
              <main className="flex-1">{children}</main>
              <Footer />
            </div>
            <Toaster position="bottom-right" richColors />
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
