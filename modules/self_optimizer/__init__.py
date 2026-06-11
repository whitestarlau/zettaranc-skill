"""Darwin Self-Optimizer for zettaranc-skill.

V1 dry-run mode: 集成 ratchet + reflex_blacklist + break_signal,
不修改 SKILL.md, 产 optimization_drafts/ 供人工 review.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from modules.self_optimizer.phase1_baseline import phase1_baseline
from modules.self_optimizer.phase2_hillclimb import (
    RoundResult,
    check_break_signal,
    run_round,
)
from modules.self_optimizer.phase3_report import (
    append_improvement_log,
    write_optimization_draft,
    write_results_tsv,
)


class SelfOptimizer:
    """Self-optimizer orchestrator.

    Args:
        target: 优化目标 (trading | skill). V1 仅支持 trading.
        rounds: 最大迭代轮数 (默认 3).
        mode: dry_run (V1) | auto_revert (V2).
        review_months: 基线评估用的最近月份数 (默认 3).
    """

    def __init__(
        self,
        target: Literal["trading", "skill"] = "trading",
        rounds: int = 3,
        mode: Literal["dry_run", "auto_revert"] = "dry_run",
        review_months: int = 3,
    ) -> None:
        if target not in ("trading", "skill"):
            raise ValueError(f"V1 仅支持 trading/skill, 收到: {target}")
        if mode not in ("dry_run", "auto_revert"):
            raise ValueError(f"V1 仅支持 dry_run/auto_revert, 收到: {mode}")
        if mode == "auto_revert":
            raise NotImplementedError("V1 不支持 auto_revert, 将在 V2 实现")
        if rounds < 1 or rounds > 10:
            raise ValueError(f"rounds 必须在 [1, 10], 收到: {rounds}")

        self.target = target
        self.rounds = rounds
        self.mode = mode
        self.review_months = review_months
        self.log_dir = Path("logs")
        self.draft_dir = Path("optimization_drafts")
        self.results_tsv = self.log_dir / "results.tsv"

    def run(self) -> dict:
        """Phase 1 → 2 → 3 完整跑一次."""
        baseline = self.phase1_baseline()
        history: list[RoundResult] = []
        for n in range(1, self.rounds + 1):
            old_score = history[-1].new_score if history else baseline
            result = run_round(
                round_n=n,
                old_score=old_score,
                target=self.target,
                history=history,
            )
            history.append(result)
            if result.status == "break":
                break
        return self.phase3_report(history)

    def phase1_baseline(self) -> float:
        return phase1_baseline(target=self.target, review_months=self.review_months)

    def phase3_report(self, history: list[RoundResult]) -> dict:
        from datetime import datetime

        run_id = datetime.now().strftime("%Y-%m-%d-r%H%M%S")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.draft_dir.mkdir(parents=True, exist_ok=True)
        tsv_path = write_results_tsv(self.results_tsv, run_id, history)
        for r in history:
            draft_path = write_optimization_draft(self.draft_dir, run_id, r)
            append_improvement_log(self.log_dir, r)
        return {
            "run_id": run_id,
            "rounds": len(history),
            "keep": sum(1 for r in history if r.status == "keep"),
            "revert": sum(1 for r in history if r.status == "revert"),
            "break": sum(1 for r in history if r.status == "break"),
            "results_tsv": str(tsv_path),
            "drafts_dir": str(self.draft_dir),
        }


__all__ = [
    "SelfOptimizer",
    "RoundResult",
    "check_break_signal",
]
