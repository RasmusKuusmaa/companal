/**
 * Triggers a browser download for an in-memory blob via a throwaway <a>
 * element. Needed instead of a plain hyperlink to the API URL because auth
 * here is a Bearer token attached by axios' interceptor, not a cookie - a
 * raw <a href> GET wouldn't carry it.
 */
export function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
