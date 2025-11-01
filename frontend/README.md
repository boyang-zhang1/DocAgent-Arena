# RAGRace Frontend

A Next.js web application for browsing and visualizing RAG (Retrieval-Augmented Generation) provider benchmark results.

## Overview

This frontend provides a read-only interface to view benchmark results from the RAGRace backend API. Users can browse completed benchmark runs, compare provider performance, and drill down into detailed question-by-question results.

## Prerequisites

- Node.js 18+ and npm
- RAGRace backend API running (default: `http://localhost:8000`)

## Installation

```bash
# Install dependencies
npm install
```

## Configuration

Create a `.env.local` file in the frontend directory:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Development

```bash
# Start development server
npm run dev

# Open browser to http://localhost:3000
```

The development server will:
- Hot-reload on file changes
- Show detailed error messages
- Connect to the backend API at the configured URL

## Building for Production

```bash
# Build optimized production bundle
npm run build

# Start production server
npm start
```

## Project Structure

```
frontend/
├── app/                          # Next.js App Router pages
│   ├── layout.tsx                # Root layout with Navbar
│   ├── page.tsx                  # Home page (results list)
│   ├── results/
│   │   └── [run_id]/
│   │       └── page.tsx          # Run details page
│   └── datasets/
│       └── page.tsx              # Datasets info page
│
├── components/
│   ├── ui/                       # shadcn/ui components
│   │   ├── table.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   ├── button.tsx
│   │   ├── skeleton.tsx
│   │   └── collapsible.tsx
│   ├── layout/
│   │   └── Navbar.tsx            # Navigation component
│   └── results/
│       ├── ResultsTable.tsx      # Benchmark runs table
│       ├── RunDetails.tsx        # Detailed run view
│       └── OverallResultsCard.tsx # Aggregate results with chart
│
├── lib/
│   ├── api-client.ts             # Backend API client
│   ├── aggregateScores.ts        # Score aggregation utilities
│   └── utils.ts                  # Utility functions
│
├── types/
│   └── api.ts                    # TypeScript type definitions
│
└── public/                       # Static assets
```

## Available Scripts

- `npm run dev` - Start development server with webpack
- `npm run build` - Build production bundle
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Pages

### Home (`/`)
- **Purpose**: Browse all benchmark runs
- **Features**:
  - Sortable table with run metadata
  - Filter by dataset (coming soon)
  - Click any row to view details
  - Shows: Run ID, Dataset, Providers, Status, Document count, Question count, Date, Duration

### Run Details (`/results/[run_id]`)
- **Purpose**: View detailed results for a specific run
- **Features**:
  - Run metadata (dataset, providers, status, timing)
  - **Overall aggregate results card** with:
    - Run-level average scores across all documents
    - Provider comparison table with success rates and durations
    - Interactive bar chart with metric selection
  - Document-by-document results
  - Provider comparison tables
  - Aggregated scores per provider per document
  - **Expandable sections** for question-by-question results
  - Ground truth vs. provider answers
  - Retrieved context chunks
  - Evaluation scores and latency metrics

### Datasets (`/datasets`)
- **Purpose**: View available benchmark datasets
- **Features**:
  - Dataset descriptions
  - Available splits (train, validation, test)
  - Document counts
  - Task types

## API Integration

The frontend communicates with the RAGRace backend through three main endpoints:

```typescript
// Get list of runs
GET /api/v1/results?limit=50&offset=0&dataset=qasper

// Get run details
GET /api/v1/results/{run_id}

// Get datasets
GET /api/v1/datasets
```

See `lib/api-client.ts` for the full API client implementation.

## Technology Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v3
- **UI Components**: shadcn/ui
- **Charts**: Recharts (for data visualizations)
- **Date Formatting**: date-fns
- **Icons**: lucide-react

## Features

### Implemented ✅
- Server-side rendering for fast initial loads
- Responsive design (mobile, tablet, desktop)
- Loading skeletons during data fetching
- Error handling with user-friendly messages
- Type-safe API client with TypeScript
- Color-coded status indicators
- Expandable detail views
- Professional UI with shadcn/ui components
- **Charts and visualizations** (interactive bar charts with metric selection)
- **Run-level aggregate results** with cross-document score averaging

### Future Enhancements 🚀
- Additional chart types (radar charts, line charts)
- Advanced filtering and sorting
- Pagination for large result sets
- Dark mode toggle
- Export results (CSV, JSON)
- Real-time updates for running benchmarks
- Search functionality

## Troubleshooting

### Frontend won't connect to backend
1. Verify backend API is running: `curl http://localhost:8000/api/health`
2. Check `.env.local` has correct `NEXT_PUBLIC_API_URL`
3. Ensure CORS is enabled in backend (already configured)

### Build errors
1. Delete `.next` directory: `rm -rf .next`
2. Clear node_modules: `rm -rf node_modules package-lock.json`
3. Reinstall: `npm install`
4. Rebuild: `npm run build`

### Styling not working
1. Verify Tailwind CSS is properly configured in `tailwind.config.js`
2. Check `app/globals.css` imports Tailwind directives
3. Restart dev server after config changes

## Contributing

When adding new features:

1. **Add types** to `types/api.ts` if using new API responses
2. **Update API client** in `lib/api-client.ts` for new endpoints
3. **Create reusable components** in `components/`
4. **Follow naming conventions**:
   - Components: PascalCase (e.g., `ResultsTable.tsx`)
   - Utilities: camelCase (e.g., `api-client.ts`)
   - Types: PascalCase interfaces (e.g., `RunSummary`)

## License

Part of the RAGRace project.
