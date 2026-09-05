import { RouterLinkStub, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { nextTick } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/features/projects/api/projects.api", () => ({
  projectsApi: {
    list: vi.fn(),
  },
}));

import DashboardView from "@/app/views/DashboardView.vue";
import { projectsApi } from "@/features/projects/api/projects.api";
import type { Composition } from "@/features/projects/types";

const composition: Composition = {
  id: "c1",
  title: "A Minor Study",
  versionCount: 2,
  createdAt: "2026-01-01T00:00:00Z",
  updatedAt: "2026-01-02T00:00:00Z",
};

function mountDashboard() {
  return mount(DashboardView, {
    global: {
      stubs: {
        RouterLink: RouterLinkStub,
        ContinueLearningCard: true,
        CoverageSummaryCard: true,
      },
    },
  });
}

async function flushAll(): Promise<void> {
  for (let i = 0; i < 5; i += 1) {
    await Promise.resolve();
  }
  await nextTick();
}

beforeEach(() => {
  setActivePinia(createPinia());
  vi.mocked(projectsApi.list).mockReset();
});

describe("DashboardView: project list loading", () => {
  it("shows the compositions once loaded", async () => {
    vi.mocked(projectsApi.list).mockResolvedValue([composition]);

    const wrapper = mountDashboard();
    await flushAll();

    expect(wrapper.text()).toContain("A Minor Study");
  });

  it("shows an error with a retry action when the fetch fails", async () => {
    vi.mocked(projectsApi.list).mockRejectedValue(new Error("network down"));

    const wrapper = mountDashboard();
    await flushAll();

    expect(wrapper.text()).toContain("Could not load your compositions.");
    expect(wrapper.text()).not.toContain("No compositions yet.");

    vi.mocked(projectsApi.list).mockResolvedValue([composition]);
    const retryButton = wrapper
      .findAll("button")
      .find((button) => button.text() === "Try again");
    await retryButton!.trigger("click");
    await flushAll();

    expect(wrapper.text()).toContain("A Minor Study");
  });
});
