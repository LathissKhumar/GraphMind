# GraphMind Frontend Development Plan

**Project**: GraphMind (CodeGraphX)  
**Date**: May 3, 2026  
**Audience**: Frontend Developer (Your Friend)  
**Status**: Ready for Implementation

---

## Executive Summary

You are tasked with building the **complete frontend** for GraphMind - a token-efficient code reasoning engine. The frontend is a React + Vite dashboard that visualizes codebases as interactive graphs, tracks token savings, and provides query interface to an AI-powered backend.

**Current State**: No frontend exists. You are building from scratch.

**Backend State**: FastAPI backend with 9 endpoints (contract defined, implementation in progress).

---

## 1. Project Overview

### What is GraphMind?

GraphMind (CodeGraphX) is a smart inference engine that:
- Accepts real codebases via GitHub URL or ZIP upload
- Parses them into knowledge graphs (using TigerGraph)
- Routes queries through 3 tiers to minimize LLM token usage by 70-90%:
  - **GRAPH_ONLY** (0 tokens) - Direct graph lookup
  - **GRAPH_RAG** (compressed context) - Graph + compressed code
  - **LLM_FULL** (full generation) - Full LLM query

### Your Mission

Build a React dashboard (`dashboard/`) that provides:
1. Codebase input (GitHub URL or ZIP upload)
2. Interactive graph visualization (Cytoscape.js)
3. Query interface with routing tier display
4. Token savings meter with dollar cost
5. Metrics charts (token usage, latency)
6. Query history with reasoning display
7. Budget controller
8. Competitor comparison table

---

## 2. Tech Stack (Confirmed)

### Core Framework
| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | Latest | UI framework |
| **TypeScript** | ^5.x | Type safety |
| **Vite** | Latest | Build tool & dev server |

### Visualization Libraries
| Library | Purpose |
|---------|---------|
| **Cytoscape.js** | Graph/network visualization |
| **cytoscape-react** | React wrapper for Cytoscape |
| **Chart.js** | Charts and metrics visualization |
| **react-chartjs-2** | React wrapper for Chart.js |

### Explicitly EXCLUDED (Do NOT Use)
- ❌ **framer-motion** - No animations
- ❌ **WebSocket** - Use polling (every 5 seconds)
- ❌ **Dark mode** - Light mode only
- ❌ **Export features** - No PDF/image export
- ❌ **Authentication** - Public access only

---

## 3. API Endpoints (9 Total)

**Base URL**: `http://localhost:8000/api`

### Input Endpoints

#### 1. POST /api/upload
Upload ZIP file containing codebase.
```typescript
// Request
Content-Type: multipart/form-data
Body: file=@codebase.zip

// Response
{
  "status": "success",
  "file_count": 150,
  "languages": ["Python", "JavaScript"],
  "codebase_id": "abc123"
}
```

#### 2. POST /api/clone
Clone GitHub repository.
```typescript
// Request
{ "url": "https://github.com/fastapi/fastapi" }

// Response
{
  "status": "success",
  "repo_name": "fastapi/fastapi",
  "file_count": 500,
  "codebase_id": "def456"
}
```

#### 3. POST /api/ingest
Trigger ingestion after upload/clone.
```typescript
// Request
{ "codebase_id": "abc123" }

// Response
{
  "status": "success",
  "nodes_created": 1200,
  "edges_created": 3400
}
```

### Query Endpoint

#### 4. POST /api/query
Submit query about the codebase.
```typescript
// Request
{
  "query": "What does the authenticate function do?",
  "codebase_id": "abc123"
}

// Response
{
  "answer": "The authenticate function...",
  "tier": "GRAPH_RAG",
  "tokens_used": 850,
  "response_time": 1.2,
  "savings": 0.75,
  "reasoning": "Found relevant nodes in graph, used compressed context"
}
```

### Data Endpoints

#### 5. GET /api/health
System health check.
```typescript
// Response
{ "status": "healthy" }
```

#### 6. GET /api/metrics
Token usage statistics.
```typescript
// Response
{
  "total_tokens": 15000,
  "total_cost": 0.45,
  "savings_percentage": 78.5,
  "queries_count": 42
}
```

#### 7. GET /api/graph
Cytoscape-compatible graph JSON.
```typescript
// Response (Cytoscape.js format)
{
  "nodes": [
    { "data": { "id": "func1", "label": "authenticate", "type": "function" } }
  ],
  "edges": [
    { "data": { "source": "func1", "target": "func2", "type": "calls" } }
  ]
}
```

#### 8. GET /api/query-history
Recent query history.
```typescript
// Response
[
  {
    "query": "What does authenticate do?",
    "answer": "The authenticate function...",
    "tier": "GRAPH_RAG",
    "timestamp": "2026-05-03T12:00:00Z",
    "tokens_used": 850,
    "reasoning": "..."
  }
]
```

### Budget Endpoint

#### 9. POST /api/budget
Set token budget.
```typescript
// Request
{ "budget": 10000 }

// Response
{
  "budget_limit": 10000,
  "budget_used": 2500,
  "budget_remaining": 7500,
  "savings_percentage": 78.5,
  "dollar_cost": 0.45
}
```

---

## 4. UI Components (13 Total)

### Core Components

#### 1. FileDropZone
**Purpose**: Drag-and-drop ZIP file upload

**Features**:
- Drag-and-drop zone with visual feedback
- Progress bar during upload
- Accept only `.zip` files
- Max file size: 10MB
- Shows file count and languages after upload
- Error handling for invalid/corrupt ZIPs

**API Call**: `POST /api/upload` (multipart/form-data)

---

#### 2. RepoInput
**Purpose**: Input GitHub repository URL and clone

**Features**:
- Text input field for GitHub URL
- "Clone" button
- URL validation (must be valid GitHub URL)
- Shows repo name, file count after clone
- Error handling for invalid URLs

**API Call**: `POST /api/clone` (JSON body)

---

#### 3. QueryInput
**Purpose**: Submit queries about the codebase

**Features**:
- Text input for query
- "Submit" button
- Displays query tier (GRAPH_ONLY, GRAPH_RAG, LLM_FULL)
- Shows reasoning for tier selection
- Displays answer
- Shows tokens used and savings

**API Call**: `POST /api/query` (JSON body)

---

#### 4. GraphViz (Cytoscape.js)
**Purpose**: Interactive graph visualization of the codebase

**Features**:
- Render codebase as interactive network graph
- Clickable nodes (show function/class details)
- Zoom and pan controls
- Node types: Module, Class, Function, Import
- Edge types: defines, calls, inherits, imports, contains, depends_on
- Cytoscape-compatible JSON from `/api/graph`
- Auto-refresh via polling (every 5s)

**API Call**: `GET /api/graph` (polling every 5s)

---

#### 5. SavingsMeter
**Purpose**: Display token savings with dollar cost

**Features**:
- Shows: "Saved: $X.XX (YY%)"
- Dollar cost display: "Cost: $0.45"
- Visual progress bar for savings percentage
- Updates in real-time

**API Call**: `GET /api/metrics` (polling every 5s)

---

#### 6. TokenChart (Chart.js)
**Purpose**: Visualize token usage over time

**Features**:
- Line or bar chart
- Show token usage per query
- Compare baseline vs actual (CodeGraphX)
- Display savings per query

**API Call**: Uses data from `GET /api/query-history`

---

#### 7. LatencyChart (Chart.js)
**Purpose**: Visualize response times

**Features**:
- Bar chart showing response time per query
- Compare across query tiers (GRAPH_ONLY, GRAPH_RAG, LLM_FULL)
- Display average latency per tier

**API Call**: Uses data from `GET /api/query-history`

---

#### 8. QueryHistory
**Purpose**: List of past queries with details

**Features**:
- Scrollable list of past queries
- Shows: query text, answer preview, tier, timestamp
- Click to revisit query
- Expand to see full answer and reasoning
- Color-code by tier (green=GRAPH_ONLY, yellow=GRAPH_RAG, red=LLM_FULL)

**API Call**: `GET /api/query-history` (polling every 5s)

---

#### 9. BudgetDisplay
**Purpose**: Show and control token budget

**Features**:
- Shows: "Budget: $5.00 | Used: $0.42 | Saved: $4.58"
- Progress bar for budget usage
- Input field to set new budget: `POST /api/budget`
- Shows remaining budget
- Warning when budget <25% (switches to GRAPH_RAG)
- Critical warning when budget <10% (switches to GRAPH_ONLY)

**API Call**: `GET /api/metrics` + `POST /api/budget`

---

### Additional Components

#### 10. ResetButton
**Purpose**: Clear current repo/state

**Features**:
- "Reset" button
- Confirmation dialog: "Clear current codebase and all data?"
- Clears: codebase_id, graph, query history, metrics
- Refreshes UI to initial state

---

#### 11. CompetitorComparison
**Purpose**: Show comparison with competitors

**Features**:
- Table comparing: Baseline vs GraphRAG vs CodeGraphX
- Metrics: Token usage, cost, time, savings percentage
- Highlight CodeGraphX advantages
- Shows 70-90% token reduction vs baseline

**Data Source**: Static comparison based on benchmark results

---

#### 12. RepoBrowser
**Purpose**: Display current repository information

**Features**:
- Shows: repo name (or "No repo loaded")
- File count
- Languages detected
- "Switch" button to load different repo

---

#### 13. SwitchRepoButton
**Purpose**: Enable loading a different repository

**Features**:
- Clears current repo state
- Enables FileDropZone and RepoInput
- Refreshes UI for new repo input

---

## 5. Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Header: GraphMind - Token-Efficient Code Reasoning           │
│  [RepoBrowser: fastapi/fastapi | 500 files | Python] [Switch]│
└─────────────────────────────────────────────────────────────────┘
┌──────────────────┬──────────────────────────────────────────────┐
│ Left Panel      │  Center Area                                │
│                 │                                             │
│ [QueryInput]    │  [GraphViz - Cytoscape.js]                │
│ ┌─────────────┐ │  (Interactive graph with zoom/pan)          │
│ │ Type query  │ │                                             │
│ │ [Submit]    │ │                                             │
│ └─────────────┘ │                                             │
│                 │                                             │
│ [FileDropZone]  │                                             │
│ ┌─────────────┐ │                                             │
│ │ Drop ZIP    │ │                                             │
│ │ [progress]  │ │                                             │
│ └─────────────┘ │                                             │
│                 │                                             │
│ [RepoInput]     │                                             │
│ ┌─────────────┐ │                                             │
│ │ GitHub URL  │ │                                             │
│ │ [Clone]     │ │                                             │
│ └─────────────┘ │                                             │
│                 │                                             │
│ [BudgetDisplay] │                                             │
│ ┌─────────────┐ │                                             │
│ │ Budget: $5  │ │                                             │
│ │ Used: $0.42 │ │                                             │
│ │ [Set Budget]│ │                                             │
│ └─────────────┘ │                                             │
└──────────────────┴──────────────────────────────────────────────┘
┌──────────────────┬──────────────────┬──────────────────────────┐
│ Right Panel      │                  │                            │
│                  │                  │                            │
│ [SavingsMeter]   │ [TokenChart]     │ [QueryHistory]           │
│ Saved: $4.58    │ (Chart.js)       │ - What does auth do?     │
│ (78.5%)         │                  │   [GRAPH_RAG]            │
│ [========= ]    │                  │ - List of 10 queries     │
│                  │                  │   with tier colors         │
│ [LatencyChart]   │                  │                            │
│ (Chart.js)       │                  │                            │
│                  │                  │                            │
└──────────────────┴──────────────────┴──────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│ [CompetitorComparison]                                         │
│ Baseline | GraphRAG | CodeGraphX                              │
│ Tokens: 10000 | 5000 | 1500                                  │
│ Cost: $1.00 | $0.50 | $0.15                                 │
│ Time: 5s | 3s | 1.2s                                        │
│ Savings: - | 50% | 85% ✓                                     │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│  [ResetButton] - Clear all data and start fresh               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Data Flow & State Management

### State Variables
```typescript
interface AppState {
  // Current codebase
  codebaseId: string | null;
  repoName: string | null;
  fileCount: number | null;
  languages: string[] | null;

  // Graph data
  graphData: CytoscapeGraphData | null;

  // Query
  queryHistory: QueryHistoryItem[];
  currentQuery: string;
  currentAnswer: string | null;
  currentTier: string | null;
  currentReasoning: string | null;

  // Metrics
  metrics: MetricsData | null;
  budget: BudgetData | null;

  // UI state
  isLoading: boolean;
  error: string | null;
}
```

### Data Flow
1. **ZIP Upload Flow**:
   - User drops ZIP → `POST /api/upload` → get `codebase_id`
   - Trigger ingestion → `POST /api/ingest`
   - Start polling: `GET /api/graph`, `GET /api/metrics`

2. **GitHub Clone Flow**:
   - User enters URL → `POST /api/clone` → get `codebase_id`
   - Trigger ingestion → `POST /api/ingest`
   - Start polling: `GET /api/graph`, `GET /api/metrics`

3. **Query Flow**:
   - User submits query → `POST /api/query` → display answer + tier + reasoning
   - Update query history → `GET /api/query-history`
   - Update metrics → `GET /api/metrics`

4. **Polling** (every 5 seconds):
   - `GET /api/graph` → update GraphViz
   - `GET /api/metrics` → update SavingsMeter, BudgetDisplay
   - `GET /api/query-history` → update QueryHistory

**NO WebSocket** - Use `setInterval` with 5000ms delay.

---

## 7. File Structure

```
dashboard/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── README.md
├── src/
│   ├── main.tsx                    # Entry point
│   ├── App.tsx                     # Main app component
│   ├── App.css                     # Global styles
│   ├── components/
│   │   ├── FileDropZone.tsx        # ZIP upload
│   │   ├── FileDropZone.css
│   │   ├── RepoInput.tsx           # GitHub URL input
│   │   ├── RepoInput.css
│   │   ├── QueryInput.tsx          # Query submission
│   │   ├── QueryInput.css
│   │   ├── GraphViz.tsx            # Cytoscape graph
│   │   ├── GraphViz.css
│   │   ├── SavingsMeter.tsx        # Token savings display
│   │   ├── SavingsMeter.css
│   │   ├── TokenChart.tsx          # Chart.js token chart
│   │   ├── TokenChart.css
│   │   ├── LatencyChart.tsx        # Chart.js latency chart
│   │   ├── LatencyChart.css
│   │   ├── QueryHistory.tsx        # Query history list
│   │   ├── QueryHistory.css
│   │   ├── BudgetDisplay.tsx       # Budget controller
│   │   ├── BudgetDisplay.css
│   │   ├── ResetButton.tsx         # Reset state
│   │   ├── ResetButton.css
│   │   ├── CompetitorComparison.tsx # Comparison table
│   │   ├── CompetitorComparison.css
│   │   ├── RepoBrowser.tsx         # Current repo info
│   │   ├── RepoBrowser.css
│   │   ├── SwitchRepoButton.tsx    # Switch repo
│   │   └── SwitchRepoButton.css
│   ├── api/
│   │   ├── client.ts               # API client functions
│   │   └── types.ts               # TypeScript interfaces
│   ├── hooks/
│   │   ├── usePolling.ts           # Polling hook (5s interval)
│   │   └── useApi.ts              # API hooks (tanstack-query or custom)
│   └── utils/
│       ├── constants.ts             # API base URL, intervals
│       └── helpers.ts              # Utility functions
└── public/
    └── (static assets if needed)
```

---

## 8. Implementation Steps (Execution Plan)

### Phase 1: Project Setup (Day 1)

1. **Create dashboard directory**
   ```bash
   mkdir dashboard
   cd dashboard
   ```

2. **Initialize Vite + React + TypeScript**
   ```bash
   npm create vite@latest . -- --template react-ts
   npm install
   ```

3. **Install dependencies**
   ```bash
   # Visualization
   npm install cytoscape cytoscape-react

   # Charts
   npm install chart.js react-chartjs-2

   # HTTP client
   npm install axios

   # Optional: state management
   npm install zustand  # or use React context
   ```

4. **Set up project structure**
   - Create folders: `src/components/`, `src/api/`, `src/hooks/`, `src/utils/`
   - Create empty component files
   - Configure `vite.config.ts`

5. **Verify setup**
   ```bash
   npm run dev
   # Should launch at http://localhost:5173
   ```

---

### Phase 2: API Client + Types (Day 1-2)

6. **Define TypeScript interfaces** (`src/api/types.ts`)
   ```typescript
   export interface UploadResponse {
     status: string;
     file_count: number;
     languages: string[];
     codebase_id: string;
   }

   export interface CloneResponse {
     status: string;
     repo_name: string;
     file_count: number;
     codebase_id: string;
   }

   export interface QueryResponse {
     answer: string;
     tier: 'GRAPH_ONLY' | 'GRAPH_RAG' | 'LLM_FULL';
     tokens_used: number;
     response_time: number;
     savings: number;
     reasoning: string;
   }

   export interface MetricsData {
     total_tokens: number;
     total_cost: number;
     savings_percentage: number;
     queries_count: number;
   }

   export interface GraphData {
     nodes: Array<{ data: { id: string; label: string; type: string } }>;
     edges: Array<{ data: { source: string; target: string; type: string } }>;
   }

   // ... define all other interfaces
   ```

7. **Create API client** (`src/api/client.ts`)
   ```typescript
   import axios from 'axios';
   import { UploadResponse, CloneResponse, QueryResponse, ... } from './types';

   const API_BASE = 'http://localhost:8000/api';

   export const api = {
     uploadZip: async (file: File): Promise<UploadResponse> => { ... },
     cloneRepo: async (url: string): Promise<CloneResponse> => { ... },
     submitQuery: async (query: string, codebaseId: string): Promise<QueryResponse> => { ... },
     getGraph: async (): Promise<GraphData> => { ... },
     getMetrics: async (): Promise<MetricsData> => { ... },
     getQueryHistory: async (): Promise<QueryHistoryItem[]> => { ... },
     setBudget: async (budget: number): Promise<BudgetData> => { ... },
     checkHealth: async (): Promise<{ status: string }> => { ... },
   };
   ```

8. **Add error handling**
   - Wrap API calls in try-catch
   - Show user-friendly error messages
   - Handle network errors, 4xx, 5xx responses

9. **Create mock data** (for development without backend)
   ```typescript
   // src/api/mock.ts
   export const mockGraphData = { ... };
   export const mockMetrics = { ... };
   // Use mocks until backend is ready
   ```

---

### Phase 3: Core Components (Day 2-3)

10. **Build FileDropZone component**
    - Use HTML5 drag-and-drop API or react-dropzone library
    - Style with CSS (dashed border, hover effects)
    - Show progress bar during upload
    - Validate file type (.zip) and size (10MB max)
    - Call `api.uploadZip()` on drop

11. **Build RepoInput component**
    - Text input with validation (regex for GitHub URL)
    - "Clone" button
    - Call `api.cloneRepo()` on submit
    - Show loading state during clone

12. **Build QueryInput component**
    - Text input for query
    - "Submit" button
    - Display tier badge (color-coded)
    - Show reasoning text
    - Display answer in a card
    - Call `api.submitQuery()` on submit

13. **Build GraphViz component (Cytoscape.js)**
    - Initialize Cytoscape instance
    - Configure layout (e.g., cose-bilkent for auto-layout)
    - Style nodes by type (function=blue, class=green, etc.)
    - Style edges by type (calls=solid, inherits=dashed, etc.)
    - Add click handler for nodes (show details)
    - Call `api.getGraph()` and render
    - Set up polling (every 5s) to refresh graph

---

### Phase 4: Metrics + Visualization (Day 3-4)

14. **Build SavingsMeter component**
    - Display: "Saved: $X.XX (YY%)"
    - Show dollar cost: "Total Cost: $Z.ZZ"
    - Progress bar for savings percentage
    - Use `api.getMetrics()` (polling every 5s)

15. **Build TokenChart component (Chart.js)**
    - Line chart: tokens used per query over time
    - Bar chart: compare baseline vs CodeGraphX
    - Use data from `api.getQueryHistory()`
    - Configure Chart.js options (labels, colors, tooltips)

16. **Build LatencyChart component (Chart.js)**
    - Bar chart: response time per query
    - Group by tier (GRAPH_ONLY, GRAPH_RAG, LLM_FULL)
    - Use data from `api.getQueryHistory()`

17. **Build BudgetDisplay component**
    - Show: "Budget: $X | Used: $Y | Remaining: $Z"
    - Progress bar for budget usage
    - Input field to set new budget
    - Call `api.setBudget()` on submit
    - Warning colors when budget <25% or <10%

---

### Phase 5: Additional Features (Day 4-5)

18. **Build QueryHistory component**
    - Scrollable list of past queries
    - Each item shows: query text (truncated), tier badge, timestamp
    - Click to expand: show full answer + reasoning
    - Color-code by tier
    - Use `api.getQueryHistory()` (polling every 5s)

19. **Build RepoBrowser component**
    - Display current repo name (or "No repo loaded")
    - Show file count and languages
    - "Switch" button (triggers reset)

20. **Build ResetButton component**
    - "Reset" button with confirmation dialog
    - On confirm: clear all state (codebaseId, graph, history, metrics)
    - Refresh UI to initial state

21. **Build CompetitorComparison component**
    - Table with 3 columns: Baseline, GraphRAG, CodeGraphX
    - Rows: Token usage, Cost, Time, Savings %
    - Highlight CodeGraphX as winner (green checkmark)
    - Use static data (benchmark results)

22. **Build SwitchRepoButton component**
    - Triggers reset of current repo
    - Enables FileDropZone and RepoInput
    - Refreshes UI

---

### Phase 6: Integration + Polish (Day 5-6)

23. **Integrate all components into App.tsx**
    - Import all 13 components
    - Set up layout (using CSS Grid or Flexbox)
    - Pass props and callbacks
    - Manage global state (use Context or Zustand)

24. **Implement 5-second polling**
    - Create `usePolling` hook
    - Poll: `getGraph()`, `getMetrics()`, `getQueryHistory()`
    - Use `setInterval` with 5000ms delay
    - Clear interval on unmount

25. **Add loading states**
    - Show spinners during API calls
    - Disable buttons while loading
    - Show "Loading..." text

26. **Add error handling**
    - Show error messages in red banners
    - Handle network errors gracefully
    - Provide retry buttons

27. **Style the dashboard**
    - Consistent color scheme (use CSS variables)
    - Responsive design (if needed)
    - Clean, modern UI
    - Match the layout diagram above

---

### Phase 7: Testing (Day 6-7)

28. **Write unit tests** (optional, if time permits)
    - Test API client functions
    - Test utility functions
    - Test component rendering

29. **Run Playwright E2E tests**
    - Test: Dashboard loads successfully
    - Test: ZIP upload flow (if backend ready)
    - Test: GitHub clone flow (if backend ready)
    - Test: Query submission flow
    - Test: Reset button clears state
    - Test: All 13 components render

30. **Manual testing checklist**
    - [ ] All 13 components visible
    - [ ] GraphViz renders Cytoscape graph
    - [ ] FileDropZone accepts ZIP and shows progress
    - [ ] RepoInput clones GitHub repo
    - [ ] QueryInput submits query and shows answer
    - [ ] SavingsMeter shows dollar amounts
    - [ ] TokenChart and LatencyChart render with data
    - [ ] QueryHistory shows past queries with reasoning
    - [ ] BudgetDisplay shows budget info
    - [ ] ResetButton clears all state
    - [ ] CompetitorComparison table visible
    - [ ] RepoBrowser shows repo info
    - [ ] SwitchRepoButton works
    - [ ] Polling updates data every 5 seconds
    - [ ] Error handling works for all API calls

---

## 9. Acceptance Criteria

### Setup
- [ ] `cd dashboard && npm install` succeeds without errors
- [ ] `npm run dev` launches at `http://localhost:5173`
- [ ] All dependencies installed (check `package.json`)

### Components (All 13)
- [ ] **FileDropZone**: Accepts .zip, shows progress, max 10MB
- [ ] **RepoInput**: Validates GitHub URL, clones repo
- [ ] **QueryInput**: Submits query, shows answer + tier + reasoning
- [ ] **GraphViz**: Renders Cytoscape graph, clickable nodes, zoom/pan
- [ ] **SavingsMeter**: Shows dollar amounts and percentage
- [ ] **TokenChart**: Renders token usage chart (Chart.js)
- [ ] **LatencyChart**: Renders latency chart (Chart.js)
- [ ] **QueryHistory**: Lists past queries with tier colors
- [ ] **BudgetDisplay**: Shows budget info, allows setting budget
- [ ] **ResetButton**: Clears state with confirmation
- [ ] **CompetitorComparison**: Shows comparison table
- [ ] **RepoBrowser**: Displays current repo info
- [ ] **SwitchRepoButton**: Enables switching repos

### Integration
- [ ] Polls API every 5 seconds (NO WebSocket)
- [ ] Graph updates automatically
- [ ] Metrics update automatically
- [ ] Query history updates automatically
- [ ] Reset clears all state correctly
- [ ] Switch repo works correctly
- [ ] Error handling for all API calls

### Code Quality
- [ ] TypeScript used throughout (no `any` types)
- [ ] Components are properly typed
- [ ] API client has error handling
- [ ] No console.log in production code
- [ ] Code is clean and readable
- [ ] No unused imports

---

## 10. Constraints (MUST NOT DO)

❌ **No dark mode** - Build only light mode  
❌ **No WebSocket** - Use polling every 5 seconds only  
❌ **No export features** - Do not implement PDF/image export  
❌ **No framer-motion** - Do not use animation libraries  
❌ **No authentication** - Public access only, no login  
❌ **No real-time updates** - Polling only, no live data  
❌ **No additional libraries** - Stick to the specified tech stack  

---

## 11. Helpful Resources

### Documentation
- **React**: https://react.dev/
- **TypeScript**: https://www.typescriptlang.org/docs/
- **Vite**: https://vitejs.dev/guide/
- **Cytoscape.js**: https://js.cytoscape.org/
- **cytoscape-react**: https://github.com/cytoscape/cytoscape.js-react
- **Chart.js**: https://www.chartjs.org/docs/latest/
- **react-chartjs-2**: https://react-chartjs-2.js.org/

### Reference Implementation
Check the main plan file for API response shapes and expected behavior:
- `.sisyphus/plans/codegraphx.md` (tasks 15 and 19 describe dashboard requirements)

### Backend API (When Ready)
- Base URL: `http://localhost:8000/api`
- Health check: `GET http://localhost:8000/api/health`
- Test endpoints with curl or Postman before connecting frontend

### Mock Data (For Development)
Create mock data files to develop frontend without backend:
```typescript
// src/api/mock.ts
export const mockGraphData = {
  nodes: [
    { data: { id: '1', label: 'authenticate', type: 'function' } },
    { data: { id: '2', label: 'User', type: 'class' } }
  ],
  edges: [
    { data: { source: '1', target: '2', type: 'calls' } }
  ]
};
```

---

## 12. Timeline Estimate

| Phase | Task | Estimated Time |
|-------|------|----------------|
| 1 | Project Setup | 1 day |
| 2 | API Client + Types | 1-2 days |
| 3 | Core Components | 2 days |
| 4 | Metrics + Visualization | 2 days |
| 5 | Additional Features | 1-2 days |
| 6 | Integration + Polish | 1-2 days |
| 7 | Testing | 1 day |
| **Total** | | **7-10 days** |

---

## 13. Getting Help

If you get stuck:
1. **Check the main plan**: `.sisyphus/plans/codegraphx.md`
2. **Ask the project owner** (the person who assigned you this task)
3. **Check API documentation** when backend is ready
4. **Use browser DevTools** to debug API calls and state

---

## 14. Final Checklist Before Starting

- [ ] Read this entire document
- [ ] Understand the 9 API endpoints
- [ ] Know all 13 components you need to build
- [ ] Have Node.js and npm installed
- [ ] Have a code editor (VS Code recommended)
- [ ] Backend API is running (or use mock data)
- [ ] Understand the polling requirement (5s interval, no WebSocket)

---

**Good luck! Build an awesome dashboard! 🚀**

---

*Document saved to: `.sisyphus/plans/graphmind-frontend-plan.md`*  
*Created for: Your Friend (Frontend Developer)*  
*Date: May 3, 2026*
