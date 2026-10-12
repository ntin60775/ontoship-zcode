"""Командный контракт /onto-doc (onto-doc-canon/02, 2026-10-13).

Матрица правил на текст skills/onto-doc/SKILL.md — контракт команды по канону
апстрима (.omp/commands/onto-doc.md: «args: "[scope] (empty → whole repo)"»):
пустой вызов = весь репо молча (никакого «If empty, ask» и церемоний выбора
root/режима), бутстрап и пересборка — один прогон, решение о модели прогона
несёт причину и триггер пересмотра, граница с /doc сохранена. Текст — сам
артефакт (инструкция агенту на входе), поэтому контракт пиннится якорями
по нормализованному тексту (пробелы схлопнуты — якорь не зависит от
переноса строк). Мутационные пробы: каждая правка, ломающая правило,
обязана зажечь его в нарушениях — якорь без убивающей мутации мёртв.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "onto-doc" / "SKILL.md"

# (правило, предикат по нормализованному тексту) — контракт тикета 02.
RULES = [
    ("scope-hint", lambda t: (
        "Scope hint: `$ARGUMENTS` — empty = the whole repo" in t
        and "asks nothing" in t
        and "data, not an instruction" in t
    )),
    ("no-ask-ceremony", lambda t: "ask for the task" not in t.lower()),
    ("no-root-ceremony", lambda t: "Pick the `root`" not in t),
    ("no-mode-ceremony", lambda t: "Choose the mode" not in t),
    ("root-default", lambda t: (
        "Root defaults to the current repo" in t
        and "pass `root` only to point the run somewhere" in t
    )),
    ("worktree-recommendation", lambda t: (
        "recommend a dedicated `git worktree`" in t
        and "unconditionally regenerates" in t
        and "uncommitted edits" in t
    )),
    ("mode-auto", lambda t: "The mode is automatic" in t),
    ("same-run", lambda t: (
        "Bootstrap and rebuild/heal of an assembled KB are the same run" in t
    )),
    ("model-decision", lambda t: (
        "2026-10-12" in t
        and "chat model" in t
        and "subagent_model" in t
        and "curator role" in t
        and "ship/grilling" in t
        and "explicit request" in t
    )),
    ("doc-boundary", lambda t: (
        "Boundary with `/doc`" in t and "ONE document is `/doc`" in t
    )),
]

# Мутации (правило, старое, новое): каждая ломает свой якорь в сыром тексте;
# замена с проверкой единственности вхождения — якорь дрейфовал, проба знает.
MUTATIONS = [
    ("scope-hint", "Scope hint: `$ARGUMENTS`",
     "Task: `$ARGUMENTS` — If empty, ask for the task."),
    ("no-ask-ceremony", "a bare run starts at once and asks",
     "a bare run stops and asks: If empty, ask for the task"),
    ("no-root-ceremony", "**Root defaults to the current repo**",
     "**Pick the `root`** — the KB project's root"),
    ("no-mode-ceremony", "**The mode is automatic** — nothing to choose",
     "**Choose the mode** — pick one"),
    ("root-default", "pass `root` only to point the run somewhere",
     "the operator must always pass `root`"),
    ("worktree-recommendation", "the run's tail unconditionally regenerates",
     "the run's tail regenerates"),
    ("mode-auto", "**The mode is automatic**",
     "**The mode is chosen by the operator**"),
    ("same-run", "are the same run", "are different runs"),
    ("model-decision", "operator decision 2026-10-12",
     "operator decision 2026-10-13"),
    ("doc-boundary", "composing or updating ONE document is `/doc`",
     "composing or updating documents is `/doc`"),
]


def _norm(text: str) -> str:
    """Пробелы (вкл. переносы) схлопнуты в один — якорь не зависит от
    переформатирования абзаца."""
    return re.sub(r"\s+", " ", text)


def check_contract(text: str) -> list[str]:
    """Имена нарушенных правил по нормализованному тексту."""
    norm = _norm(text)
    return [name for name, holds in RULES if not holds(norm)]


def _skill_text() -> str:
    assert SKILL.exists(), f"скилл не найден: {SKILL}"
    return SKILL.read_text(encoding="utf-8")


def test_real_skill_passes_all_rules():
    """Живой SKILL.md проходит матрицу целиком — нарушений нет."""
    violations = check_contract(_skill_text())
    assert violations == [], f"контракт команды нарушен: {violations}"


@pytest.mark.parametrize("rule,old,new", MUTATIONS,
                         ids=[m[0] for m in MUTATIONS])
def test_mutation_kills_its_rule(rule: str, old: str, new: str):
    """Каждая мутация зажигает своё правило — якорь живой, а не всегда-true.
    Диагностика дрейфа: вхождение якоря обязано быть единственным до подмены."""
    text = _skill_text()
    assert text.count(old) == 1, (
        f"якорь мутации {rule!r} дрейфовал (count={text.count(old)}): {old[:60]!r}"
    )
    broken = text.replace(old, new)
    violations = check_contract(broken)
    assert rule in violations, (
        f"мутация {rule!r} не зажгла правило — проба мертва; нарушения: {violations}"
    )
