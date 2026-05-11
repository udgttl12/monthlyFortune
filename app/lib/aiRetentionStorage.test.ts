import assert from "node:assert/strict";
import test from "node:test";
import {
  AI_RETENTION_ARCHIVE_STORAGE_KEY,
  appendAiRetentionArchiveItem,
  readAiRetentionArchive
} from "./aiRetentionStorage";

class MemoryStorage {
  private values = new Map<string, string>();

  getItem(key: string): string | null {
    return this.values.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.values.set(key, value);
  }
}

test("appendAiRetentionArchiveItem prepends latest item", () => {
  const storage = new MemoryStorage();
  appendAiRetentionArchiveItem(storage, {
    id: "first",
    type: "coach",
    title: "면접 질문",
    createdAt: "2026-05-10T00:00:00.000Z",
    payload: { answer: "준비하세요." }
  });

  const archive = readAiRetentionArchive(storage);

  assert.equal(archive[0].id, "first");
  assert.equal(JSON.parse(storage.getItem(AI_RETENTION_ARCHIVE_STORAGE_KEY) ?? "[]").length, 1);
});

test("readAiRetentionArchive returns empty list for corrupt json", () => {
  const storage = new MemoryStorage();
  storage.setItem(AI_RETENTION_ARCHIVE_STORAGE_KEY, "{");

  assert.deepEqual(readAiRetentionArchive(storage), []);
});
