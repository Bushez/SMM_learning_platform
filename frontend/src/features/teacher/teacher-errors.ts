import messages from "../../../messages/ru.json";

import { ApiError } from "@/shared/api/http-client";

function translatePublishIssue(issue: string): string {
  if (issue === "Course needs at least one module") return messages.teacher.publishNoModule;
  if (issue === "Course needs at least one lesson") return messages.teacher.publishNoLesson;
  if (issue === "Course needs at least one task") return messages.teacher.publishNoTask;
  if (issue.includes("accepted text answer")) return messages.teacher.publishTaskText;
  if (issue.includes("two options") || issue.includes("correct option")) {
    return messages.teacher.publishTaskChoice;
  }
  return messages.teacher.genericActionError;
}

export type TeacherError = {
  title: string;
  details: string[];
};

export function getTeacherError(error: unknown, fallback: string): TeacherError {
  if (!(error instanceof ApiError)) return { title: fallback, details: [] };

  if (error.code === "validation_error" && Array.isArray(error.details)) {
    const field = (error.details[0] as { loc?: unknown[] } | undefined)?.loc?.at(-1);
    if (field === "title") return { title: messages.teacher.contentTitleError, details: [] };
    if (field === "description") return { title: messages.teacher.courseDescriptionError, details: [] };
  }

  if (error.message === "Course cannot be published" && Array.isArray(error.details)) {
    return {
      title: messages.teacher.publishTitle,
      details: [...new Set(error.details.filter((item): item is string => typeof item === "string").map(translatePublishIssue))],
    };
  }

  if (error.message.includes("learner progress")) {
    return { title: messages.teacher.progressLockError, details: [] };
  }
  if (error.message === "Choice tasks require at least two options") {
    return { title: messages.teacher.taskOptionsError, details: [] };
  }
  if (error.message === "Each option requires text or an image") {
    return { title: messages.teacher.taskOptionContentError, details: [] };
  }
  if (error.message === "Single choice tasks require exactly one correct option") {
    return { title: messages.teacher.taskCorrectOptionError, details: [] };
  }
  if (error.message === "Text input tasks require at least one accepted answer") {
    return { title: messages.teacher.taskAcceptedAnswersError, details: [] };
  }
  if (error.message === "Image exceeds the configured upload size limit") {
    return { title: messages.teacher.imageTooLarge, details: [] };
  }
  if (error.message === "Only JPEG, PNG, and WebP images are allowed") {
    return { title: messages.teacher.imageFormat, details: [] };
  }
  if (error.message === "Uploaded file is not a valid image" || error.message === "Image file is empty") {
    return { title: messages.teacher.imageInvalid, details: [] };
  }
  if (error.message.includes("does not match its content")) {
    return { title: messages.teacher.imageMismatch, details: [] };
  }
  return { title: fallback, details: [] };
}
