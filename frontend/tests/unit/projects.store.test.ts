import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/features/projects/api/projects.api", () => ({
  projectsApi: {
    list: vi.fn(),
    create: vi.fn(),
    rename: vi.fn(),
    remove: vi.fn(),
  },
}));

import { projectsApi } from "@/features/projects/api/projects.api";
import { useProjectsStore } from "@/features/projects/stores/projects.store";

const mockComposition = {
  id: "11111111-1111-1111-1111-111111111111",
  title: "Sonata No. 1",
  versionCount: 0,
  createdAt: "2026-01-01T00:00:00Z",
  updatedAt: "2026-01-01T00:00:00Z",
};

describe("projects store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("fetches and stores the composition list", async () => {
    vi.mocked(projectsApi.list).mockResolvedValue([mockComposition]);

    const store = useProjectsStore();
    await store.fetchAll();

    expect(store.compositions).toEqual([mockComposition]);
    expect(store.isLoading).toBe(false);
  });

  it("prepends a newly created composition", async () => {
    const existing = { ...mockComposition, id: "existing", title: "Existing" };
    vi.mocked(projectsApi.list).mockResolvedValue([existing]);
    vi.mocked(projectsApi.create).mockResolvedValue(mockComposition);

    const store = useProjectsStore();
    await store.fetchAll();
    await store.create({ title: mockComposition.title });

    expect(store.compositions.map((c) => c.id)).toEqual([mockComposition.id, "existing"]);
  });

  it("replaces the renamed composition in place", async () => {
    vi.mocked(projectsApi.list).mockResolvedValue([mockComposition]);
    const renamed = { ...mockComposition, title: "New Title" };
    vi.mocked(projectsApi.rename).mockResolvedValue(renamed);

    const store = useProjectsStore();
    await store.fetchAll();
    await store.rename(mockComposition.id, { title: "New Title" });

    expect(store.compositions[0]?.title).toBe("New Title");
  });

  it("removes a deleted composition from the list", async () => {
    vi.mocked(projectsApi.list).mockResolvedValue([mockComposition]);
    vi.mocked(projectsApi.remove).mockResolvedValue(undefined);

    const store = useProjectsStore();
    await store.fetchAll();
    await store.remove(mockComposition.id);

    expect(store.compositions).toEqual([]);
  });
});
