# TaxMax AI

> A minimal, premium, AI-assisted tax preparation frontend prototype for U.S.
> federal returns. Built for design + product demos — not for actual filing.

TaxMax AI walks a user through a clean, guided tax prep flow: upload a W-2 or
1098-T, review the extracted fields, answer a few profile questions, and see an
estimated summary — with a contextual chatbot sidebar available the whole way.

This is a **frontend-only prototype**. There is no real document parsing, no
real tax calculation, and no e-filing integration. All values are mock data.

## Stack

- React 19 + TypeScript
- Vite
- Tailwind CSS v4
- Zero runtime dependencies beyond React

## Getting started

```bash
npm install
npm run dev
```

Then open http://localhost:5173.

### Other scripts

```bash
npm run build      # type-check + production build
npm run preview    # serve the production build locally
npm run lint       # ESLint
```

## App structure

```
src/
  App.tsx                 # Step state machine + layout
  main.tsx                # React root
  index.css               # Tailwind v4 + theme tokens
  types.ts                # Shared TypeScript types
  data/
    mockData.ts           # Mock W-2 / 1098-T data, chatbot replies
  components/
    Header.tsx
    Stepper.tsx
    ChatbotSidebar.tsx
    ui/                   # Reusable primitives (Button, Card, Input, ...)
  screens/
    Welcome.tsx
    Upload.tsx
    ManualEntry.tsx
    ParsedReview.tsx
    TaxProfile.tsx
    Summary.tsx
    FinalReview.tsx
```

## User flow

1. **Welcome** — choose document upload or manual entry
2. **Documents** *(upload path)* — drag-and-drop W-2 / 1098-T / 1099-INT, mock parsing
3. **Manual entry** *(manual path)* — personal info, filing status, income, education, credits
4. **Parsed review** — confirm each extracted field with edit + confirm
5. **Tax profile** — filing status and yes/no questions
6. **Summary** — estimated refund / amount owed (clearly labeled as estimate)
7. **Final review** — section-by-section status + warnings, prepare review package

A **TaxMax Guide** chatbot sidebar is available throughout the flow. It uses
mock responses and contextual hints based on the current step.

## Design principles

- White / black / gray with a subtle blue accent
- Generous white space, large readable type, soft borders and shadows
- One clear primary action per screen
- Step-based flow with a persistent stepper
- Trust indicators visible in the header
- Plain-language copy throughout

## Disclaimers (also visible in the UI)

- TaxMax AI provides AI-assisted preparation support. It does not provide legal
  or tax advice.
- Document parsing may contain errors. Always review and confirm your
  information.
- E-filing is not available in this prototype.

## Connecting to a real backend later

State is intentionally kept simple (top-level `useState` in `App.tsx`). When you
add a backend:

- Replace the mock parser in `Upload.tsx` (the `setTimeout` after upload) with a
  real call that returns extracted fields, then feed those into `W2Review` /
  `T1098Review` instead of `buildMockW2Review` / `buildMock1098TReview`.
- Replace `mockChatReply` in `data/mockData.ts` with a streaming call to your
  LLM endpoint.
- Hoist state into a context or query client (e.g. TanStack Query, Zustand,
  Redux) once the surface grows.

## License

Private prototype. All rights reserved.
