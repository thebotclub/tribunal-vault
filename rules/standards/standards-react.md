# React Project Standards

## Component Architecture
- Prefer functional components with hooks over class components
- Co-locate component logic, styles, and tests in the same directory
- Use named exports for components (not default exports) for better refactoring support
- Keep components small and focused: if a component exceeds ~150 lines, split it

## State Management
- Use `useState` for local UI state, `useReducer` for complex state logic
- Lift state only as high as necessary — avoid prop drilling beyond 2 levels (use Context or a state library)
- Prefer server state libraries (React Query / SWR) for async data — avoid storing server responses in Redux/Zustand

## Hooks
- Custom hooks must start with `use` and live in `src/hooks/`
- Never call hooks inside conditions, loops, or nested functions
- Extract repeated effect logic into custom hooks

## Testing (TDD)
- Use React Testing Library — query by role/label, not test IDs
- Test user behaviour, not implementation details
- Required coverage: all user interactions, loading/error states, edge cases
- Mock at the network boundary (MSW preferred over mocking modules)

## Performance
- Wrap expensive computations in `useMemo`, expensive callbacks in `useCallback`
- Use `React.lazy` + `Suspense` for route-level code splitting
- Avoid anonymous functions in JSX for stable references

## TypeScript
- All props must be typed via `interface` (not `type` for component props)
- Never use `any` — use `unknown` and narrow appropriately
- Use `React.FC` sparingly — prefer explicit return types

## Accessibility
- Every interactive element must be keyboard-navigable
- Images require `alt` text; decorative images use `alt=""`
- Use semantic HTML elements before reaching for ARIA attributes
