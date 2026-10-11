import type { Metadata } from "next";
import { DocumentLibrary } from "@/components/DocumentLibrary";

export const metadata: Metadata = { title: "Documents · RAG Assistant" };

export default function DocumentsPage() {
  return <DocumentLibrary />;
}
