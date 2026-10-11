"use client";

import { DocumentList } from "@/components/DocumentList";
import { UploadDropzone } from "@/components/UploadDropzone";

export function DocumentLibrary() {
  return (
    <div className="min-h-0 flex-1 overflow-y-auto">
      <div className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6">
        <header>
          <h1 className="text-lg font-semibold tracking-tight">Documents</h1>
          <p className="mt-1 text-sm text-ink-muted">
            Files are split into passages and indexed when uploaded. Questions are answered only from these documents.
          </p>
        </header>

        <section aria-label="Upload documents" className="mt-6">
          <UploadDropzone />
        </section>

        <section aria-labelledby="library-heading" className="mt-8">
          <h2 id="library-heading" className="mb-3 text-sm font-medium">
            Library
          </h2>
          <DocumentList />
        </section>
      </div>
    </div>
  );
}
