"""Tests for the multi-stage candidate lesson generation pipeline."""

from pathlib import Path
from unittest.mock import patch

from app.discovery.lesson_extractor import (
    _build_evidence_links,
    _build_review_checklist,
    _draft_lesson,
    _summarize_sources,
    detect_extractable_content,
    generate_candidate_lesson,
)

MOCK_REPO = {
    "github_url": "https://github.com/example/deploy-app",
    "owner": "example",
    "repo_name": "deploy-app",
    "primary_language": "Python",
    "stars": 50,
    "license": "MIT",
}

MOCK_GAP = {
    "gap_id": "gap_deploy",
    "normalized_topic": "container deployment",
    "missing_concepts": ["docker", "kubernetes", "ci-cd"],
}


def _setup_mock_repo(tmp_path: Path):
    """Create a mock repo with README, Dockerfile, and CI workflow."""
    (tmp_path / "README.md").write_text(
        "# Deploy App\n\nA sample container deployment application.\nIt shows best practices.",
        encoding="utf-8",
    )
    (tmp_path / "Dockerfile").write_text("FROM python:3.11\nCOPY . /app", encoding="utf-8")
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "deploy.yml").write_text(
        "name: Deploy\non: push\njobs:\n  deploy:\n    runs-on: ubuntu-latest",
        encoding="utf-8",
    )
    return tmp_path


class TestSummarizeSources:
    def test_summarizes_readme(self, tmp_path):
        _setup_mock_repo(tmp_path)
        content_files = detect_extractable_content(tmp_path)
        summaries = _summarize_sources(tmp_path, content_files)
        readme_summaries = [s for f, s in summaries if f.name == "README.md"]
        assert len(readme_summaries) >= 1
        assert "sample container deployment" in readme_summaries[0].lower() or len(readme_summaries[0]) > 10

    def test_summarizes_dockerfile(self, tmp_path):
        _setup_mock_repo(tmp_path)
        content_files = detect_extractable_content(tmp_path)
        summaries = _summarize_sources(tmp_path, content_files)
        docker_summaries = [s for f, s in summaries if f.name == "Dockerfile"]
        assert len(docker_summaries) == 1
        assert "deployment" in docker_summaries[0].lower() or "container" in docker_summaries[0].lower()

    def test_summarizes_ci_workflow(self, tmp_path):
        _setup_mock_repo(tmp_path)
        content_files = detect_extractable_content(tmp_path)
        summaries = _summarize_sources(tmp_path, content_files)
        ci_summaries = [s for f, s in summaries if "deploy.yml" in f.name]
        assert len(ci_summaries) == 1
        assert "workflow" in ci_summaries[0].lower()


class TestDraftLesson:
    def test_draft_with_summaries(self):
        summaries = [
            (Path("README.md"), "A deployment guide."),
            (Path("Dockerfile"), "Container setup."),
        ]
        body = _draft_lesson("container deployment", ["docker", "kubernetes"], summaries)
        assert "container deployment" in body
        assert "docker" in body
        assert "deployment guide" in body.lower()

    def test_draft_without_summaries(self):
        body = _draft_lesson("container deployment", [], [])
        assert "container deployment" in body
        assert "human analysis" in body.lower()


class TestBuildEvidenceLinks:
    def test_links_point_to_github_blob(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("content", encoding="utf-8")
        summaries = [(readme, "Project docs")]
        result = _build_evidence_links(tmp_path, "example", "deploy-app", summaries)
        assert "https://github.com/example/deploy-app/blob/main/README.md" in result
        assert "Project docs" in result

    def test_empty_summaries(self):
        result = _build_evidence_links(Path("/fake"), "a", "b", [])
        assert "No specific evidence" in result


class TestBuildReviewChecklist:
    def test_has_four_items(self):
        checklist = _build_review_checklist()
        items = [line for line in checklist.split("\n") if line.strip().startswith("- [ ]")]
        assert len(items) == 4

    def test_contains_required_checks(self):
        checklist = _build_review_checklist()
        assert "accurately reflects" in checklist.lower()
        assert "attribution" in checklist.lower()
        assert "proprietary" in checklist.lower()
        assert "propose to source" in checklist.lower()


class TestFullPipeline:
    def test_generated_lesson_has_all_sections(self, tmp_path):
        _setup_mock_repo(tmp_path)
        content_files = detect_extractable_content(tmp_path)

        with patch("app.discovery.lesson_extractor.CANDIDATE_LESSONS_DIR", tmp_path / "candidates"):
            lesson_path = generate_candidate_lesson(tmp_path, MOCK_REPO, MOCK_GAP, content_files)

        assert lesson_path is not None
        assert lesson_path.exists()

        content = lesson_path.read_text(encoding="utf-8")

        # Required sections
        assert "## Summary" in content
        assert "## Source Project" in content
        assert "## Lesson" in content
        assert "## Evidence From Project" in content
        assert "## Attribution and Thanks" in content
        assert "## Review Checklist" in content
        assert "## Coordination TODO" in content

    def test_evidence_links_are_github_urls(self, tmp_path):
        _setup_mock_repo(tmp_path)
        content_files = detect_extractable_content(tmp_path)

        with patch("app.discovery.lesson_extractor.CANDIDATE_LESSONS_DIR", tmp_path / "candidates"):
            lesson_path = generate_candidate_lesson(tmp_path, MOCK_REPO, MOCK_GAP, content_files)

        content = lesson_path.read_text(encoding="utf-8")
        assert "https://github.com/example/deploy-app/blob/main/" in content

    def test_frontmatter_has_generated_by(self, tmp_path):
        _setup_mock_repo(tmp_path)
        content_files = detect_extractable_content(tmp_path)

        with patch("app.discovery.lesson_extractor.CANDIDATE_LESSONS_DIR", tmp_path / "candidates"):
            lesson_path = generate_candidate_lesson(tmp_path, MOCK_REPO, MOCK_GAP, content_files)

        content = lesson_path.read_text(encoding="utf-8")
        assert "generated_by: lesson_extractor_v2" in content
        assert "review_status: needs_review" in content
        assert "status: candidate_external" in content

    def test_review_checklist_has_four_items(self, tmp_path):
        _setup_mock_repo(tmp_path)
        content_files = detect_extractable_content(tmp_path)

        with patch("app.discovery.lesson_extractor.CANDIDATE_LESSONS_DIR", tmp_path / "candidates"):
            lesson_path = generate_candidate_lesson(tmp_path, MOCK_REPO, MOCK_GAP, content_files)

        content = lesson_path.read_text(encoding="utf-8")
        checklist_items = [line for line in content.split("\n") if line.strip().startswith("- [ ]")]
        assert len(checklist_items) == 4
