# Convenciones de Frontend (React.js)

## Stack Tecnológico
- **Lenguaje:** TypeScript (estricto: `strict: true` en `tsconfig`).
- **Build tool:** Vite.
- **UI:** React 18+ con componentes funcionales y hooks.
- **Enrutamiento:** React Router (v6+).
- **Manejador de estado global:** **Zustand** (decidido — menor superficie para el alcance del MVP).
- **HTTP client:** **Axios** con instancia central (`baseURL`, interceptores para JWT y errores).
- **Server state / caché:** **React Query (TanStack Query)** para todas las llamadas al backend (cubre el bonus de caching).
- **Testing:** Vitest + React Testing Library.
- **Lint/format:** ESLint + Prettier.

## Convenciones de integración con el backend
- Manejo del shape de error canónico del backend (`{ error: { code, message, details } }`) en un interceptor de Axios; mapear `code` → mensaje UX.
- Auth: access token en memoria (Zustand store), refresh token en `httpOnly` cookie si el backend lo soporta, o en `localStorage` como fallback documentado.
- Interceptor que renueva el access token al recibir `AUTH_TOKEN_EXPIRED` y reintenta la request original una vez.

## Estilo de Código y UI
- Todos los componentes reutilizables deben ser modulares y ubicarse en `src/components/ui/`.
- Manejar los estados de carga (loading) y error de forma explícita en cada petición HTTP para mejorar la experiencia de usuario.

## Comandos de Utilidad (Claude Code CLI)
- Instalar dependencias: `npm install` o `yarn install`
- Ejecutar en desarrollo: `npm run dev`
- Ejecutar pruebas: `npm run test` (Obligatorio ejecutar tras cambios en UI).
