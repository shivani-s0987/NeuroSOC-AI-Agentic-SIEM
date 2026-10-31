import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";
import { setAccessToken } from "./auth";

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
    setAccessToken("test-token");
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    expect(document.body.textContent).toContain("AI-Assisted SOC");
    setAccessToken(null);
  });
});
