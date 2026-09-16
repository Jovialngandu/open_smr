/** Génère un identifiant de mock sans dépendre d'un contexte navigateur sécurisé. */
export function createMockId(prefix = 'mock'): string {
  const nativeRandomUuid = globalThis.crypto?.randomUUID?.bind(globalThis.crypto);
  if (nativeRandomUuid) return nativeRandomUuid();

  const randomPart = Math.random().toString(36).slice(2, 10);
  return `${prefix}-${Date.now().toString(36)}-${randomPart}`;
}
