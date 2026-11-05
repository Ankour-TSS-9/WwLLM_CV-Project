/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_ENABLE_AI_COACH: string
  readonly VITE_ENABLE_COMMENTARY: string
  readonly VITE_ENABLE_CHAT: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
