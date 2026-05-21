import { useMemo, useState } from "react";
import type {
  ManualEntryData,
  StepId,
  T1098Review,
  TaxProfile,
  UploadedDocument,
  W2Review,
} from "./types";
import {
  EMPTY_MANUAL_ENTRY,
  EMPTY_TAX_PROFILE,
  buildMock1098TReview,
  buildMockW2Review,
} from "./data/mockData";
import { Header } from "./components/Header";
import { Stepper, type StepDescriptor } from "./components/Stepper";
import { ChatbotSidebar } from "./components/ChatbotSidebar";
import { Welcome } from "./screens/Welcome";
import { Upload } from "./screens/Upload";
import { ManualEntry } from "./screens/ManualEntry";
import { ParsedReview } from "./screens/ParsedReview";
import { TaxProfile as TaxProfileScreen } from "./screens/TaxProfile";
import { Summary } from "./screens/Summary";
import { FinalReview } from "./screens/FinalReview";

const STEPS: StepDescriptor[] = [
  { id: "welcome", label: "Welcome", shortLabel: "Welcome" },
  { id: "upload", label: "Documents", shortLabel: "Documents" },
  { id: "review", label: "Review", shortLabel: "Review" },
  { id: "profile", label: "Profile", shortLabel: "Profile" },
  { id: "summary", label: "Summary", shortLabel: "Summary" },
  { id: "final", label: "Final", shortLabel: "Final" },
];

// When the user is in manual entry mode, swap the second step label.
const MANUAL_STEPS: StepDescriptor[] = STEPS.map((s) =>
  s.id === "upload"
    ? { id: "manual" as StepId, label: "Manual entry", shortLabel: "Manual" }
    : s,
);

export default function App() {
  const [step, setStep] = useState<StepId>("welcome");
  const [mode, setMode] = useState<"upload" | "manual">("upload");

  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [w2Review, setW2Review] = useState<W2Review | null>(null);
  const [t1098Review, setT1098Review] = useState<T1098Review | null>(null);
  const [manual, setManual] = useState<ManualEntryData>(EMPTY_MANUAL_ENTRY);
  const [profile, setProfile] = useState<TaxProfile>(EMPTY_TAX_PROFILE);
  const [prepared, setPrepared] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);

  const handleMarkParsed = (id: string) => {
    setDocuments((prev) =>
      prev.map((d) => (d.id === id ? { ...d, status: "parsed" } : d)),
    );

    setDocuments((curr) => {
      const doc = curr.find((d) => d.id === id);
      if (!doc) return curr;
      if (doc.kind === "W-2" && !w2Review) {
        setW2Review(buildMockW2Review(id));
      } else if (doc.kind === "1098-T" && !t1098Review) {
        setT1098Review(buildMock1098TReview(id));
      }
      return curr;
    });
  };

  const handleDeleteDocument = (id: string) => {
    setDocuments((prev) => prev.filter((d) => d.id !== id));
    if (w2Review?.documentId === id) setW2Review(null);
    if (t1098Review?.documentId === id) setT1098Review(null);
  };

  const visibleSteps = useMemo<StepDescriptor[]>(() => {
    if (step === "welcome") return STEPS;
    return mode === "manual" ? MANUAL_STEPS : STEPS;
  }, [step, mode]);

  // The id in the stepper for the current step (upload vs manual differ).
  const stepperCurrent: StepId = step === "manual" ? "manual" : step;

  const goNext = (next: StepId) => {
    setStep(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#fafafa]">
      <Header
        onToggleChat={() => setChatOpen((v) => !v)}
        chatOpen={chatOpen}
      />

      <div className="mx-auto flex w-full max-w-7xl flex-1">
        <div className="flex w-full flex-1 flex-col lg:mr-[360px]">
          {step !== "welcome" ? (
            <div className="border-b border-slate-200/70 bg-white/60">
              <div className="mx-auto w-full max-w-3xl px-4 py-3 sm:py-4">
                <Stepper
                  steps={visibleSteps}
                  currentStep={stepperCurrent}
                  onStepClick={(id) => setStep(id)}
                />
              </div>
            </div>
          ) : null}

          <main className="flex-1">
            {step === "welcome" ? (
              <Welcome
                onStartUpload={() => {
                  setMode("upload");
                  goNext("upload");
                }}
                onStartManual={() => {
                  setMode("manual");
                  goNext("manual");
                }}
              />
            ) : null}

            {step === "upload" ? (
              <Upload
                documents={documents}
                onAdd={(docs) => setDocuments((prev) => [...prev, ...docs])}
                onMarkParsed={handleMarkParsed}
                onDelete={handleDeleteDocument}
                onContinue={() => goNext("review")}
                onBack={() => goNext("welcome")}
              />
            ) : null}

            {step === "manual" ? (
              <ManualEntry
                data={manual}
                onChange={setManual}
                onContinue={() => {
                  if (manual.filingStatus && !profile.filingStatus) {
                    setProfile((p) => ({
                      ...p,
                      filingStatus: manual.filingStatus,
                    }));
                  }
                  goNext("profile");
                }}
                onBack={() => goNext("welcome")}
              />
            ) : null}

            {step === "review" ? (
              <ParsedReview
                w2={w2Review}
                t1098={t1098Review}
                onUpdateW2={setW2Review}
                onUpdate1098T={setT1098Review}
                onContinue={() => goNext("profile")}
                onBack={() => goNext("upload")}
              />
            ) : null}

            {step === "profile" ? (
              <TaxProfileScreen
                profile={profile}
                onChange={setProfile}
                onContinue={() => goNext("summary")}
                onBack={() => goNext(mode === "manual" ? "manual" : "review")}
              />
            ) : null}

            {step === "summary" ? (
              <Summary
                w2={w2Review}
                t1098={t1098Review}
                manual={manual}
                profile={profile}
                documents={documents}
                onContinue={() => goNext("final")}
                onBack={() => goNext("profile")}
              />
            ) : null}

            {step === "final" ? (
              <FinalReview
                w2={w2Review}
                t1098={t1098Review}
                manual={manual}
                profile={profile}
                documents={documents}
                onBack={() => goNext("summary")}
                onPrepare={() => setPrepared(true)}
                prepared={prepared}
              />
            ) : null}
          </main>

          <footer className="border-t border-slate-200/70 bg-white/50 py-6 text-center text-[11px] text-slate-400">
            TaxMax AI · Prototype · Not for actual filing · United States
          </footer>
        </div>

        <ChatbotSidebar
          step={step}
          open={chatOpen}
          onClose={() => setChatOpen(false)}
          scenarioContext={{
            profile,
            manual,
            w2: w2Review,
            t1098: t1098Review,
            documents,
          }}
        />
      </div>
    </div>
  );
}
