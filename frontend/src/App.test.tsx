import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";
import { setAccessToken } from "./auth";

vi.mock("./api", async () => {
  const actual = await vi.importActual<typeof import("./api")>("./api");
  return {
    ...actual,
    api: {
      get: vi.fn().mockRejectedValue(new Error("network unavailable in unit test")),
      post: vi.fn(),
      patch: vi.fn(),
      interceptors: { request: { use: vi.fn() } },
    },
  };
});

describe("App", () => {
  it("renders the login screen before authentication", () => {
    setAccessToken(null);
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    expect(document.body.textContent).toContain("Sign in");
  });

  it("renders the dashboard shell when authenticated", () => {
    localStorage.setItem("neurosoc_access_token", "test-token");
    setAccessToken("test-token");
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    expect(document.body.textContent).toContain("Enterprise SOC");
    setAccessToken(null);
  });
});
