// @ts-expect-error — JSON imports lack type declarations
import lessonsData from "../content/generated/lessons.json";
// @ts-expect-error — JSON imports lack type declarations
import reposData from "../content/generated/repos.json";
// @ts-expect-error — JSON imports lack type declarations
import tagsData from "../content/generated/tags.json";
// @ts-expect-error — JSON imports lack type declarations
import phasesData from "../content/generated/phases.json";
// @ts-expect-error — JSON imports lack type declarations
import lessonTypesData from "../content/generated/lesson_types.json";

export interface Lesson {
  id: string;
  title: string;
  summary: string;
  repo_id: string;
  repo_name: string;
  repo_owner: string;
  repo_slug: string;
  source_path: string;
  source_url: string;
  project_url: string;
  date: string | null;
  updated: string | null;
  phase: string | null;
  lesson_type: string | null;
  status: string;
  tags: string[];
  source_files: string[];
  related_prs: string[];
  related_issues: string[];
  related_commits: string[];
  audience: string[];
  content: string;
  word_count: number;
  reading_minutes: number;
}

export interface Repo {
  id: string;
  name: string;
  owner: string;
  repo: string;
  branch: string;
  project_url: string;
  lesson_count: number;
  tags: string[];
  recent_date: string | null;
}

export interface TagEntry {
  tag: string;
  count: number;
  lesson_ids: string[];
}

export interface PhaseEntry {
  phase: string;
  count: number;
  lesson_ids: string[];
}

export interface LessonTypeEntry {
  lesson_type: string;
  count: number;
  lesson_ids: string[];
}

export function getLessons(): Lesson[] {
  return lessonsData as unknown as Lesson[];
}

export function getRepos(): Repo[] {
  return reposData as unknown as Repo[];
}

export function getTags(): TagEntry[] {
  return tagsData as unknown as TagEntry[];
}

export function getPhases(): PhaseEntry[] {
  return phasesData as unknown as PhaseEntry[];
}

export function getLessonTypes(): LessonTypeEntry[] {
  return lessonTypesData as unknown as LessonTypeEntry[];
}

export function getBlockSubLessons(indexId: string): Lesson[] {
  const blockPrefix = indexId.replace(/-index$/, '');
  return getLessons()
    .filter((l) => l.id.startsWith(blockPrefix + '-') && l.id !== indexId)
    .sort((a, b) => a.id.localeCompare(b.id));
}
