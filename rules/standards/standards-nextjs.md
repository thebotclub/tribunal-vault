# Next.js Project Standards

## App Router vs Pages Router
- New projects use App Router (`app/`) exclusively
- Server Components by default — add `"use client"` only when necessary (event handlers, browser APIs, hooks)
- Never import server-only code into client components

## Data Fetching
- Fetch data in Server Components — pass as props to Client Components
- Use `fetch()` with Next.js cache options: `{ cache: 'force-cache' }` (static), `{ next: { revalidate: N } }` (ISR), `{ cache: 'no-store' }` (dynamic)
- Use React Query / SWR only for client-side mutations and real-time data

## Routing & Layout
- Colocate page-specific components in the route segment directory
- Use `layout.tsx` for shared UI, `loading.tsx` for Suspense boundaries, `error.tsx` for error boundaries
- Dynamic segments: `[slug]`, catch-all: `[...slug]`, optional: `[[...slug]]`

## Server Actions
- Use Server Actions for form submissions and mutations (not API routes for internal data)
- Always validate inputs with Zod in Server Actions
- Return `{ success, error, data }` shaped responses from Server Actions

## API Routes (Route Handlers)
- Use Route Handlers (`app/api/`) only for external webhooks or public APIs
- Export named HTTP method functions: `export async function GET(request: Request)`
- Validate auth at the top of every Route Handler

## Testing (TDD)
- Unit test Server Components with `@testing-library/react` + `react-dom/server`
- Integration test with Playwright for critical user flows (auth, checkout, etc.)
- Mock `next/navigation` hooks in client component tests

## Performance
- Use `next/image` for all images — never raw `<img>` tags
- Use `next/font` for web fonts — eliminates CLS
- Analyse bundle with `@next/bundle-analyzer` before each major release
- Avoid large client-side dependencies — check if server-side alternatives exist

## TypeScript
- Enable `strict: true` in `tsconfig.json`
- Type page `params` and `searchParams` props explicitly
- Use `Metadata` type from `next` for SEO metadata exports
