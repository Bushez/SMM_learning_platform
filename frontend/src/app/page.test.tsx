import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "./page";
import { Providers } from "./providers";

describe("Home", () => {
  it("shows the product value proposition", () => {
    render(<Providers><Home /></Providers>);

    expect(screen.getByRole("heading", { name: "Учись видеть кадр до нажатия на кнопку" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Выбрать курс" })).toHaveAttribute("href", "/courses");
  });
});
