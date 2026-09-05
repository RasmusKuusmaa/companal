/**
 * The wire format for a `NotationDocument`.
 *
 * Field names match the domain type key for key except where a MusicXML-
 * derived term differs (`is_rest`, `tied_to_next`, `beat_type`) - the same
 * convention every other feature's `*.api.ts` follows. Shared here rather
 * than duplicated per caller because every feature that sends or receives a
 * document (starter notation, composition submission, a future musicxml
 * import) needs exactly this mapping and none of it is feature-specific.
 */

import { httpClient } from "@/services/http";

import type {
  ClefName,
  DurationName,
  NotationDocument,
  NotationMeasure,
  NotationNote,
  NotationStaff,
  NotationVoice,
  PitchStep,
} from "./types";

export interface NotationNoteDto {
  id: string;
  step: PitchStep;
  octave: number;
  alter: number;
  duration: DurationName;
  dots: number;
  is_rest: boolean;
  tied_to_next: boolean;
}

export interface NotationVoiceDto {
  id: string;
  notes: NotationNoteDto[];
}

export interface NotationMeasureDto {
  id: string;
  voices: NotationVoiceDto[];
}

export interface NotationStaffDto {
  id: string;
  clef: ClefName;
  name?: string | null;
  measures: NotationMeasureDto[];
}

export interface NotationDocumentDto {
  fifths: number;
  mode: "major" | "minor";
  time: { beats: number; beat_type: number };
  tempo: number;
  staves: NotationStaffDto[];
}

function mapNoteFromDto(dto: NotationNoteDto): NotationNote {
  return {
    id: dto.id,
    step: dto.step,
    octave: dto.octave,
    alter: dto.alter,
    duration: dto.duration,
    dots: dto.dots,
    isRest: dto.is_rest,
    tiedToNext: dto.tied_to_next,
  };
}

function mapNoteToDto(note: NotationNote): NotationNoteDto {
  return {
    id: note.id,
    step: note.step,
    octave: note.octave,
    alter: note.alter,
    duration: note.duration,
    dots: note.dots,
    is_rest: note.isRest,
    tied_to_next: note.tiedToNext,
  };
}

function mapVoiceFromDto(dto: NotationVoiceDto): NotationVoice {
  return { id: dto.id, notes: dto.notes.map(mapNoteFromDto) };
}

function mapVoiceToDto(voice: NotationVoice): NotationVoiceDto {
  return { id: voice.id, notes: voice.notes.map(mapNoteToDto) };
}

function mapMeasureFromDto(dto: NotationMeasureDto): NotationMeasure {
  return { id: dto.id, voices: dto.voices.map(mapVoiceFromDto) };
}

function mapMeasureToDto(measure: NotationMeasure): NotationMeasureDto {
  return { id: measure.id, voices: measure.voices.map(mapVoiceToDto) };
}

function mapStaffFromDto(dto: NotationStaffDto): NotationStaff {
  return {
    id: dto.id,
    clef: dto.clef,
    ...(dto.name ? { name: dto.name } : {}),
    measures: dto.measures.map(mapMeasureFromDto),
  };
}

function mapStaffToDto(staff: NotationStaff): NotationStaffDto {
  return {
    id: staff.id,
    clef: staff.clef,
    name: staff.name ?? null,
    measures: staff.measures.map(mapMeasureToDto),
  };
}

export function notationDocumentFromDto(dto: NotationDocumentDto): NotationDocument {
  return {
    fifths: dto.fifths,
    mode: dto.mode,
    time: { beats: dto.time.beats, beatType: dto.time.beat_type },
    tempo: dto.tempo,
    staves: dto.staves.map(mapStaffFromDto),
  };
}

export function notationDocumentToDto(document: NotationDocument): NotationDocumentDto {
  return {
    fifths: document.fifths,
    mode: document.mode,
    time: { beats: document.time.beats, beat_type: document.time.beatType },
    tempo: document.tempo,
    staves: document.staves.map(mapStaffToDto),
  };
}

export const notationApi = {
  /**
   * Opens an uploaded score as a notation document the editor can load,
   * same as pasting it into `NotationEditor`'s `v-model`. Validated on the
   * backend by the same check a composition version upload goes through
   * (`validate_musicxml_upload`) - a 400 here means the file itself is the
   * problem, not this request.
   */
  async importMusicXml(file: File): Promise<NotationDocument> {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await httpClient.post<NotationDocumentDto>("/notation/import", formData);
    return notationDocumentFromDto(data);
  },
};
