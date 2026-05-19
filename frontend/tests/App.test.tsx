import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { App } from "@/App";

describe("App shell", () => {
  it("renders the TimeTrack brand", async () => {
    render(<App />);

    expect(await screen.findByRole("banner")).toHaveTextContent(/timetrack/i);
  });
});
