import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/features/learning/api/learning.api", () => ({
  learningApi: {
    getRoadmap: vi.fn(),
    getProgress: vi.fn(),
    getLesson: vi.fn(),
    answerQuiz: vi.fn(),
    markStepSeen: vi.fn(),
    completeLesson: vi.fn(),
  },
}));

import { learningApi } from "@/features/learning/api/learning.api";
import MultipleChoiceStep from "@/features/learning/components/MultipleChoiceStep.vue";
import { useLearningStore } from "@/features/learning/stores/learning.store";
import type { Lesson, QuizStep } from "@/features/learning/types";

const QUIZ: QuizStep = {
  id: "step-2",
  slug: "intervals-quiz",
  position: 1,
  kind: "quiz",
  question: "How many semitones in a perfect fifth?",
  choices: ["5", "7", "8"],
};

const LESSON: Lesson = {
  id: "lesson-1",
  slug: "intervals",
  title: "Intervals",
  summary: "Distances between notes.",
  position: 0,
  estimatedMinutes: 12,
  course: { id: "course-1", slug: "fundamentals", title: "Fundamentals" },
  status: "not_started",
  currentStepId: null,
  completedAt: null,
  steps: [
    { id: "step-1", slug: "intervals-reading", position: 0, kind: "reading", markdown: "# Hello" },
    QUIZ,
    { id: "step-3", slug: "intervals-recap", position: 2, kind: "reading", markdown: "## Recap" },
  ],
  previousLessonSlug: null,
  nextLessonSlug: "scales",
};

/** The nth choice radio, asserted to exist so a missing one fails loudly. */
function radio(wrapper: ReturnType<typeof mount>, index: number) {
  const inputs = wrapper.findAll("input[type='radio']");
  const found = inputs[index];
  if (!found) throw new Error(`No radio at index ${index} (found ${inputs.length}).`);
  return found;
}

async function flush(): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, 0));
}

describe("lesson player", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.mocked(learningApi.getLesson).mockResolvedValue(structuredClone(LESSON));
    vi.mocked(learningApi.markStepSeen).mockResolvedValue({
      lessonId: LESSON.id,
      currentStepId: "step-1",
      status: "in_progress",
    });
  });

  describe("step navigation", () => {
    it("opens at the first step", async () => {
      const store = useLearningStore();
      await store.openLesson("intervals");

      expect(store.stepIndex).toBe(0);
      expect(store.isFirstStep).toBe(true);
      expect(store.isLastStep).toBe(false);
    });

    it("resumes at the step last reached", async () => {
      vi.mocked(learningApi.getLesson).mockResolvedValue({
        ...structuredClone(LESSON),
        currentStepId: "step-2",
      });

      const store = useLearningStore();
      await store.openLesson("intervals");

      expect(store.stepIndex).toBe(1);
      expect(store.currentStep?.slug).toBe("intervals-quiz");
    });

    it("walks forwards and backwards", async () => {
      const store = useLearningStore();
      await store.openLesson("intervals");

      store.nextStep();
      expect(store.currentStep?.slug).toBe("intervals-quiz");

      store.nextStep();
      expect(store.isLastStep).toBe(true);

      store.previousStep();
      expect(store.currentStep?.slug).toBe("intervals-quiz");
    });

    it("refuses to walk off either end", async () => {
      const store = useLearningStore();
      await store.openLesson("intervals");

      store.previousStep();
      expect(store.stepIndex).toBe(0);

      store.goToStep(2);
      store.nextStep();
      expect(store.stepIndex).toBe(2);
    });

    it("keeps reading a lesson possible when progress reporting fails", async () => {
      vi.mocked(learningApi.markStepSeen).mockRejectedValue(new Error("offline"));

      const store = useLearningStore();
      await store.openLesson("intervals");
      await store.markSeen("intervals-reading");

      // Bookkeeping failing must not break the lesson in front of the student.
      expect(store.currentStep?.slug).toBe("intervals-reading");
    });
  });

  describe("quiz submission", () => {
    function mountQuiz() {
      return mount(MultipleChoiceStep, { props: { step: QUIZ } });
    }

    beforeEach(() => {
      vi.mocked(learningApi.answerQuiz).mockResolvedValue({
        attemptId: "attempt-1",
        isCorrect: false,
        correctIndex: 1,
        explanation: "Seven semitones - count them on a keyboard.",
      });
    });

    it("cannot be submitted before a choice is made", async () => {
      const store = useLearningStore();
      await store.openLesson("intervals");

      const wrapper = mountQuiz();
      expect(wrapper.find("button").attributes("disabled")).toBeDefined();
    });

    it("submits the selected choice", async () => {
      const store = useLearningStore();
      await store.openLesson("intervals");

      const wrapper = mountQuiz();
      await radio(wrapper, 2).setValue();
      await wrapper.find("button").trigger("click");
      await flush();

      expect(learningApi.answerQuiz).toHaveBeenCalledWith("intervals", "intervals-quiz", 2);
    });

    it("reveals the explanation and the right answer after a wrong one", async () => {
      const store = useLearningStore();
      await store.openLesson("intervals");

      const wrapper = mountQuiz();
      await radio(wrapper, 0).setValue();
      await wrapper.find("button").trigger("click");
      await flush();

      expect(wrapper.text()).toContain("Not quite.");
      // Retries are free, so withholding the answer would only make it a
      // guessing game - the explanation is the part that teaches.
      expect(wrapper.text()).toContain("Seven semitones");
      expect(wrapper.text()).toContain("correct");
    });

    it("says so when the answer was right", async () => {
      vi.mocked(learningApi.answerQuiz).mockResolvedValue({
        attemptId: "attempt-2",
        isCorrect: true,
        correctIndex: 1,
        explanation: "Seven.",
      });

      const store = useLearningStore();
      await store.openLesson("intervals");

      const wrapper = mountQuiz();
      await radio(wrapper, 1).setValue();
      await wrapper.find("button").trigger("click");
      await flush();

      expect(wrapper.text()).toContain("Correct.");
    });

    it("lets the student try again", async () => {
      const store = useLearningStore();
      await store.openLesson("intervals");

      const wrapper = mountQuiz();
      await radio(wrapper, 0).setValue();
      await wrapper.find("button").trigger("click");
      await flush();

      const retry = wrapper.findAll("button").find((b) => b.text() === "Try again");
      await retry?.trigger("click");
      await flush();

      expect(wrapper.text()).not.toContain("Not quite.");
      expect(store.quizResults["intervals-quiz"]).toBeUndefined();
    });

    it("keeps a verdict when the student navigates away and back", async () => {
      const store = useLearningStore();
      await store.openLesson("intervals");
      await store.answerQuiz("intervals-quiz", 0);

      const wrapper = mountQuiz();

      expect(wrapper.text()).toContain("Not quite.");
    });

    it("reports a failed submission", async () => {
      vi.mocked(learningApi.answerQuiz).mockRejectedValue(new Error("offline"));

      const store = useLearningStore();
      await store.openLesson("intervals");

      const wrapper = mountQuiz();
      await radio(wrapper, 1).setValue();
      await wrapper.find("button").trigger("click");
      await flush();

      expect(wrapper.text()).toContain("Could not submit that answer.");
    });
  });

  describe("completion", () => {
    it("marks the lesson complete and reports the next one", async () => {
      vi.mocked(learningApi.completeLesson).mockResolvedValue({
        lessonId: LESSON.id,
        status: "completed",
        completedAt: "2026-09-04T10:00:00Z",
        nextLessonSlug: "scales",
      });

      const store = useLearningStore();
      await store.openLesson("intervals");
      const next = await store.completeLesson();

      expect(next).toBe("scales");
      expect(store.lesson?.status).toBe("completed");
    });
  });
});
