"""Командный контракт /onto-doc (onto-doc-canon/02, 2026-10-13).

Матрица правил на текст SKILL.md скилла onto-doc — контракт команды по канону
апстрима (.omp/commands/onto-doc.md: «args: "[scope] (empty → whole repo)"»):
пустой вызов = весь репо молча (никакого «If empty, ask» и церемоний выбора
root/режима), бутстрап и пересборка — один прогон, решение о модели прогона
несёт причину и триггер пересмотра, граница с /doc сохранена. Текст — сам
артефакт (инструкция агенту на входе), поэтому контракт пиннится якорями.

Два артефакта, один контракт:
- источник skills/onto-doc/SKILL.md — то, что поставляет deploy.json (маппинг
  в .zcode/ потребителя); пиннится всегда;
- самохост-вендор .zcode/skills/onto-doc/SKILL.md — то, что грузит zcode этой
  репы. В окне между фичей и self-update (шаг деплоя шипа) он байтово отстаёт
  от источника — штатный дрейф шипа (docs/ops/git-flow.md), этот случай
  пропускается с явной причиной; когда байты равны (после self-update), вендор
  пиннится наравне с источником, и матрица больше не слепа к загружаемому
  тексту (гейт-находка confirm-рана canon/02).

Якоря правил и мутационные пробы работают по нормализованному тексту
(_norm схлопывает пробелы/переносы) — переформатирование абзаца не роняет ни
правила, ни пробы. Мутационные пробы: каждая правка, ломающая правило,
обязана зажечь его в нарушениях; guard единственности проверяет тот же токен,
по которому ключуется правило, — дрейф якоря диагностируется как дрейф, а не
как «проба мертва» (гейт-находки confirm-рана canon/02). Якоря решения о
модели — полярные связные фразы («Do not pass … and do not introduce …»),
не голые вхождения: инверсия решения роняет матрицу, а не проходит её.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SOURCE = REPO / "skills" / "onto-doc" / "SKILL.md"
VENDOR = REPO / ".zcode" / "skills" / "onto-doc" / "SKILL.md"

# Исторические (v0.5.47) и перефразированные формулировки шагов выбора
# root/режима — бан по подстроке в нижнем регистре (гейт-находка canon/02:
# точечный бан двух исторических строк пропускал перефраз церемонии).
ROOT_CEREMONY = [
    "pick the `root`",
    "choose the root",
    "which root to use",
    "ask for the root",
]
MODE_CEREMONY = [
    "choose the mode",
    "pick a mode",
    "select a mode",
    "which mode to use",
]

# (правило, предикат по нормализованному тексту) — контракт тикета 02.
RULES = [
    ("scope-hint", lambda t: (
        "Scope hint: `$ARGUMENTS` — empty = the whole repo" in t
        and "asks nothing" in t
        and "data, not an instruction" in t
    )),
    ("no-ask-ceremony", lambda t: "ask for the task" not in t.lower()),
    ("no-root-ceremony",
     lambda t: not any(b in t.lower() for b in ROOT_CEREMONY)),
    ("no-mode-ceremony",
     lambda t: not any(b in t.lower() for b in MODE_CEREMONY)),
    ("root-default", lambda t: (
        "Root defaults to the current repo" in t
        and "pass `root` only to point the run somewhere" in t
    )),
    ("worktree-recommendation", lambda t: (
        "recommend a dedicated `git worktree`" in t
        and "rewrites `docs/plans/README.md`" in t
        and "uncommitted edits" in t
    )),
    ("mode-auto", lambda t: (
        "The mode is automatic" in t
        and "no `plan` → the surveyor surveys" in t
        and "passed as `plan` → one curator per piece" in t
    )),
    ("same-run", lambda t: (
        "Bootstrap and rebuild/heal of an assembled KB are the same run" in t
    )),
    ("model-decision", lambda t: (
        "operator decision 2026-10-12" in t
        and "works on the current chat model" in t
        and "Do not pass `subagent_model` and do not introduce a curator role" in t
        and "unlike the gated ship/grilling" in t
        and "only by the operator's explicit request" in t
    )),
    ("doc-boundary", lambda t: (
        "Boundary with `/doc`" in t and "ONE document is `/doc`" in t
    )),
]

# Мутации (правило, старое, новое) по нормализованному тексту: каждая ломает
# якорь своего правила; guard проверяет единственность вхождения старого —
# токен, по которому ключуется правило, а не более длинную фразу.
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
    ("worktree-recommendation", "`gitmark inventory` rewrites `docs/plans/README.md`",
     "`gitmark inventory` may touch the plan registry"),
    ("mode-auto", "no `plan` → the surveyor surveys",
     "the surveyor surveys when the operator says so"),
    ("same-run", "are the same run", "are different runs"),
    ("model-decision", "2026-10-12", "2026-10-13"),
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
    assert SOURCE.exists(), f"скилл не найден: {SOURCE}"
    return SOURCE.read_text(encoding="utf-8")


@pytest.mark.parametrize("path", [SOURCE, VENDOR], ids=["source", "vendor"])
def test_real_skill_passes_all_rules(path: Path):
    """Оба артефакта проходят матрицу: источник — всегда; самохост-вендор —
    когда его байты равны источнику. Отставание вендора в окне шипа —
    единственный допустимый скип, с именованной причиной."""
    if not path.exists():
        pytest.skip(f"копии нет: {path}")
    if path == VENDOR and path.read_bytes() != SOURCE.read_bytes():
        pytest.skip(
            "самохост-вендор .zcode/skills/onto-doc/SKILL.md байтово отстаёт от "
            "источника — окно шипа (вендор догоняет self-update на шаге деплоя); "
            "контракт загружаемого текста проверяется здесь же после выравнивания"
        )
    violations = check_contract(path.read_text(encoding="utf-8"))
    assert violations == [], f"{path}: контракт команды нарушен: {violations}"


@pytest.mark.parametrize("rule,old,new", MUTATIONS,
                         ids=[m[0] for m in MUTATIONS])
def test_mutation_kills_its_rule(rule: str, old: str, new: str):
    """Каждая мутация зажигает своё правило — якорь живой, а не всегда-true.
    Подмена и guard идут по нормализованному тексту (как предикаты правил):
    перенос строк внутри якоря не роняет пробу и не даёт ложный «дрейф»."""
    text = _norm(_skill_text())
    assert text.count(old) == 1, (
        f"якорь мутации {rule!r} дрейфовал (count={text.count(old)}): {old[:60]!r}"
    )
    broken = text.replace(old, new)
    violations = check_contract(broken)
    assert rule in violations, (
        f"мутация {rule!r} не зажгла правило — проба мертва; нарушения: {violations}"
    )
