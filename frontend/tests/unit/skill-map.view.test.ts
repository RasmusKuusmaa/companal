import { RouterLinkStub, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/features/learning/api/learning.api", () => ({
  learningApi: {
    getSkillMap: vi.fn(),
  },
}));

import { learningApi } from "@/features/learning/api/learning.api";
import SkillMapView from "@/features/learning/views/SkillMapView.vue";
import type { SkillMap, TopicMastery } from "@/features/learning/types";

function topic(overrides: Partial<TopicMastery> = {}): TopicMastery {
  return {
    id: "topic-1",
    slug: "intervals",
    name: "Intervals",
    area: "fundamentals",
    description: "Number, quality and inversion.",
    status: "untouched",
    attemptCount: 0,
    correctCount: 0,
    accuracy: 0,
    recentResults: [],
    lastSeenAt: null,
    lessons: [{ slug: "intervals", title: "Intervals" }],
    ...overrides,
  };
}

const skillMap: SkillMap = {
  topics: [
    topic({ id: "t1", slug: "intervals", name: "Intervals", area: "fundamentals" }),
    topic({
      id: "t2",
      slug: "cadences",
      name: "Cadences",
      area: "harmony",
      status: "solid",
      attemptCount: 6,
      correctCount: 5,
      accuracy: 0.83,
      recentResults: [true, true, false, true, true, true],
      lessons: [{ slug: "cadences", title: "Cadences" }],
    }),
    topic({
      id: "t3",
      slug: "parallel-fifths",
      name: "Parallel fifths and octaves",
      area: "harmony",
      status: "needs_practice",
      attemptCount: 4,
      correctCount: 1,
      accuracy: 0.25,
    }),
  ],
  topicCount: 3,
  touchedTopicCount: 2,
};

function mountView() {
  return mount(SkillMapView, {
    global: { stubs: { RouterLink: RouterLinkStub } },
  });
}

async function flush(): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, 0));
}

describe("SkillMapView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.mocked(learningApi.getSkillMap).mockResolvedValue(skillMap);
  });

  it("renders every area", async () => {
    const wrapper = mountView();
    await flush();

    expect(wrapper.text()).toContain("Fundamentals");
    expect(wrapper.text()).toContain("Harmony");
  });

  it("groups topics under their area", async () => {
    const wrapper = mountView();
    await flush();

    expect(wrapper.text()).toContain("Intervals");
    expect(wrapper.text()).toContain("Cadences");
    expect(wrapper.text()).toContain("Parallel fifths and octaves");
  });

  it("shows the coverage total", async () => {
    const wrapper = mountView();
    await flush();

    expect(wrapper.text()).toContain("2 of 3 topics touched");
  });

  it("labels each topic's mastery status", async () => {
    const wrapper = mountView();
    await flush();

    expect(wrapper.text()).toContain("Untouched");
    expect(wrapper.text()).toContain("Solid");
    expect(wrapper.text()).toContain("Needs practice");
  });

  it("shows accuracy only for topics that have been attempted", async () => {
    const wrapper = mountView();
    await flush();

    expect(wrapper.text()).toContain("83%");
    expect(wrapper.text()).toContain("25%");
  });

  it("lists the topic that needs practice, worst first", async () => {
    const wrapper = mountView();
    await flush();

    const list = wrapper.find("li");
    expect(list.exists()).toBe(true);
    expect(wrapper.text()).toContain("Parallel fifths and octaves");

    const hrefs = wrapper.findAllComponents(RouterLinkStub).map((link) => link.props().to);
    expect(hrefs).toContain("/learn/intervals");
  });

  it("lists the topic that's solid", async () => {
    const wrapper = mountView();
    await flush();

    expect(wrapper.text()).toContain("Strengths");
    expect(wrapper.text()).toContain("Cadences");
  });

  it("opens a topic's detail panel on click and closes it again", async () => {
    const wrapper = mountView();
    await flush();

    expect(wrapper.text()).not.toContain("Your attempt history");

    await wrapper
      .findAll("button")
      .find((button) => button.text().includes("Cadences"))
      ?.trigger("click");

    expect(wrapper.text()).toContain("Your attempt history");
    expect(wrapper.text()).toContain("Taught in");
    const hrefs = wrapper.findAllComponents(RouterLinkStub).map((link) => link.props().to);
    expect(hrefs).toContain("/learn/cadences");

    await wrapper.find("[aria-label='Close']").trigger("click");
    expect(wrapper.text()).not.toContain("Your attempt history");
  });

  it("explains an empty curriculum instead of rendering nothing", async () => {
    vi.mocked(learningApi.getSkillMap).mockResolvedValue({
      topics: [],
      topicCount: 0,
      touchedTopicCount: 0,
    });

    const wrapper = mountView();
    await flush();

    expect(wrapper.text()).toContain("seed-curriculum");
  });

  it("reports a failed load", async () => {
    vi.mocked(learningApi.getSkillMap).mockRejectedValue(new Error("network down"));

    const wrapper = mountView();
    await flush();

    expect(wrapper.text()).toContain("Could not load the skill map");
    expect(wrapper.text()).not.toContain("Fundamentals");
  });
});
