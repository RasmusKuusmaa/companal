import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import StaffRenderer from "@/features/notation/components/StaffRenderer.vue";
import { useNotationEditor } from "@/features/notation/composables/useNotationEditor";
import { createDocument, createNote, createSatbDocument, insertNote } from "@/features/notation/document";
import type { NotationCursor } from "@/features/notation/types";
import { buildBeams, buildVoice, stemDirectionForVoice } from "@/features/notation/vexflow";

describe("createSatbDocument", () => {
  it("builds a treble+bass grand staff with two voices per staff", () => {
    const doc = createSatbDocument({ measureCount: 3 });
    expect(doc.staves).toHaveLength(2);
    expect(doc.staves[0]!.clef).toBe("treble");
    expect(doc.staves[1]!.clef).toBe("bass");
    expect(doc.staves[0]!.measures[0]!.voices.map((v) => v.id)).toEqual(["1", "2"]);
    expect(doc.staves[1]!.measures[0]!.voices.map((v) => v.id)).toEqual(["3", "4"]);
    expect(doc.staves[0]!.measures).toHaveLength(3);
  });
});

describe("stemDirectionForVoice", () => {
  it("leaves a single voice to VexFlow's own default", () => {
    expect(stemDirectionForVoice(0, 1)).toBeUndefined();
  });

  it("alternates up/down starting with the first voice", () => {
    expect(stemDirectionForVoice(0, 2)).toBe(1);
    expect(stemDirectionForVoice(1, 2)).toBe(-1);
    expect(stemDirectionForVoice(2, 4)).toBe(1);
    expect(stemDirectionForVoice(3, 4)).toBe(-1);
  });
});

describe("buildBeams", () => {
  function eighthsDocument(count: number): ReturnType<typeof createDocument> {
    let doc = createDocument({ measureCount: 1 });
    let cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    for (let i = 0; i < count; i += 1) {
      const result = insertNote(doc, cursor, createNote({ duration: "eighth" }));
      doc = result.document;
      cursor = result.cursor;
    }
    return doc;
  }

  it("groups eighths in pairs by default", () => {
    const doc = eighthsDocument(4);
    const voice = doc.staves[0]!.measures[0]!.voices[0]!;
    const built = buildVoice(doc, voice, "treble");

    const beams = buildBeams(built);
    expect(beams.map((beam) => beam.getNotes().length)).toEqual([2, 2]);
  });

  it("splits a beam wherever a note forces a break, without touching the rest", () => {
    const doc = eighthsDocument(4);
    const voice = doc.staves[0]!.measures[0]!.voices[0]!;
    voice.notes[0]!.beamBreakAfter = true;
    const built = buildVoice(doc, voice, "treble");

    const beams = buildBeams(built);
    // Note 0 stands alone (no beam), notes 1-2 still pair up by default,
    // and note 3 is left over with no partner.
    expect(beams).toHaveLength(1);
    expect(beams[0]!.getNotes()).toHaveLength(2);
  });
});

describe("staff and voice selection", () => {
  it("setActiveStaff moves entry to the target staff without inserting a note", () => {
    const editor = useNotationEditor(createDocument({ clefs: ["treble", "bass"] }));

    expect(editor.cursor.value.staffIndex).toBe(0);
    editor.setActiveStaff(1);
    expect(editor.cursor.value.staffIndex).toBe(1);
    expect(editor.cursor.value.voiceId).toBe("2");
    expect(editor.document.value.staves[1]!.measures[0]!.voices[0]!.notes).toHaveLength(0);
  });

  it("setActiveStaff is a no-op for an out-of-range index", () => {
    const editor = useNotationEditor(createDocument());
    editor.setActiveStaff(5);
    expect(editor.cursor.value.staffIndex).toBe(0);
  });

  it("setActiveVoice switches within the active staff and updates the voice list", () => {
    const editor = useNotationEditor(createSatbDocument());

    expect(editor.activeStaffVoices.value.map((v) => v.id)).toEqual(["1", "2"]);
    editor.setActiveVoice("2");
    expect(editor.cursor.value.voiceId).toBe("2");

    editor.setActiveStaff(1);
    expect(editor.activeStaffVoices.value.map((v) => v.id)).toEqual(["3", "4"]);
  });

  it("setActiveVoice is a no-op for a voice id on a different staff", () => {
    const editor = useNotationEditor(createSatbDocument());
    editor.setActiveVoice("4"); // belongs to staff 1; cursor starts on staff 0
    expect(editor.cursor.value.voiceId).toBe("1");
  });

  it("placing a note targets the active voice, not the others sharing its staff", () => {
    const editor = useNotationEditor(createSatbDocument());
    editor.setActiveVoice("2");
    editor.placeStep("C");
    expect(editor.document.value.staves[0]!.measures[0]!.voices[1]!.notes).toHaveLength(1);
    expect(editor.document.value.staves[0]!.measures[0]!.voices[0]!.notes).toHaveLength(0);
  });
});

describe("locked staves", () => {
  it("refuses to place a note on a locked staff", () => {
    const editor = useNotationEditor(createDocument({ clefs: ["treble", "bass"] }), {
      lockedStaffIndices: [1],
    });

    editor.setActiveStaff(1);
    const placed = editor.placeStep("C");

    expect(placed).toBe(false);
    expect(editor.lastRefusal.value).toBe("This line is given and can't be edited.");
    expect(editor.document.value.staves[1]!.measures[0]!.voices[0]!.notes).toHaveLength(0);
  });

  it("refuses delete on a locked staff", () => {
    const unlocked = useNotationEditor(createDocument({ clefs: ["treble", "bass"] }));
    unlocked.setActiveStaff(1);
    unlocked.placeStep("C");
    const withNote = unlocked.document.value;

    const editor = useNotationEditor(withNote, { lockedStaffIndices: [1] });
    editor.setActiveStaff(1);

    editor.deleteBefore();
    expect(editor.document.value.staves[1]!.measures[0]!.voices[0]!.notes).toHaveLength(1);
    expect(editor.lastRefusal.value).toBe("This line is given and can't be edited.");
  });

  it("leaves an unlocked staff fully editable", () => {
    const editor = useNotationEditor(createDocument({ clefs: ["treble", "bass"] }), {
      lockedStaffIndices: [1],
    });
    const placed = editor.placeStep("C"); // staff 0, unlocked
    expect(placed).toBe(true);
  });
});

describe("StaffRenderer", () => {
  it("renders a braced grand staff without throwing", () => {
    const doc = createSatbDocument({ measureCount: 4 });
    expect(() =>
      mount(StaffRenderer, { props: { document: doc, measuresPerSystem: 2 } }),
    ).not.toThrow();
  });
});
