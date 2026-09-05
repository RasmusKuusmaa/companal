import { RouterLinkStub, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/features/learning/api/learning.api", () => ({
  learningApi: {
    getRoadmap: vi.fn(),
    getProgress: vi.fn(),
  },
}));

vi.mock("@/features/exams/api/exams.api", () => ({
  examsApi: {
    listExams: vi.fn(),
  },
}));

import { examsApi } from "@/features/exams/api/exams.api";
import { learningApi } from "@/features/learning/api/learning.api";
import RoadmapView from "@/features/learning/views/RoadmapView.vue";
import type { Roadmap, ProgressSummary } from "@/features/learning/types";

function lesson(overrides: Partial<Roadmap["courses"][0]["lessons"][0]> = {}) {
  return {
    id: "lesson-1",
    slug: "intervals",
    title: "Intervals",
    summary: "Measuring the distance between two notes.",
    position: 0,
    estimatedMinutes: 12,
    stepCount: 4,
    status: "not_started" as const,
    completedAt: null,
    ...overrides,
  };
}

const roadmap: Roadmap = {
  courses: [
    {
      id: "course-1",
      slug: "fundamentals",
      title: "Fundamentals",
      description: "Where everything starts.",
      level: "beginner",
      position: 0,
      lessonCount: 2,
      completedLessonCount: 1,
      lessons: [
        lesson({ id: "l1", slug: "intervals", title: "Intervals", status: "completed" }),
        lesson({ id: "l2", slug: "scales", title: "Major scales", status: "not_started" }),
      ],
    },
    {
      id: "course-2",
      slug: "harmony",
      title: "Harmony",
      description: "Triads and what they do.",
      level: "intermediate",
      position: 1,
      lessonCount: 1,
      completedLessonCount: 0,
      lessons: [lesson({ id: "l3", slug: "triads", title: "Triads", status: "in_progress" })],
    },
  ],
  lessonCount: 3,
  completedLessonCount: 1,
  inProgressLessonCount: 1,
};

const progress: ProgressSummary = {
  lessonCount: 3,
  completedLessonCount: 1,
  inProgressLessonCount: 1,
  byCourse: [],
  continueLessonSlug: "triads",
  continueLessonTitle: "Triads",
};

function mountView() {
  return mount(RoadmapView, {
    global: { stubs: { RouterLink: RouterLinkStub } },
  });
}

async function flush(): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, 0));
}

describe("RoadmapView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.mocked(learningApi.getRoadmap).mockResolvedValue(roadmap);
    vi.mocked(learningApi.getProgress).mockResolvedValue(progress);
    vi.mocked(examsApi.listExams).mockResolvedValue([]);
  });

  it("renders every stage", async () => {
    const wrapper = mountView();
    await flush();

    expect(wrapper.text()).toContain("Fundamentals");
    expect(wrapper.text()).toContain("Harmony");
  });

  it("renders every lesson, whatever its status", async () => {
    const wrapper = mountView();
    await flush();

    // Nothing is hidden or locked - an untouched stage is as reachable as
    // the one in progress.
    expect(wrapper.text()).toContain("Intervals");
    expect(wrapper.text()).toContain("Major scales");
    expect(wrapper.text()).toContain("Triads");
  });

  it("links every lesson card, including ones not started", async () => {
    const wrapper = mountView();
    await flush();

    const hrefs = wrapper.findAllComponents(RouterLinkStub).map((link) => link.props().to);
    expect(hrefs).toContain("/learn/intervals");
    expect(hrefs).toContain("/learn/scales");
    expect(hrefs).toContain("/learn/triads");
  });

  it("links to the skill map", async () => {
    const wrapper = mountView();
    await flush();

    const hrefs = wrapper.findAllComponents(RouterLinkStub).map((link) => link.props().to);
    expect(hrefs).toContain("/skills");
  });

  it("shows each stage's completed count", async () => {
    const wrapper = mountView();
    await flush();

    expect(wrapper.text()).toContain("1/2");
    expect(wrapper.text()).toContain("0/1");
  });

  it("offers the lesson to continue", async () => {
    const wrapper = mountView();
    await flush();

    expect(wrapper.text()).toContain("Continue");
    expect(wrapper.text()).toContain("Triads");
  });

  it("explains an empty curriculum instead of rendering nothing", async () => {
    vi.mocked(learningApi.getRoadmap).mockResolvedValue({
      courses: [],
      lessonCount: 0,
      completedLessonCount: 0,
      inProgressLessonCount: 0,
    });

    const wrapper = mountView();
    await flush();

    expect(wrapper.text()).toContain("seed-curriculum");
  });

  it("reports a failed load", async () => {
    vi.mocked(learningApi.getRoadmap).mockRejectedValue(new Error("network down"));

    const wrapper = mountView();
    await flush();

    // A bare Error carries no server-supplied `detail`, so the view falls
    // back to its own wording rather than surfacing a raw exception message.
    expect(wrapper.text()).toContain("Could not load the roadmap");
    expect(wrapper.text()).not.toContain("Fundamentals");
  });

  it("links to the stage exam at the end of its section", async () => {
    vi.mocked(examsApi.listExams).mockResolvedValue([
      {
        id: "exam-1",
        slug: "fundamentals-exam",
        title: "Fundamentals exam",
        description: "d",
        courseSlug: "fundamentals",
        questionCount: 3,
      },
    ]);

    const wrapper = mountView();
    await flush();
    await flush();

    expect(wrapper.text()).toContain("Take the Fundamentals exam");
    const hrefs = wrapper.findAllComponents(RouterLinkStub).map((link) => link.props().to);
    expect(hrefs).toContain("/exams/fundamentals-exam/attempt");
  });

  it("offers the comprehensive final once every stage is listed", async () => {
    vi.mocked(examsApi.listExams).mockResolvedValue([
      {
        id: "exam-final",
        slug: "final-exam",
        title: "Comprehensive final",
        description: "Everything, together.",
        courseSlug: null,
        questionCount: 10,
      },
    ]);

    const wrapper = mountView();
    await flush();
    await flush();

    expect(wrapper.text()).toContain("Comprehensive final");
    const hrefs = wrapper.findAllComponents(RouterLinkStub).map((link) => link.props().to);
    expect(hrefs).toContain("/exams/final-exam/attempt");
  });

  it("does not stumble when exams fail to load", async () => {
    vi.mocked(examsApi.listExams).mockRejectedValue(new Error("network down"));

    const wrapper = mountView();
    await flush();
    await flush();

    // The roadmap itself is unaffected - exam entry points are an
    // embellishment, not something that should take the page down.
    expect(wrapper.text()).toContain("Fundamentals");
    expect(wrapper.text()).not.toContain("Could not load the roadmap");
  });
});
