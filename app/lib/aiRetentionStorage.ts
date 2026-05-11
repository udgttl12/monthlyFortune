export const AI_RETENTION_ARCHIVE_STORAGE_KEY = "monthlyFortune.aiRetentionArchive.v1";

export interface AiRetentionArchiveItem {
  id: string;
  type: "daily" | "coach";
  title: string;
  createdAt: string;
  payload: unknown;
}

interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

function isArchiveItem(value: unknown): value is AiRetentionArchiveItem {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.id === "string" &&
    (record.type === "daily" || record.type === "coach") &&
    typeof record.title === "string" &&
    typeof record.createdAt === "string"
  );
}

export function readAiRetentionArchive(storage: StorageLike): AiRetentionArchiveItem[] {
  try {
    const rawValue = storage.getItem(AI_RETENTION_ARCHIVE_STORAGE_KEY);
    if (!rawValue) {
      return [];
    }

    const parsed: unknown = JSON.parse(rawValue);
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.filter(isArchiveItem);
  } catch {
    return [];
  }
}

export function appendAiRetentionArchiveItem(storage: StorageLike, item: AiRetentionArchiveItem): void {
  try {
    const next = [item, ...readAiRetentionArchive(storage)].slice(0, 50);
    storage.setItem(AI_RETENTION_ARCHIVE_STORAGE_KEY, JSON.stringify(next));
  } catch {
    // Archiving should never block the user's reading.
  }
}
