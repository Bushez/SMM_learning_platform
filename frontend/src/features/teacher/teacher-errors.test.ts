import { describe, expect, it } from "vitest";

import { ApiError } from "@/shared/api/http-client";

import { getTeacherError } from "./teacher-errors";

describe("teacher error messages", () => {
  it("translates structured course publishing issues", () => {
    const error = new ApiError(409, "conflict", "Course cannot be published", [
      "Course needs at least one module",
      "Course needs at least one task",
    ]);

    expect(getTeacherError(error, "fallback")).toEqual({
      title: "Курс пока нельзя опубликовать",
      details: ["Добавьте хотя бы один модуль.", "Добавьте хотя бы одно задание."],
    });
  });

  it("explains an invalid image upload", () => {
    const error = new ApiError(422, "validation_error", "Only JPEG, PNG, and WebP images are allowed");

    expect(getTeacherError(error, "fallback").title).toBe(
      "Поддерживаются только изображения JPEG, PNG и WebP.",
    );
  });
});
