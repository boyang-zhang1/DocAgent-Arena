# DocAgent Arena Frontend

Next.js web interface for PDF parser comparison.

## Overview

Two main features:
1. **Parse Battle** (`/battle`) - Blind A/B testing of PDF parsers with 12+ configurations
2. **Side-by-Side Comparison** (`/parse`) - Full document parsing comparison across 5 providers

**Key Features**:
- 5 parsing providers (LlamaIndex, Reducto, LandingAI, ExtendAI, Unstructured.io)
- Real-time SSE streaming for parse progress
- Debug mode with request/response logging
- LaTeX toggle in markdown viewer
- Provider carousel with dual response dropdowns
- Shared PDF viewer hooks for consistent UX

## Prerequisites

- Node.js 18+ and npm
- Backend API running at `http://localhost:8000`

## Quick Start

```bash
# Install dependencies
npm install

# Configure API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev

# Open http://localhost:3000
```

## Project Structure

```
frontend/
├── app/
│   ├── battle/           # Parse Battle UI
│   │   ├── page.tsx      # Battle mode main page + history
│   │   └── [battleId]/   # Battle detail view
│   └── parse/            # Side-by-side comparison
│       └── page.tsx      # Full document parsing
│
├── components/
│   ├── parse/            # Parsing UI components
│   │   ├── FileUploadZone.tsx
│   │   ├── ApiKeyForm.tsx
│   │   ├── ProviderConfigForm.tsx
│   │   ├── CostEstimation.tsx
│   │   ├── PDFViewer.tsx
│   │   └── MarkdownViewer.tsx    # LaTeX toggle support
│   ├── battle/           # Battle mode components
│   │   ├── BattleCharacters.tsx
│   │   └── ModelSelectionCard.tsx
│   └── ui/               # shadcn/ui components
│
├── hooks/
│   └── usePDFViewer.ts   # Shared PDF viewer state management
│
├── lib/
│   ├── api-client.ts     # Backend API client with SSE support
│   ├── modelUtils.ts     # Provider metadata and utilities
│   ├── providerMetadata.ts  # Provider configurations
│   └── utils.ts          # Utilities
│
└── types/
    └── api.ts            # TypeScript types
```

## Pages

### Battle Mode (`/battle`)

Blind A/B testing interface with 12+ configurations:
- Upload PDF and select page for battle
- Configure model options per provider (5 providers, 2-5 modes each)
- System randomly selects 2 providers from configured pool
- View blind comparison (Provider A vs B)
- Submit feedback and reveal winners
- Browse battle history with results
- Provider carousel for easy navigation

**Key Components**: `BattleComparisonView`, `FeedbackForm`, `BattleHistory`, `BattleCard`, `ModelSelectionCard`

### Parse Comparison (`/parse`)

Full document parsing with 5 providers:
- Drag-and-drop PDF upload
- Select up to 5 providers (LlamaIndex, Reducto, LandingAI, ExtendAI, Unstructured.io)
- Configure options per provider (modes, strategies, models)
- Cost estimation before parsing
- Real-time SSE streaming for parse progress
- Page-by-page navigation with dual dropdowns (Structured/Original)
- LaTeX toggle for mathematical expressions
- Debug mode for request/response logging
- Download results

**Key Components**: `FileUploadZone`, `ApiKeyForm`, `ProviderConfigForm`, `CostEstimation`, `PDFViewer`, `MarkdownViewer`

## API Integration

### Parsing Endpoints

```typescript
// Upload PDF
POST /api/v1/parsing/upload
FormData { file }

// Get page count
POST /api/v1/parsing/page-count
{ file_id: string }

// Run battle (single page)
POST /api/v1/parsing/compare
{
  file_id: string,
  page_number: number,
  providers: string[],  // Empty for random selection
  api_keys: { provider: key },
  configs: { provider: { mode, model } }
}

// Parse with SSE streaming (real-time progress)
POST /api/v1/parsing/compare-stream
{
  file_id: string,
  providers: string[],
  api_keys: { provider: key },
  configs: { provider: { mode, model } }
}

// Submit feedback
POST /api/v1/parsing/battle-feedback
{
  battle_id: string,
  preferred_labels: string[],
  comment: string
}

// Get battle history
GET /api/v1/parsing/battles?limit=10&offset=0

// Get battle detail
GET /api/v1/parsing/battles/{battle_id}
```

See `lib/api-client.ts` for full API client implementation.

## Technology Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v3
- **UI Components**: shadcn/ui
- **Charts**: Recharts
- **Animation**: Framer Motion (battle mode)
- **Icons**: lucide-react
- **Markdown**: react-markdown with LaTeX support (KaTeX)
- **PDF Viewer**: react-pdf with custom hooks

## Development

```bash
# Development mode with hot reload
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint
npm run lint
```

## State Management

- **API Keys**: Stored in localStorage, persisted across sessions (5 providers)
- **Provider Configs**: Stored in localStorage per provider (mode, model, strategy)
- **Battle State**: React state, cleared on page refresh
- **Parse Results**: React state, temporary
- **PDF Viewer State**: Managed by `usePDFViewer` hook (shared across battle/parse)
- **SSE Connections**: Managed in parse page for real-time updates
- **Debug Mode**: Toggle stored in component state

## Styling

Built with Tailwind CSS v3 and shadcn/ui components. Theme configured in `tailwind.config.js`.

## Troubleshooting

### Backend connection issues
```bash
# Check backend is running
curl http://localhost:8000/api/health

# Verify .env.local
cat .env.local
```

### Build errors
```bash
# Clean rebuild
rm -rf .next node_modules package-lock.json
npm install
npm run build
```

## Contributing

When adding features:
1. Add TypeScript types to `types/api.ts`
2. Update API client in `lib/api-client.ts`
3. Create reusable components in `components/`
4. Follow existing naming conventions (PascalCase for components)

## License

Part of the DocAgent Arena project (MIT License).
