import { describe, expect, it } from "vitest";

import { quarterLength } from "@/features/notation/constants";
import {
  appendMeasure,
  createDocument,
  createNote,
  deleteNoteAt,
  deleteNoteBefore,
  deleteNotes,
  diatonicIndex,
  fits,
  fromDiatonicIndex,
  getVoice,
  insertNote,
  locateNote,
  measureCount,
  measureQuarters,
  moveCursor,
  nearestOctaveForStep,
  noteAt,
  noteQuarters,
  notesById,
  notesInRange,
  remainingQuarters,
  removeLastMeasure,
  replaceNote,
  setTempo,
  toggleTieBefore,
  voiceQuarters,
} from "@/features/notation/document";
import type { NotationCursor, NotationDocument, NotePosition } from "@/features/notation/types";

function place(
  doc: NotationDocument,
  cursor: NotationCursor,
  overrides: Parameters<typeof createNote>[0] = {},
) {
  return insertNote(doc, cursor, createNote(overrides));
}

describe("duration maths", () => {
  it("dots add half of what came before", () => {
    expect(quarterLength("quarter", 0)).toBe(1);
    expect(quarterLength("quarter", 1)).toBe(1.5);
    expect(quarterLength("quarter", 2)).toBe(1.75);
  });

  it("every named duration halves the one before it", () => {
    expect(quarterLength("whole", 0)).toBe(4);
    expect(quarterLength("half", 0)).toBe(2);
    expect(quarterLength("eighth", 0)).toBe(0.5);
    expect(quarterLength("16th", 0)).toBe(0.25);
    expect(quarterLength("32nd", 0)).toBe(0.125);
  });

  it("measureQuarters follows the time signature, not just the top number", () => {
    expect(measureQuarters({ beats: 4, beatType: 4 })).toBe(4);
    expect(measureQuarters({ beats: 3, beatType: 4 })).toBe(3);
    expect(measureQuarters({ beats: 6, beatType: 8 })).toBe(3);
    expect(measureQuarters({ beats: 9, beatType: 8 })).toBe(4.5);
  });

  it("noteQuarters and voiceQuarters sum the same way", () => {
    let doc = createDocument({ measureCount: 1 });
    let cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    for (const duration of ["quarter", "eighth", "eighth"] as const) {
      const r = place(doc, cursor, { duration });
      doc = r.document;
      cursor = r.cursor;
    }
    const voice = getVoice(doc, cursor);
    expect(voice).toBeDefined();
    expect(voice!.notes.map(noteQuarters)).toEqual([1, 0.5, 0.5]);
    expect(voiceQuarters(voice!)).toBe(2);
  });
});

describe("document construction", () => {
  it("defaults to a single treble staff with one voice", () => {
    const doc = createDocument();
    expect(doc.staves).toHaveLength(1);
    expect(doc.staves[0]!.clef).toBe("treble");
    expect(doc.staves[0]!.measures[0]!.voices).toHaveLength(1);
  });

  it("numbers voices across staves continuously, not per staff", () => {
    const doc = createDocument({ clefs: ["treble", "bass"], voicesPerStaff: 2 });
    const trebleVoiceIds = doc.staves[0]!.measures[0]!.voices.map((v) => v.id);
    const bassVoiceIds = doc.staves[1]!.measures[0]!.voices.map((v) => v.id);
    expect(trebleVoiceIds).toEqual(["1", "2"]);
    expect(bassVoiceIds).toEqual(["3", "4"]);
  });

  it("measureCount reflects the requested length", () => {
    expect(measureCount(createDocument({ measureCount: 5 }))).toBe(5);
  });
});

describe("insertion", () => {
  it("inserts at the requested index and advances the cursor past it", () => {
    const doc = createDocument({ measureCount: 1 });
    const cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    const r = place(doc, cursor, { step: "G", octave: 4 });
    expect(r.inserted).toBe(true);
    expect(r.cursor.noteIndex).toBe(1);
    expect(getVoice(r.document, cursor)!.notes[0]!.step).toBe("G");
  });

  it("inserts between existing notes rather than only at the end", () => {
    let doc = createDocument({ measureCount: 1 });
    const cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    let r = place(doc, cursor, { step: "C" });
    doc = r.document;
    r = place(doc, r.cursor, { step: "E" });
    doc = r.document;

    r = insertNote(doc, { ...cursor, noteIndex: 1 }, createNote({ step: "D" }));
    const steps = getVoice(r.document, cursor)!.notes.map((n) => n.step);
    expect(steps).toEqual(["C", "D", "E"]);
  });

  it("refuses a note that would overflow the bar, leaving the document untouched", () => {
    let doc = createDocument({ measureCount: 1 });
    let cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    for (let i = 0; i < 4; i += 1) {
      const r = place(doc, cursor, { duration: "quarter" });
      doc = r.document;
      cursor = r.cursor;
    }
    expect(remainingQuarters(doc, cursor)).toBe(0);
    expect(fits(doc, cursor, "quarter", 0)).toBe(false);

    const before = doc;
    const overflow = place(doc, cursor, { duration: "quarter" });
    expect(overflow.inserted).toBe(false);
    expect(overflow.document).toBe(before);
  });

  it("a dot can push a note past what otherwise fits", () => {
    let doc = createDocument({ measureCount: 1 });
    let cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    const r = place(doc, cursor, { duration: "half" });
    doc = r.document;
    cursor = r.cursor;
    expect(remainingQuarters(doc, cursor)).toBe(2);
    expect(fits(doc, cursor, "half", 1)).toBe(false);
    expect(fits(doc, cursor, "half", 0)).toBe(true);
  });
});

describe("replaceNote", () => {
  it("swaps a note in place without moving anything else", () => {
    let doc = createDocument({ measureCount: 1 });
    const cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    const r = place(doc, cursor, { step: "C" });
    doc = r.document;

    doc = replaceNote(doc, cursor, { step: "D", octave: 5 });
    const note = getVoice(doc, cursor)!.notes[0]!;
    expect(note.step).toBe("D");
    expect(note.octave).toBe(5);
  });

  it("refuses a replacement that would no longer fit the bar", () => {
    let doc = createDocument({ measureCount: 1 });
    let cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    for (let i = 0; i < 4; i += 1) {
      const r = place(doc, cursor, { duration: "quarter" });
      doc = r.document;
      cursor = r.cursor;
    }
    const target = { ...cursor, noteIndex: 0 };
    const before = doc;
    const after = replaceNote(doc, target, { duration: "whole" });
    expect(after).toBe(before);
  });
});

describe("deletion", () => {
  it("backspace removes the note before the cursor", () => {
    let doc = createDocument({ measureCount: 1 });
    let cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    let r = place(doc, cursor, { step: "C" });
    doc = r.document;
    r = place(doc, r.cursor, { step: "D" });
    doc = r.document;
    cursor = r.cursor;

    const del = deleteNoteBefore(doc, cursor);
    const notes = getVoice(del.document, cursor)!.notes;
    expect(notes).toHaveLength(1);
    expect(notes[0]!.step).toBe("C");
    expect(del.cursor.noteIndex).toBe(1);
  });

  it("backspace at the start of a voice is a no-op", () => {
    const doc = createDocument({ measureCount: 1 });
    const cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    const del = deleteNoteBefore(doc, cursor);
    expect(del.document).toBe(doc);
    expect(del.cursor).toEqual(cursor);
  });

  it("delete removes the note under the cursor and leaves the cursor in place", () => {
    let doc = createDocument({ measureCount: 1 });
    const start: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    let r = place(doc, start, { step: "C" });
    doc = r.document;
    r = place(doc, r.cursor, { step: "D" });
    doc = r.document;

    const del = deleteNoteAt(doc, start);
    const notes = getVoice(del.document, start)!.notes;
    expect(notes).toHaveLength(1);
    expect(notes[0]!.step).toBe("D");
    expect(del.cursor).toEqual(start);
  });

  it("delete past the end of a voice is a no-op", () => {
    const doc = createDocument({ measureCount: 1 });
    const cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    const del = deleteNoteAt(doc, cursor);
    expect(del.document).toBe(doc);
  });
});

describe("cursor movement", () => {
  it("steps within a measure", () => {
    let doc = createDocument({ measureCount: 1 });
    let cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    let r = place(doc, cursor, {});
    doc = r.document;
    r = place(doc, r.cursor, {});
    doc = r.document;
    cursor = r.cursor;

    expect(moveCursor(doc, cursor, -1).noteIndex).toBe(1);
    expect(moveCursor(doc, cursor, -2).noteIndex).toBe(0);
  });

  it("crosses a barline forwards and back symmetrically", () => {
    let doc = createDocument({ measureCount: 2 });
    let cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    const r = place(doc, cursor, {});
    doc = r.document;
    cursor = r.cursor;

    const forward = moveCursor(doc, cursor, 1);
    expect(forward.measureIndex).toBe(1);
    expect(forward.noteIndex).toBe(0);

    const back = moveCursor(doc, forward, -1);
    expect(back).toEqual(cursor);
  });

  it("refuses to move past either end of the score", () => {
    const doc = createDocument({ measureCount: 1 });
    const cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    expect(moveCursor(doc, cursor, -1)).toEqual(cursor);
    expect(moveCursor(doc, cursor, 5)).toEqual(cursor);
  });
});

describe("diatonic pitch arithmetic", () => {
  it("round-trips through every natural step and a handful of octaves", () => {
    for (const octave of [2, 3, 4, 5]) {
      for (const step of ["C", "D", "E", "F", "G", "A", "B"] as const) {
        expect(fromDiatonicIndex(diatonicIndex(step, octave))).toEqual({ step, octave });
      }
    }
  });

  it("nearestOctaveForStep picks the closer of two candidates", () => {
    const referenceD4 = diatonicIndex("D", 4);
    // B3 is two diatonic steps below D4, B4 is five above - B3 is closer.
    expect(nearestOctaveForStep("B", referenceD4)).toBe(3);
  });

  it("nearestOctaveForStep can return the same octave as the reference", () => {
    const referenceE4 = diatonicIndex("E", 4);
    expect(nearestOctaveForStep("E", referenceE4)).toBe(4);
  });
});

describe("ties", () => {
  it("toggles the note before the cursor", () => {
    let doc = createDocument({ measureCount: 1 });
    const cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    const r = place(doc, cursor, {});
    doc = r.document;

    doc = toggleTieBefore(doc, r.cursor);
    expect(getVoice(doc, cursor)!.notes[0]!.tiedToNext).toBe(true);
    doc = toggleTieBefore(doc, r.cursor);
    expect(getVoice(doc, cursor)!.notes[0]!.tiedToNext).toBe(false);
  });

  it("refuses to tie a rest", () => {
    const doc = createDocument({ measureCount: 1 });
    const cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    const r = place(doc, cursor, { isRest: true });
    const after = toggleTieBefore(r.document, r.cursor);
    expect(after).toBe(r.document);
  });

  it("does nothing with no note before the cursor", () => {
    const doc = createDocument({ measureCount: 1 });
    const cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    expect(toggleTieBefore(doc, cursor)).toBe(doc);
  });
});

describe("locating a note by id", () => {
  it("finds a note anywhere in the score and points just after it", () => {
    let doc = createDocument({ measureCount: 2 });
    const first: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    let r = place(doc, first, {});
    doc = r.document;
    const second: NotationCursor = { staffIndex: 0, measureIndex: 1, voiceId: "1", noteIndex: 0 };
    r = place(doc, second, {});
    doc = r.document;

    const targetId = getVoice(doc, second)!.notes[0]!.id;
    const located = locateNote(doc, targetId);
    expect(located).toEqual({ staffIndex: 0, measureIndex: 1, voiceId: "1", noteIndex: 1 });
  });

  it("returns undefined for an id that isn't in the score", () => {
    const doc = createDocument({ measureCount: 1 });
    expect(locateNote(doc, "not-a-real-id")).toBeUndefined();
  });
});

describe("selecting a range of notes", () => {
  function fourNoteVoice(): { document: NotationDocument; ids: string[] } {
    let doc = createDocument({ measureCount: 1 });
    const start: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    let r = place(doc, start, { step: "C" });
    doc = r.document;
    r = place(doc, r.cursor, { step: "D" });
    doc = r.document;
    r = place(doc, r.cursor, { step: "E" });
    doc = r.document;
    r = place(doc, r.cursor, { step: "F" });
    doc = r.document;
    return { document: doc, ids: getVoice(doc, start)!.notes.map((note) => note.id) };
  }

  it("collects every note between two positions, in document order", () => {
    const { document: doc, ids } = fourNoteVoice();
    const from: NotePosition = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 1 };
    const to: NotePosition = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 3 };

    expect(notesInRange(doc, from, to)).toEqual([ids[1], ids[2], ids[3]]);
  });

  it("doesn't care which end is passed first", () => {
    const { document: doc, ids } = fourNoteVoice();
    const from: NotePosition = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 1 };
    const to: NotePosition = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 3 };

    expect(notesInRange(doc, to, from)).toEqual(notesInRange(doc, from, to));
    expect(notesInRange(doc, to, from)).toEqual([ids[1], ids[2], ids[3]]);
  });

  it("spans a barline within the same voice", () => {
    let doc = createDocument({ measureCount: 2 });
    const first: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    let r = place(doc, first, { step: "C" });
    doc = r.document;
    const second: NotationCursor = { staffIndex: 0, measureIndex: 1, voiceId: "1", noteIndex: 0 };
    r = place(doc, second, { step: "D" });
    doc = r.document;

    const from: NotePosition = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    const to: NotePosition = { staffIndex: 0, measureIndex: 1, voiceId: "1", noteIndex: 0 };

    const cId = getVoice(doc, first)!.notes[0]!.id;
    const dId = getVoice(doc, second)!.notes[0]!.id;
    expect(notesInRange(doc, from, to)).toEqual([cId, dId]);
  });

  it("returns nothing for two ends naming different staves or voices", () => {
    const { document: doc } = fourNoteVoice();
    const a: NotePosition = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    const wrongStaff: NotePosition = { staffIndex: 1, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    const wrongVoice: NotePosition = { staffIndex: 0, measureIndex: 0, voiceId: "2", noteIndex: 0 };

    expect(notesInRange(doc, a, wrongStaff)).toEqual([]);
    expect(notesInRange(doc, a, wrongVoice)).toEqual([]);
  });
});

describe("looking up notes by id", () => {
  it("returns the notes in the order the ids were given, not document order", () => {
    let doc = createDocument({ measureCount: 2 });
    const first: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    let r = place(doc, first, { step: "C" });
    doc = r.document;
    const second: NotationCursor = { staffIndex: 0, measureIndex: 1, voiceId: "1", noteIndex: 0 };
    r = place(doc, second, { step: "D" });
    doc = r.document;

    const cId = getVoice(doc, first)!.notes[0]!.id;
    const dId = getVoice(doc, second)!.notes[0]!.id;

    expect(notesById(doc, 0, "1", [dId!, cId!]).map((note) => note.step)).toEqual(["D", "C"]);
  });

  it("silently skips an id that isn't in this staff+voice", () => {
    const doc = createDocument({ measureCount: 1 });
    expect(notesById(doc, 0, "1", ["not-a-real-id"])).toEqual([]);
  });
});

describe("deleting a range of notes", () => {
  it("removes every named note and leaves the rest untouched", () => {
    let doc = createDocument({ measureCount: 1 });
    const start: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    let r = place(doc, start, { step: "C" });
    doc = r.document;
    r = place(doc, r.cursor, { step: "D" });
    doc = r.document;
    r = place(doc, r.cursor, { step: "E" });
    doc = r.document;

    const notes = getVoice(doc, start)!.notes;
    const [cId, dId] = notes.map((note) => note.id);

    const next = deleteNotes(doc, 0, "1", new Set([cId!, dId!]));
    const remaining = getVoice(next, start)!.notes;
    expect(remaining.map((note) => note.step)).toEqual(["E"]);
  });

  it("removes notes across every measure a voice spans", () => {
    let doc = createDocument({ measureCount: 2 });
    const first: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    let r = place(doc, first, { step: "C" });
    doc = r.document;
    const second: NotationCursor = { staffIndex: 0, measureIndex: 1, voiceId: "1", noteIndex: 0 };
    r = place(doc, second, { step: "D" });
    doc = r.document;

    const cId = getVoice(doc, first)!.notes[0]!.id;
    const dId = getVoice(doc, second)!.notes[0]!.id;

    const next = deleteNotes(doc, 0, "1", new Set([cId!, dId!]));
    expect(getVoice(next, first)!.notes).toHaveLength(0);
    expect(getVoice(next, second)!.notes).toHaveLength(0);
  });
});

describe("measures", () => {
  it("appends a measure to every staff", () => {
    const doc = createDocument({ clefs: ["treble", "bass"], measureCount: 1 });
    const next = appendMeasure(doc);
    expect(measureCount(next)).toBe(2);
    expect(next.staves[1]!.measures).toHaveLength(2);
  });

  it("removes the last measure but never the only one", () => {
    const doc = createDocument({ measureCount: 2 });
    const removed = removeLastMeasure(doc);
    expect(measureCount(removed)).toBe(1);
    expect(removeLastMeasure(removed)).toBe(removed);
  });
});

describe("tempo", () => {
  it("sets a valid tempo", () => {
    const doc = createDocument();
    expect(setTempo(doc, 120).tempo).toBe(120);
  });

  it("clamps to a sane range", () => {
    const doc = createDocument();
    expect(setTempo(doc, 5).tempo).toBe(20);
    expect(setTempo(doc, 5000).tempo).toBe(300);
  });

  it("rounds a fractional tempo", () => {
    expect(setTempo(createDocument(), 90.6).tempo).toBe(91);
  });
});

describe("noteAt", () => {
  it("returns undefined off either end of a voice", () => {
    let doc = createDocument({ measureCount: 1 });
    const cursor: NotationCursor = { staffIndex: 0, measureIndex: 0, voiceId: "1", noteIndex: 0 };
    const r = place(doc, cursor, {});
    doc = r.document;
    expect(noteAt(doc, { ...cursor, noteIndex: -1 })).toBeUndefined();
    expect(noteAt(doc, { ...cursor, noteIndex: 5 })).toBeUndefined();
    expect(noteAt(doc, cursor)).toBeDefined();
  });
});
