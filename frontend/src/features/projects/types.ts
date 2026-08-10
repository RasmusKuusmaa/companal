export interface Composition {
  id: string;
  title: string;
  versionCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface Version {
  id: string;
  compositionId: string;
  versionNumber: number;
  originalFilename: string;
  fileSize: number;
  createdAt: string;
}

export interface CreateCompositionPayload {
  title: string;
}

export interface RenameCompositionPayload {
  title: string;
}

/** One engine's algorithmic (non-AI) score and findings. */
export interface EngineAnalysis {
  score: number;
  strengths: string[];
  issues: string[];
}

export interface UnavailableEngine {
  engine: string;
  reason: string;
}

export interface CompositionAnalysis {
  compositionId: string;
  versionId: string;
  versionNumber: number;
  overallScore: number;
  melody: EngineAnalysis | null;
  harmony: EngineAnalysis | null;
  rhythm: EngineAnalysis | null;
  unavailable: UnavailableEngine[];
  analyzedAt: string;
}
