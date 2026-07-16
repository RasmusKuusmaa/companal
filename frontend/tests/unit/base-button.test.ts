import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import BaseButton from "@/shared/components/base/BaseButton.vue";

describe("BaseButton", () => {
  it("renders slot content", () => {
    const wrapper = mount(BaseButton, { slots: { default: "Save" } });
    expect(wrapper.text()).toBe("Save");
  });

  it("applies the disabled attribute", () => {
    const wrapper = mount(BaseButton, { props: { disabled: true } });
    expect(wrapper.attributes("disabled")).toBeDefined();
  });

  it("defaults to type=button so it never submits an enclosing form by accident", () => {
    const wrapper = mount(BaseButton);
    expect(wrapper.attributes("type")).toBe("button");
  });
});
