# `.planning/` — Source-of-truth detallado

Esta carpeta contiene la documentación de proceso del proyecto **Mis Eventos**: reglas de dominio, spec de fases, convenciones de API, catálogo de errores y decisiones arquitectónicas (ADRs).


## Mapa

```
.planning/
├── README.md
├── domain.md              Entidades, RBAC, reglas de negocio
├── api.md                 Convenciones REST + shape de error canónico
├── error-catalog.md       Tabla canónica de códigos de error
├── backlog.md             Post-MVP (rate-limit, logging JSON, etc.)
├── phases/
│   ├── 00-bootstrap.md
│   ├── 01-auth-rbac.md
│   ├── 02-events.md
│   ├── 03-transitions.md
│   ├── 04-sessions.md
│   ├── 05-registrations.md
│   └── 06-hardening.md
└── decisions/             ADRs (Architecture Decision Records)
    ├── 001-transactional-helper.md
    ├── 002-state-machine-matrix.md
    ├── 003-speaker-as-derived.md
    ├── 004-sqlite-vs-postgres-locks.md
    └── 005-phase-6-scope-cuts.md
```

## Convenciones

- **Idioma**: estos archivos están en **español** (la decisión de negocio fue tomada en español; los archivos de código sí están en inglés).
- **Formato de fases**: cada `phases/0X-name.md` sigue el mismo esquema **Meta → Pre-requisitos → Decisiones materiales → Pasos secuenciales → DoD verificable → No hacer (anti-scope-creep) → Salida**.
- **Formato de ADRs**: **Contexto → Decisión → Consecuencias**

## Para Claude / colaboradores nuevos

Si entras al proyecto sin contexto previo, lee en este orden:

1. **`/CLAUDE.md`** (root) — reglas must-know + estado de fases.
2. **`.planning/domain.md`** — qué hace el sistema y por qué.
3. **`.planning/api.md`** + **`.planning/error-catalog.md`** — cómo hablan el cliente y la API.
4. **`.planning/phases/0X-name.md`** — el detalle de la fase en la que vas a trabajar.
5. **`.planning/decisions/00X-*.md`** — el porqué de las decisiones difíciles.
