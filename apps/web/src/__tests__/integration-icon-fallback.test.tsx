// @vitest-environment jsdom
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { IntegrationIcon } from "@/features/integrations/components/IntegrationIcon";

/**
 * A device MCP integration has no icon_url and an id that matches no known
 * category, so getToolCategoryIcon returns null — which used to render a blank
 * space on the integrations page. IntegrationIcon must always render something.
 * Remove the fallback and this goes red (empty container, no svg).
 */
describe("IntegrationIcon", () => {
  it("renders a fallback glyph when there is no category icon and no iconUrl", () => {
    const { container } = render(
      <IntegrationIcon integrationId="device-uuid-no-config" iconUrl={null} />,
    );
    expect(container.querySelector("svg")).not.toBeNull();
  });
});
