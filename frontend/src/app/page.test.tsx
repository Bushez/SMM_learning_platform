import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("Home", () => {
  it("shows the current lesson and its progress", () => {
    render(<Home />);

    expect(
      screen.getByRole("heading", {
        name: "Учись видеть кадр до нажатия на кнопку",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "57");
  });
});
