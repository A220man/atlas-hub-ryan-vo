import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import App from "../App.tsx";
import { AuthProvider } from "../context/AuthContext.tsx";

// Mock fetch for API calls
vi.stubGlobal("fetch", vi.fn().mockImplementation((url: string) => {
  if (typeof url === "string" && url.includes("/api/auth/demo-login")) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          access_token: "mock-token",
          token_type: "Bearer",
          user: {
            sub: "demo-analyst",
            email: "analyst@atlas-hub.local",
            roles: ["analyst"],
          },
        }),
    });
  }
  if (typeof url === "string" && url.includes("/api/presentations")) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          items: [
            {
              id: "test-deck-1",
              title: "Test Deck Title",
              topic: "AI/ML developer tools",
              template_id: "modern-navy",
              status: "synthesized",
              aspect_ratio: "16:9",
              slide_count: 5,
              created_by: "analyst@atlas-hub.local",
              created_at: "2026-10-10T00:00:00Z",
              updated_at: "2026-10-10T00:00:00Z",
            },
          ],
          total: 1,
          page: 1,
          size: 10,
          total_pages: 1,
        }),
    });
  }
  return Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({}),
  });
}));

describe("App Root Component", () => {
  it("renders navbar with Atlas Hub brand and header actions", async () => {
    render(
      <AuthProvider>
        <App />
      </AuthProvider>
    );

    expect(screen.getByText("Atlas Hub")).toBeInTheDocument();
    expect(screen.getByText("AI Slide Synthesis & Alignment")).toBeInTheDocument();
    expect(await screen.findByText("+ Synthesize Deck")).toBeInTheDocument();
  });
});
