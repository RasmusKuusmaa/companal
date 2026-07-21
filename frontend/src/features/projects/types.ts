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
