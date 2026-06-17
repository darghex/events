# Mis Eventos — Frontend

React 18 + TypeScript + Vite , React Router, Zustand, Axios + React Query, Vitest + RTL

## Requisitos
- Node.js 20 LTS
- (o solo) Docker + Docker Compose

## Ejecución vía Docker (recomendada)
Desde la raíz del repo:
```bash
cp .env.example .env
make up
```
App: <http://localhost:5173>.

## Ejecución local (sin Docker)
```bash
cd frontend
npm install
npm run dev
```

## Tests
```bash
npm run test
```

## Estructura
```
frontend/
├── src/
│   ├── App.tsx        # Componente raíz (placeholder Fase 0)
│   ├── main.tsx       # Entry point
│   └── setupTests.ts  # Jest-DOM matchers
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── Dockerfile
```
