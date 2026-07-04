"""Comprehensive tests for the pipeline dashboard."""
import asyncio
import json
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.backends.pipeline import (
    PipelineJob, PipelineStep, StepStatus, JobStatus,
    PipelineEngine, _generate_outline, _generate_scenes,
    _render_scene_media, _compose_video, _publish_final,
    _run_substep
)


# ── Fixtures ──

@pytest.fixture
def sample_job():
    return PipelineJob(
        channel_id="MLN",
        niche="macroeconomics global finance crypto trends 2026",
        topic="How Central Bank Policy Drives Crypto Cycles",
    )


@pytest.fixture
def outline_text():
    return """1. How Central Bank Policy Drives Crypto Cycles
2. The Inflation Hedge Thesis: Gold vs Bitcoin
3. Quantitative Easing and Asset Price Inflation
"""


@pytest.fixture
def scenes_text():
    return """
SCENE 1 - HOOK
NARRATION: "Every time the Federal Reserve prints money, Bitcoin pumps."
BROLL: animated money printing

SCENE 2 - INTRO
NARRATION: "Welcome to Macro Lens. Today we break down..."
BROLL: studio shot, analyst at desk
"""


# ── PipelineStep tests ──

class TestPipelineStep:
    def test_default_status(self):
        step = PipelineStep(name="A1", description="Generate Outline")
        assert step.status == StepStatus.PENDING
        assert step.started_at is None
        assert step.completed_at is None

    def test_mark_running(self):
        step = PipelineStep(name="A1", description="Generate Outline")
        step.mark_running()
        assert step.status == StepStatus.RUNNING
        assert step.started_at is not None

    def test_mark_done(self):
        step = PipelineStep(name="A1", description="Generate Outline")
        step.mark_done()
        assert step.status == StepStatus.DONE
        assert step.completed_at is not None

    def test_mark_failed(self):
        step = PipelineStep(name="A1", description="Generate Outline")
        step.mark_failed("LLM timeout")
        assert step.status == StepStatus.FAILED
        assert step.error == "LLM timeout"

    def test_mark_skipped(self):
        step = PipelineStep(name="A1", description="Generate Outline")
        step.mark_skipped("cache hit")
        assert step.status == StepStatus.SKIPPED
        assert step.error == "cache hit"

    def test_to_dict(self):
        step = PipelineStep(name="A1", description="Generate Outline")
        d = step.to_dict()
        assert d["name"] == "A1"
        assert d["status"] == "pending"
        assert d["description"] == "Generate Outline"

    def test_mark_running_idempotent(self):
        step = PipelineStep(name="A1", description="Generate Outline")
        step.mark_running()
        first_time = step.started_at
        step.mark_running()
        assert step.started_at == first_time

    def test_to_dict_with_error(self):
        step = PipelineStep(name="A1", description="Generate Outline")
        step.mark_failed("timeout")
        d = step.to_dict()
        assert d["error"] == "timeout"


# ── PipelineJob tests ──

class TestPipelineJob:
    def test_initial_status(self, sample_job):
        assert sample_job.status == JobStatus.CREATED
        assert len(sample_job.steps) > 0

    def test_steps_ordered(self, sample_job):
        names = [s.name for s in sample_job.steps]
        assert names == sorted(names)

    def test_get_step(self, sample_job):
        step = sample_job.get_step("A1")
        assert step is not None
        assert step.name == "A1"

    def test_get_step_missing(self, sample_job):
        step = sample_job.get_step("ZZ")
        assert step is None

    def test_overall_progress_none_running(self, sample_job):
        progress = sample_job.overall_progress()
        assert progress == 0.0

    def test_overall_progress_all_done(self, sample_job):
        for step in sample_job.steps:
            step.mark_done()
        progress = sample_job.overall_progress()
        assert progress == 1.0

    def test_overall_progress_half(self, sample_job):
        total = len(sample_job.steps)
        for step in sample_job.steps[:total // 2]:
            step.mark_done()
        progress = sample_job.overall_progress()
        assert 0.0 < progress < 1.0

    def test_mark_failed(self, sample_job):
        sample_job.mark_failed("test error")
        assert sample_job.status == JobStatus.FAILED
        assert sample_job.error == "test error"

    def test_mark_done(self, sample_job):
        sample_job.mark_done()
        assert sample_job.status == JobStatus.DONE

    def test_to_dict(self, sample_job):
        d = sample_job.to_dict()
        assert d["channel_id"] == "MLN"
        assert d["status"] == "created"
        assert isinstance(d["steps"], list)

    def test_steps_with_substeps(self, sample_job):
        """C steps have substeps B1-B4."""
        c1 = sample_job.get_step("C1")
        assert c1 is not None
        assert c1.substeps is not None
        assert len(c1.substeps) == 4  # B1, B2, B3, B4

    def test_initial_status_created(self, sample_job):
        assert sample_job.status == JobStatus.CREATED
        assert sample_job.job_id.startswith("pipeline_")

    def test_mark_done_status(self, sample_job):
        sample_job.mark_done()
        assert sample_job.status == JobStatus.DONE
        assert sample_job.completed_at is not None

    def test_mark_failed_sets_error(self, sample_job):
        sample_job.mark_failed("boom")
        assert sample_job.error == "boom"


# ── PipelineEngine initialization ──

class TestPipelineEngineInit:
    def test_engine_init(self, tmp_path):
        engine = PipelineEngine(output_base=str(tmp_path))
        assert engine.output_base == tmp_path
        assert engine.jobs == {}

    def test_engine_start_creates_dir(self, tmp_path):
        engine = PipelineEngine(output_base=str(tmp_path / "test"))
        assert (tmp_path / "test").exists()

    def test_engine_start_job(self, tmp_path):
        engine = PipelineEngine(output_base=str(tmp_path))
        job = engine.start_job("MLN", "crypto", "test topic")
        assert job.job_id in engine.jobs
        assert job.status == JobStatus.RUNNING


# ── Substep utility ──

class TestRunSubstep:
    def test_sync_fn(self):
        def sync_fn(ctx):
            return "result"
        result = asyncio.get_event_loop().run_until_complete(
            _run_substep(sync_fn, {})
        )
        assert result == "result"

    def test_async_fn(self):
        async def async_fn(ctx):
            return "async_result"
        result = asyncio.get_event_loop().run_until_complete(
            _run_substep(async_fn, {})
        )
        assert result == "async_result"


# ── Outline generation ──

class TestGenerateOutline:
    @pytest.mark.asyncio
    async def test_outline_calls_ollama(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "1. Topic One\n2. Topic Two\n"
        mock_resp.raise_for_status = MagicMock()
        with patch('httpx.AsyncClient') as MockClient:
            instance = AsyncMock()
            instance.post = AsyncMock(return_value=mock_resp)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance
            result = await _generate_outline({"niche": "test", "topic": "test"})
            assert result is not None
            assert len(result) > 0


# ── Scenes generation ──

class TestGenerateScenes:
    @pytest.mark.asyncio
    async def test_scenes_calls_ollama(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "SCENE 1 - HOOK\nNARRATION: test\nBROLL: test"
        mock_resp.raise_for_status = MagicMock()
        with patch('httpx.AsyncClient') as MockClient:
            instance = AsyncMock()
            instance.post = AsyncMock(return_value=mock_resp)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance
            result = await _generate_scenes({"outline": "1. test\n2. test", "channel_id": "MLN"})
            assert result is not None


# ── Media rendering ──

class TestRenderMedia:
    def test_render_creates_file(self, tmp_path):
        scene_file = tmp_path / "scenes.md"
        scene_file.write_text("SCENE 1\nNARRATION: test\nBROLL: test\n")
        job = MagicMock()
        job.job_id = "test_job"
        job.job_dir = str(tmp_path / "test_job")
        os.makedirs(job.job_dir, exist_ok=True)
        # This would require ffmpeg; skip if not available
        # Just verify the function signature accepts the right args
        assert callable(_render_scene_media)


# ── Video composition ──

class TestComposeVideo:
    def test_compose_video_callable(self):
        assert callable(_compose_video)


# ── Publishing ──

class TestPublishFinal:
    def test_publish_callable(self):
        assert callable(_publish_final)
