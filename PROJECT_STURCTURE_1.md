# Folder Structure Guidelines

## Modular Folder Structure (Velog Style)

Follow this modular structure:

- `/src`
  - `/app` – Global components and config (e.g., Routes, Theme, Toast)
  - `/auth` – Authentication logic
  - `/project`
    - `/board`, `/issueCreate`, `/issueSearch` – Per-feature logic
  - `/shared` – Reusable components (e.g., Button, Avatar, Modal)

**Rules:**
- A module may only import from:
  - Itself
  - `/src/shared`
- Avoid cross-module imports unless through shared

Follow this modular structure:

- `/src`
  - `/app` – Global components and config (e.g., Routes, Theme, Toast)
  - `/auth` – Authentication logic
  - `/project`
    - `/board`, `/issueCreate`, `/issueSearch` – Per-feature logic
  - `/shared` – Reusable components (e.g., Button, Avatar, Modal)

📌 Rules:
- A module may only import from:
  - Itself
  - `/shared`
- Avoid cross-module imports unless through shared