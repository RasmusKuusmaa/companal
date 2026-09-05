import { mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import NotationEditor from "@/features/notation/components/NotationEditor.vue";
import StaffRenderer, { type StaffClick } from "@/features/notation/components/StaffRenderer.vue";
import { insertionIndexAtX, noteAtX, pitchAtY, staveAtPoint } from "@/features/notation/hit-test";
import { createDocument, createNote, getVoice, insertNote } from "@/features/notation/document";
import type { NotationCursor, NotationDocument } from "@/features/notation/types";

// ---------------------------------------------------------------------------
// Click mapping - the pure geometry StaffRenderer resolves a click through.
// jsdom returns a zero-size layout for every element, which is why this is
// tested against the geometry functions directly rather than by dispatching
// a real click at a coordinate on a mounted component.
// ---------------------------------------------------------------------------

const trebleGeometry = { clef: "treble" as const, topLineY: 100, lineSpacing: 10 };

describe("click mapping: pitch from a vertical position", () => {
  it("reads the five treble lines bottom to top as E4 G4 B4 D5 F5", () => {
    const lines = [4, 3, 2, 1, 0].map((line) => pitchAtY(trebleGeometry, 100 + line * 10));
    expect(lines).toEqual([
      { step: "E", octave: 4 },
      { step: "G", octave: 4 },
      { step: "B", octave: 4 },
      { step: "D", octave: 5 },
      { step: "F", octave: 5 },
    ]);
  });

  it("reads the four treble spaces bottom to top as F4 A4 C5 E5", () => {
    const spaces = [3.5, 2.5, 1.5, 0.5].map((line) => pitchAtY(trebleGeometry, 100 + line * 10));
    expect(spaces).toEqual([
      { step: "F", octave: 4 },
      { step: "A", octave: 4 },
      { step: "C", octave: 5 },
      { step: "E", octave: 5 },
    ]);
  });

  it("places middle C one ledger line below the treble staff", () => {
    expect(pitchAtY(trebleGeometry, 100 + 5 * 10)).toEqual({ step: "C", octave: 4 });
  });

  it("reads the bass staff's lines as G2 B2 D3 F3 A3", () => {
    const geometry = { clef: "bass" as const, topLineY: 100, lineSpacing: 10 };
    const lines = [4, 3, 2, 1, 0].map((line) => pitchAtY(geometry, 100 + line * 10));
    expect(lines.map((p) => `${p.step}${p.octave}`)).toEqual(["G2", "B2", "D3", "F3", "A3"]);
  });

  it("puts middle C on the alto clef's middle line", () => {
    const geometry = { clef: "alto" as const, topLineY: 100, lineSpacing: 10 };
    expect(pitchAtY(geometry, 100 + 2 * 10)).toEqual({ step: "C", octave: 4 });
  });

  it("puts middle C on the tenor clef's fourth line", () => {
    const geometry = { clef: "tenor" as const, topLineY: 100, lineSpacing: 10 };
    expect(pitchAtY(geometry, 100 + 1 * 10)).toEqual({ step: "C", octave: 4 });
  });

  it("clamps a wildly out-of-range click rather than reading an absurd octave", () => {
    const farAbove = pitchAtY(trebleGeometry, 100 - 900);
    const farBelow = pitchAtY(trebleGeometry, 100 + 900);
    expect(farAbove.octave).toBeLessThan(9);
    expect(farBelow.octave).toBeGreaterThan(0);
  });
});

describe("click mapping: which measure a point falls in", () => {
  const boxes = [
    {
      staffIndex: 0,
      measureIndex: 0,
      x: 0,
      width: 200,
      topLineY: 100,
      bottomLineY: 140,
      lineSpacing: 10,
    },
    {
      staffIndex: 1,
      measureIndex: 0,
      x: 0,
      width: 200,
      topLineY: 200,
      bottomLineY: 240,
      lineSpacing: 10,
    },
  ];

  it("picks whichever staff the point is vertically nearer to", () => {
    expect(staveAtPoint(boxes, 50, 120)?.staffIndex).toBe(0);
    expect(staveAtPoint(boxes, 50, 220)?.staffIndex).toBe(1);
  });

  it("returns nothing for a point outside every measure", () => {
    expect(staveAtPoint(boxes, 500, 120)).toBeUndefined();
  });
});

describe("click mapping: where in a voice a click belongs", () => {
  const notes = [
    { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0, x: 100, width: 20 },
    { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 1, x: 200, width: 20 },
  ];

  it("inserts before the first note when clicking to its left", () => {
    expect(insertionIndexAtX(notes, 50)).toBe(0);
  });

  it("inserts between two notes when clicking between their heads", () => {
    expect(insertionIndexAtX(notes, 150)).toBe(1);
  });

  it("inserts after the last note when clicking past it", () => {
    expect(insertionIndexAtX(notes, 400)).toBe(2);
  });

  it("finds the note actually under the pointer, for selection", () => {
    expect(noteAtX(notes, 105)?.noteIndex).toBe(0);
    expect(noteAtX(notes, 150)).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// The editor component itself: routing a click, keyboard entry, deletion.
// ---------------------------------------------------------------------------

function oneNoteDocument(): NotationDocument {
  const doc = createDocument({ measureCount: 1 });
  const cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
  return insertNote(doc, cursor, createNote({ step: "C", duration: "quarter" })).document;
}

function latestDoc(wrapper: ReturnType<typeof mount>): NotationDocument {
  const events = wrapper.emitted<[NotationDocument]>("update:modelValue");
  if (!events || events.length === 0) throw new Error("no update:modelValue emitted");
  return events[events.length - 1]![0];
}

class FakeAudioParam {
  value = 0;
  setValueAtTime() {
    return this;
  }
  linearRampToValueAtTime() {
    return this;
  }
  cancelScheduledValues() {
    return this;
  }
}
class FakeOscillator {
  frequency = new FakeAudioParam();
  type = "sine";
  connect() {
    return this;
  }
  start() {}
  stop() {}
}
class FakeGain {
  gain = new FakeAudioParam();
  connect() {
    return this;
  }
}
class FakeAudioContext {
  currentTime = 0;
  destination = {};
  createOscillator() {
    return new FakeOscillator() as unknown as OscillatorNode;
  }
  createGain() {
    return new FakeGain() as unknown as GainNode;
  }
  close() {
    return Promise.resolve();
  }
}

beforeEach(() => {
  vi.stubGlobal("AudioContext", FakeAudioContext);
  vi.stubGlobal("requestAnimationFrame", () => 0);
  vi.stubGlobal("cancelAnimationFrame", () => {});
});
afterEach(() => vi.unstubAllGlobals());

describe("NotationEditor: click routing", () => {
  it("places a new note when the click didn't land on an existing one", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const staff = wrapper.findComponent(StaffRenderer);

    const click: StaffClick = {
      staffIndex: 0,
      measureIndex: 0,
      voiceId: "1",
      insertionIndex: 0,
      step: "G",
      octave: 4,
      noteId: null,
      shiftKey: false,
    };
    staff.vm.$emit("staff-click", click);
    await wrapper.vm.$nextTick();

    const notes = latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes;
    expect(notes).toHaveLength(1);
    expect(notes[0]!.step).toBe("G");
  });

  it("selects rather than duplicates when the click lands on an existing note", async () => {
    const doc = oneNoteDocument();
    const existingId = doc.staves[0]!.measures[0]!.voices[0]!.notes[0]!.id;
    const wrapper = mount(NotationEditor, { props: { modelValue: doc } });
    const staff = wrapper.findComponent(StaffRenderer);

    const click: StaffClick = {
      staffIndex: 0,
      measureIndex: 0,
      voiceId: "1",
      insertionIndex: 0,
      step: "C",
      octave: 4,
      noteId: existingId,
      shiftKey: false,
    };
    staff.vm.$emit("staff-click", click);
    await wrapper.vm.$nextTick();

    // Selecting is not an edit - nothing should have been emitted.
    expect(wrapper.emitted("update:modelValue")).toBeUndefined();
  });
});

describe("NotationEditor: keyboard entry", () => {
  it("places a pitch letter at the cursor with the active duration and dots", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "2" }); // half
    await root.trigger("keydown", { key: "." }); // dotted
    await root.trigger("keydown", { key: "g" });

    const note = latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes[0]!;
    expect(note.step).toBe("G");
    expect(note.duration).toBe("half");
    expect(note.dots).toBe(1);
  });

  it("moves the octave to stay near the previously entered note", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "c" }); // lands near B4 -> C5
    await root.trigger("keydown", { key: "b" }); // should land at B4, not B5

    const notes = latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes;
    expect(notes[0]!.octave).toBe(5);
    expect(notes[1]!.octave).toBe(4);
  });

  it("R enters rest mode for subsequent notes", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "r" });
    await root.trigger("keydown", { key: "e" });

    expect(latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes[0]!.isRest).toBe(true);
  });

  it("T ties the note before the cursor", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "d" });
    await root.trigger("keydown", { key: "t" });

    expect(latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes[0]!.tiedToNext).toBe(true);
  });

  it("K forces a beam break after the note before the cursor", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "4" }); // eighth note duration
    await root.trigger("keydown", { key: "d" });
    await root.trigger("keydown", { key: "k" });

    expect(
      latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes[0]!.beamBreakAfter,
    ).toBe(true);
  });

  it("K does nothing on a note too long to beam", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "d" }); // default quarter-note duration
    await root.trigger("keydown", { key: "k" });

    expect(wrapper.emitted("update:modelValue")).toHaveLength(1); // just the note entry
  });

  it("S slurs the note before the cursor into the next one", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "d" });
    await root.trigger("keydown", { key: "s" });

    expect(latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes[0]!.slurToNext).toBe(true);
  });

  it.each([
    ["u", "staccato"],
    ["v", "accent"],
    ["n", "tenuto"],
    ["m", "marcato"],
  ] as const)("%s sets the %s articulation on the note before the cursor", async (key, kind) => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "d" });
    await root.trigger("keydown", { key });

    expect(latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes[0]!.articulation).toBe(
      kind,
    );
  });

  it("leaves modified keystrokes to the browser", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "c", metaKey: true });

    expect(wrapper.emitted("update:modelValue")).toBeUndefined();
  });
});

describe("NotationEditor: deletion", () => {
  it("backspace removes the note before the cursor", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "c" });
    await root.trigger("keydown", { key: "d" });
    await root.trigger("keydown", { key: "Backspace" });

    const notes = latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes;
    expect(notes).toHaveLength(1);
    expect(notes[0]!.step).toBe("C");
  });

  it("delete removes the note the cursor sits before, after moving there", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "c" });
    await root.trigger("keydown", { key: "d" });
    await root.trigger("keydown", { key: "ArrowLeft" });
    await root.trigger("keydown", { key: "ArrowLeft" });
    await root.trigger("keydown", { key: "Delete" });

    const notes = latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes;
    expect(notes).toHaveLength(1);
    expect(notes[0]!.step).toBe("D");
  });
});

describe("NotationEditor: selection", () => {
  it("shift+arrow extends a selection, and backspace deletes the whole range at once", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "c" });
    await root.trigger("keydown", { key: "d" });
    await root.trigger("keydown", { key: "e" });
    // Anchors on E (the note before the cursor), then extends the
    // selection back onto D.
    await root.trigger("keydown", { key: "ArrowLeft", shiftKey: true });
    await root.trigger("keydown", { key: "Backspace" });

    const notes = latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes;
    expect(notes).toHaveLength(1);
    expect(notes[0]!.step).toBe("C");
  });

  it("moving the cursor without shift collapses the selection", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "c" });
    await root.trigger("keydown", { key: "d" });
    await root.trigger("keydown", { key: "e" });
    await root.trigger("keydown", { key: "ArrowLeft", shiftKey: true }); // selects D, E
    await root.trigger("keydown", { key: "ArrowLeft" }); // plain: collapses it
    await root.trigger("keydown", { key: "Backspace" }); // removes just C, not the old D/E selection

    const notes = latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes;
    expect(notes.map((note) => note.step)).toEqual(["D", "E"]);
  });

  it("shift+click extends the selection to an existing note", async () => {
    let doc = createDocument({ measureCount: 1 });
    const start: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    let r = insertNote(doc, start, createNote({ step: "C" }));
    doc = r.document;
    r = insertNote(doc, r.cursor, createNote({ step: "D" }));
    doc = r.document;
    r = insertNote(doc, r.cursor, createNote({ step: "E" }));
    doc = r.document;
    r = insertNote(doc, r.cursor, createNote({ step: "F" }));
    doc = r.document;
    const notes = getVoice(doc, start)!.notes;
    const dId = notes[1]!.id;
    const fId = notes[3]!.id;

    const wrapper = mount(NotationEditor, { props: { modelValue: doc } });
    const staff = wrapper.findComponent(StaffRenderer);

    staff.vm.$emit("staff-click", {
      staffIndex: 0,
      measureIndex: 0,
      voiceId: "1",
      insertionIndex: 0,
      step: "F",
      octave: 4,
      noteId: fId,
      shiftKey: false,
    } satisfies StaffClick);
    staff.vm.$emit("staff-click", {
      staffIndex: 0,
      measureIndex: 0,
      voiceId: "1",
      insertionIndex: 0,
      step: "D",
      octave: 4,
      noteId: dId,
      shiftKey: true,
    } satisfies StaffClick);
    await wrapper.vm.$nextTick();

    const root = wrapper.find("[tabindex]");
    await root.trigger("keydown", { key: "Backspace" });

    const remaining = latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes;
    expect(remaining.map((note) => note.step)).toEqual(["C"]);
  });
});

describe("NotationEditor: copy and paste", () => {
  it("copies the selection and pastes fresh copies elsewhere", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 2 }) },
    });
    const root = wrapper.find("[tabindex]");
    const staff = wrapper.findComponent(StaffRenderer);

    await root.trigger("keydown", { key: "c" });
    await root.trigger("keydown", { key: "d" });

    const dId = latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes[1]!.id;

    // Select just D: click it, then shift-click it again - a one-note range.
    const click = {
      staffIndex: 0,
      measureIndex: 0,
      voiceId: "1",
      insertionIndex: 0,
      step: "D" as const,
      octave: 4,
      noteId: dId,
    };
    staff.vm.$emit("staff-click", { ...click, shiftKey: false } satisfies StaffClick);
    staff.vm.$emit("staff-click", { ...click, shiftKey: true } satisfies StaffClick);
    await wrapper.vm.$nextTick();

    await root.trigger("keydown", { key: "c", ctrlKey: true });
    await root.trigger("keydown", { key: "ArrowRight" }); // into the empty second measure
    await root.trigger("keydown", { key: "v", ctrlKey: true });

    const doc = latestDoc(wrapper);
    const secondMeasureNotes = doc.staves[0]!.measures[1]!.voices[0]!.notes;
    expect(secondMeasureNotes.map((note) => note.step)).toEqual(["D"]);
    expect(secondMeasureNotes[0]!.id).not.toBe(dId);

    // The original is untouched.
    const firstMeasureNotes = doc.staves[0]!.measures[0]!.voices[0]!.notes;
    expect(firstMeasureNotes.map((note) => note.step)).toEqual(["C", "D"]);
  });

  it("pastes as much as fits and leaves the rest out", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 2 }) },
    });
    const root = wrapper.find("[tabindex]");
    const staff = wrapper.findComponent(StaffRenderer);

    await root.trigger("keydown", { key: "c" });
    await root.trigger("keydown", { key: "d" });
    await root.trigger("keydown", { key: "e" }); // measure 0: 3 of 4 quarters used
    await root.trigger("keydown", { key: "ArrowRight" }); // into measure 1
    await root.trigger("keydown", { key: "f" });
    await root.trigger("keydown", { key: "g" }); // measure 1: F, G

    const measure1Notes = latestDoc(wrapper).staves[0]!.measures[1]!.voices[0]!.notes;
    const fId = measure1Notes[0]!.id;
    const gId = measure1Notes[1]!.id;

    const clickBase = { staffIndex: 0, measureIndex: 1, voiceId: "1", insertionIndex: 0, octave: 4 };
    staff.vm.$emit("staff-click", {
      ...clickBase,
      step: "G",
      noteId: gId,
      shiftKey: false,
    } satisfies StaffClick);
    staff.vm.$emit("staff-click", {
      ...clickBase,
      step: "F",
      noteId: fId,
      shiftKey: true,
    } satisfies StaffClick);
    await wrapper.vm.$nextTick();

    await root.trigger("keydown", { key: "c", ctrlKey: true }); // copies F, G

    // Back to the end of measure 0, which has room for exactly one more quarter note.
    await root.trigger("keydown", { key: "ArrowLeft" });
    await root.trigger("keydown", { key: "ArrowLeft" });
    await root.trigger("keydown", { key: "v", ctrlKey: true });

    const measure0Notes = latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes;
    expect(measure0Notes.map((note) => note.step)).toEqual(["C", "D", "E", "F"]);
  });

  it("ctrl+v with nothing copied is a no-op", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "v", ctrlKey: true });

    expect(wrapper.emitted("update:modelValue")).toBeUndefined();
  });
});

describe("NotationEditor: undo and redo", () => {
  it("ctrl+z steps back one edit at a time", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "c" });
    await root.trigger("keydown", { key: "d" });
    await root.trigger("keydown", { key: "z", ctrlKey: true });

    const notes = latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes;
    expect(notes.map((note) => note.step)).toEqual(["C"]);
  });

  it("ctrl+shift+z re-applies what ctrl+z just undid", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "c" });
    await root.trigger("keydown", { key: "d" });
    await root.trigger("keydown", { key: "z", ctrlKey: true });
    await root.trigger("keydown", { key: "z", ctrlKey: true, shiftKey: true });

    const notes = latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes;
    expect(notes.map((note) => note.step)).toEqual(["C", "D"]);
  });

  it("a new edit after undoing clears what would have been redone", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "c" });
    await root.trigger("keydown", { key: "d" });
    await root.trigger("keydown", { key: "e" });
    await root.trigger("keydown", { key: "z", ctrlKey: true }); // back to C, D
    await root.trigger("keydown", { key: "f" }); // a fresh edit: C, D, F
    await root.trigger("keydown", { key: "z", ctrlKey: true, shiftKey: true }); // nothing to redo now

    const notes = latestDoc(wrapper).staves[0]!.measures[0]!.voices[0]!.notes;
    expect(notes.map((note) => note.step)).toEqual(["C", "D", "F"]);
  });

  it("ctrl+z with nothing to undo is a no-op", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "z", ctrlKey: true });

    expect(wrapper.emitted("update:modelValue")).toBeUndefined();
  });
});

describe("NotationEditor: keyboard shortcut help", () => {
  it("? opens the panel, and a letter typed while it's open doesn't land a note", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");

    await root.trigger("keydown", { key: "?" });
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true);

    await root.trigger("keydown", { key: "d" });
    expect(wrapper.emitted("update:modelValue")).toBeUndefined();
  });

  it("the toolbar button opens the panel too", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });

    await wrapper.find('button[aria-label="Keyboard shortcuts"]').trigger("click");

    expect(wrapper.find('[role="dialog"]').exists()).toBe(true);
  });

  it("the close button dismisses the panel", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
    });
    const root = wrapper.find("[tabindex]");
    await root.trigger("keydown", { key: "?" });

    await wrapper.find('button[aria-label="Close"]').trigger("click");

    expect(wrapper.find('[role="dialog"]').exists()).toBe(false);
  });

  it("Escape dismisses the panel", async () => {
    const wrapper = mount(NotationEditor, {
      props: { modelValue: createDocument({ measureCount: 1 }) },
      attachTo: document.body,
    });
    const root = wrapper.find("[tabindex]");
    await root.trigger("keydown", { key: "?" });
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true);

    window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[role="dialog"]').exists()).toBe(false);
    wrapper.unmount();
  });
});
