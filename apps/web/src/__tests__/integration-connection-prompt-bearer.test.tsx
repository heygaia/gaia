// @vitest-environment jsdom
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import IntegrationConnectionPrompt from "@/features/chat/components/bubbles/bot/IntegrationConnectionPrompt";

/**
 * A token-required (bearer) MCP server must collect its token in the secure
 * modal, never by connecting directly (which would fail) and never through chat.
 * The chat connect card used to only wire the OAuth/direct path, so clicking
 * Connect on a bearer server errored instead of prompting for the token.
 * Remove the bearer branch in handleConnect and the first test goes red.
 */

const connectIntegration = vi.fn(async () => ({ status: "connected" }));
let integrations: Array<Record<string, unknown>> = [];

vi.mock("@/features/integrations/hooks/useIntegrations", () => ({
  useIntegrations: () => ({ integrations, connectIntegration }),
}));

// Stub the modal so the test asserts the branch (modal opened) without HeroUI's
// portal internals; it exposes a submit button that fires onSubmit(id, token).
vi.mock("@/features/integrations/components/BearerTokenModal", () => ({
  BearerTokenModal: ({
    isOpen,
    integrationId,
    onSubmit,
  }: {
    isOpen: boolean;
    integrationId: string;
    onSubmit: (id: string, token: string) => Promise<void>;
  }) =>
    isOpen ? (
      <div data-testid="bearer-modal">
        <button
          type="button"
          onClick={() => onSubmit(integrationId, "sk-test-123")}
        >
          submit-token
        </button>
      </div>
    ) : null,
}));

vi.mock("@/components/shared/CollapsibleListWrapper", () => ({
  default: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}));

vi.mock("@/features/chat/utils/toolIcons", () => ({
  getToolCategoryIcon: () => null,
}));

function bearerIntegration() {
  return {
    id: "custom-bearer",
    name: "TokenMCP",
    description: "Needs a token",
    status: "created",
    source: "custom",
    available: true,
    authType: "bearer",
    requiresAuth: true,
  };
}

function oauthIntegration() {
  return {
    id: "custom-oauth",
    name: "OAuthMCP",
    description: "Needs oauth",
    status: "created",
    source: "custom",
    available: true,
    authType: "oauth",
    requiresAuth: true,
  };
}

describe("IntegrationConnectionPrompt — token-required servers", () => {
  beforeEach(() => {
    connectIntegration.mockClear();
    integrations = [];
  });

  it("opens the secure token modal instead of connecting directly", async () => {
    integrations = [bearerIntegration()];
    render(
      <IntegrationConnectionPrompt
        integration_connection_required={{
          integration_id: "custom-bearer",
          message: "Connect it",
          expired: false,
        }}
      />,
    );

    fireEvent.click(screen.getByRole("button"));

    expect(await screen.findByTestId("bearer-modal")).toBeDefined();
    // Never a direct connect for a bearer server — that path can't supply a token.
    expect(connectIntegration).not.toHaveBeenCalled();
  });

  it("submits the entered token through connectIntegration(id, token)", async () => {
    integrations = [bearerIntegration()];
    render(
      <IntegrationConnectionPrompt
        integration_connection_required={{
          integration_id: "custom-bearer",
          message: "Connect it",
          expired: false,
        }}
      />,
    );

    fireEvent.click(screen.getByRole("button"));
    fireEvent.click(await screen.findByText("submit-token"));

    expect(connectIntegration).toHaveBeenCalledWith(
      "custom-bearer",
      "sk-test-123",
    );
  });

  it("uses the direct/OAuth path (no token modal) for a non-bearer server", async () => {
    integrations = [oauthIntegration()];
    render(
      <IntegrationConnectionPrompt
        integration_connection_required={{
          integration_id: "custom-oauth",
          message: "Connect it",
          expired: false,
        }}
      />,
    );

    fireEvent.click(screen.getByRole("button"));

    expect(connectIntegration).toHaveBeenCalledWith("custom-oauth");
    expect(screen.queryByTestId("bearer-modal")).toBeNull();
  });
});
