import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ExportControls from "@/features/notation/components/ExportControls.vue";
import { createDocument } from "@/features/notation/document";

const { exportMusicXml } = vi.hoisted(() => ({ exportMusicXml: vi.fn() }));
const { triggerBlobDownload } = vi.hoisted(() => ({ triggerBlobDownload: vi.fn() }));

vi.mock("@/features/notation/api", () => ({
  notationApi: { exportMusicXml },
}));
vi.mock("@/shared/utils/download", () => ({ triggerBlobDownload }));

beforeEach(() => {
  exportMusicXml.mockReset();
  triggerBlobDownload.mockReset();
});

describe("ExportControls", () => {
  it("downloads the exported blob under a musicxml filename", async () => {
    const blob = new Blob(["<score-partwise/>"], { type: "application/vnd.recordare.musicxml+xml" });
    exportMusicXml.mockResolvedValue(blob);

    const document = createDocument();
    const wrapper = mount(ExportControls, { props: { document } });

    await wrapper.find("button").trigger("click");
    await wrapper.vm.$nextTick();
    await new Promise((resolve) => setTimeout(resolve));

    expect(exportMusicXml).toHaveBeenCalledWith(document);
    expect(triggerBlobDownload).toHaveBeenCalledWith(blob, "score.musicxml");
    expect(wrapper.find('[role="alert"]').exists()).toBe(false);
  });

  it("shows an error and never downloads when the export fails", async () => {
    exportMusicXml.mockRejectedValue(new Error("offline"));

    const wrapper = mount(ExportControls, { props: { document: createDocument() } });

    await wrapper.find("button").trigger("click");
    await wrapper.vm.$nextTick();
    await new Promise((resolve) => setTimeout(resolve));
    await wrapper.vm.$nextTick();

    expect(triggerBlobDownload).not.toHaveBeenCalled();
    expect(wrapper.find('[role="alert"]').text()).toContain("Could not export this score.");
  });
});
