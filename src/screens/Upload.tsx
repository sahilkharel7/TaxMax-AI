import { useCallback, useRef, useState, type DragEvent } from "react";
import type { DocumentKind, UploadedDocument } from "../types";
import { Button } from "../components/ui/Button";
import { Card, SectionHeader } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/StatusBadge";

interface UploadProps {
  documents: UploadedDocument[];
  onAdd: (docs: UploadedDocument[]) => void;
  onMarkParsed: (id: string) => void;
  onDelete: (id: string) => void;
  onContinue: () => void;
  onBack: () => void;
}

const ACCEPTED = ".pdf,.jpg,.jpeg,.png";

function inferKind(name: string): DocumentKind {
  const n = name.toLowerCase();
  if (n.includes("w2") || n.includes("w-2")) return "W-2";
  if (n.includes("1098")) return "1098-T";
  if (n.includes("1099")) return "1099-INT";
  return "Other";
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function Upload({
  documents,
  onAdd,
  onMarkParsed,
  onDelete,
  onContinue,
  onBack,
}: UploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;
      const newDocs: UploadedDocument[] = Array.from(files).map((file) => ({
        id: crypto.randomUUID(),
        name: file.name,
        kind: inferKind(file.name),
        sizeBytes: file.size,
        uploadedAt: Date.now(),
        status: "parsing",
      }));
      onAdd(newDocs);
      newDocs.forEach((doc) => {
        window.setTimeout(() => onMarkParsed(doc.id), 1500 + Math.random() * 900);
      });
    },
    [onAdd, onMarkParsed],
  );

  const hasParsed = documents.some((d) => d.status === "parsed");

  return (
    <div className="animate-fade-up mx-auto w-full max-w-3xl px-4 py-8 sm:py-10">
      <SectionHeader
        eyebrow="Step 2"
        title="Upload your tax documents"
        description="Drop in your W-2, 1098-T, 1099-INT, or any other tax form. We’ll extract the fields and walk you through a review."
      />

      <Card>
        <div
          onDragOver={(e: DragEvent<HTMLDivElement>) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e: DragEvent<HTMLDivElement>) => {
            e.preventDefault();
            setIsDragging(false);
            handleFiles(e.dataTransfer.files);
          }}
          className={[
            "flex flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-10 text-center transition",
            isDragging
              ? "border-slate-900 bg-slate-50"
              : "border-slate-200 bg-slate-50/40 hover:bg-slate-50",
          ].join(" ")}
        >
          <span className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-white text-slate-700 ring-1 ring-slate-200">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </span>
          <p className="text-sm font-medium text-slate-900">
            Drop files here or
            <button
              type="button"
              className="ml-1 underline underline-offset-4 hover:text-slate-700"
              onClick={() => inputRef.current?.click()}
            >
              browse
            </button>
          </p>
          <p className="mt-1 text-xs text-slate-500">
            PDF, JPG, or PNG · up to 25 MB each
          </p>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED}
            multiple
            className="hidden"
            onChange={(e) => {
              handleFiles(e.target.files);
              e.target.value = "";
            }}
          />
        </div>

        <p className="mt-3 text-xs text-slate-400">
          Document parsing may contain errors. Always review and confirm your
          information.
        </p>
      </Card>

      {documents.length > 0 ? (
        <Card className="mt-6">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">
              Uploaded documents
            </h3>
            <span className="text-xs text-slate-400">
              {documents.length} file{documents.length === 1 ? "" : "s"}
            </span>
          </div>
          <ul className="divide-y divide-slate-100">
            {documents.map((doc) => (
              <li
                key={doc.id}
                className="flex items-center gap-3 py-3 first:pt-0 last:pb-0"
              >
                <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-50 text-[10px] font-semibold text-slate-600 ring-1 ring-slate-200">
                  {doc.kind === "W-2"
                    ? "W-2"
                    : doc.kind === "1098-T"
                      ? "1098"
                      : doc.kind === "1099-INT"
                        ? "1099"
                        : "DOC"}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-slate-900">
                    {doc.name}
                  </p>
                  <p className="text-xs text-slate-500">
                    {doc.kind} · {formatSize(doc.sizeBytes)}
                  </p>
                </div>
                {doc.status === "parsing" ? (
                  <StatusBadge tone="info">Parsing…</StatusBadge>
                ) : doc.status === "parsed" ? (
                  <StatusBadge tone="complete">Parsed</StatusBadge>
                ) : (
                  <StatusBadge tone="missing">Error</StatusBadge>
                )}
                <button
                  type="button"
                  onClick={() => onDelete(doc.id)}
                  className="ml-2 rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-red-600"
                  aria-label={`Delete ${doc.name}`}
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                  </svg>
                </button>
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      <div className="mt-8 flex items-center justify-between">
        <Button variant="ghost" onClick={onBack}>
          Back
        </Button>
        <Button onClick={onContinue} disabled={!hasParsed}>
          Continue to review
        </Button>
      </div>
    </div>
  );
}
