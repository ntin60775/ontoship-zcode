"""Командный контракт /onto-doc (onto-doc-canon/02; модель переписана
roles-per-agent/02, 2026-10-13; гейт-фиксы dwfrun-92e63bc9).

Матрица правил на текст SKILL.md скилла onto-doc — контракт команды по канону
апстрима (.omp/commands/onto-doc.md: «args: "[scope] (empty → whole repo)"»):
пустой вызов = весь репо молча (никакого «If empty, ask» и церемоний выбора
root/режима), бутстрап и пересборка — один прогон, граница с /doc сохранена.
Модель прогона — роли (решение оператора 2026-10-13, пересматривает
2026-10-12 его же триггером): surveyor → роль `surveyor`, кураторы fan-out и
healer → роль `curator`, никогда модель чата, фолбэка нет; вход в ран —
только свежая инстанциация шаблона. Префлайт резолвит ВСЕ плейсхолдеры
шаблона независимо от режима (гейт-находка: плейсхолдер surveyor в файле
безусловен, if (bootstrap) сторожит лишь исполнение — «резолвить только
curator в plan-режиме» делало ран незапускаемым). Прежний пин «pass no
`subagent_model`» снят осознанно — субагенты больше не на модели чата/рана.
Текст — сам артефакт (инструкция агенту на входе), поэтому контракт пиннится
якорями.

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
обязана зажечь в нарушениях РОВНО своё правило — чужое правило в нарушениях
значит неадресную пробу (гейт-находка confirm-рана roles-per-agent/02:
мисадресованный якорь с изготовляющим текстом проходил молча); guard
единственности проверяет тот же токен, по которому ключуется правило, — дрейф
якоря диагностируется как дрейф, а не как «проба мертва» (гейт-находки
confirm-рана canon/02). Якоря решения о модели — полярные связные фразы
(«never rides the chat model», «runs on the `surveyor` role») ПЛЮС бан-лист
модели: подменная инверсия роняет presence-якорь, «инверсия добавлением»
(текст, снова разрешающий модель чата рядом с нетронутыми якорями) —
бан-лист (гейт-находка: 9 presence-якорей её пропускали). Уровни ролей
($max/$high) здесь — факты о дефолтах со ссылкой на их дом (tests/
/test_roles.py пиннит записи defaults); контракт скилла — назначение ролей и
дисциплина запуска, не дубликат реестра.
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
# Бан-лист модели (гейт-находка confirm-рана roles-per-agent/02): текст,
# снова разрешающий модель чата/subagent_model, роняет model-decision даже
# при нетронутых presence-якорях — «инверсия добавлением» ловится баном,
# подменная инверсия — якорями.
MODEL_BAN = [
    "pass `subagent_model`",
    "works on the current chat model",
    "runs on the current chat model",
    "rides the chat model when",
]

# (правило, предикат по нормализованному тексту) — контракт canon/02 + тикета
# roles-per-agent/02 (модель на ролях, вход — свежая инстанциация).
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
        "operator decision 2026-10-13" in t
        and "revising the 2026-10-12 chat-model decision" in t
        and "runs on the `surveyor` role" in t
        and "the fan-out curators and the healer on the `curator` role" in t
        and "surveyor GLM-5.3-Flash$max" in t
        and "curator GLM-5.3-Flash$high" in t
        and "never rides the chat model" in t
        and "no fallback" in t
        and "/roles set curator|surveyor" in t
        and not any(b in t.lower() for b in MODEL_BAN)
    )),
    ("role-preflight", lambda t: (
        "Launch through a fresh instantiation" in t
        and "every role whose placeholder the template carries" in t
        and "the template holds the surveyor placeholder unconditionally" in t
        and "resolve --json" in t
        and "missing from the output is the same stop as a mismatch" in t
        and "ListModels" in t
        and "Everything resolves before anything is instantiated" in t
    )),
    ("fresh-instantiation", lambda t: (
        "uniquely named" in t
        and ".zcode/workflow-drafts/" in t
        and "never reuse an old one" in t
        and "≥ 1 placeholder in the template" in t
        and "0 placeholders left in the instance" in t
        and "byte-equal to the resolve output" in t
        and "a quote, a newline or any other character is a stop" in t
        and "CreateWorkflow(path=<the instance>" in t
        and "the raw template is never launchable" in t
    )),
    ("doc-boundary", lambda t: (
        "Boundary with `/doc`" in t and "ONE document is `/doc`" in t
    )),
]

# Мутации (правило, старое, новое) по нормализованному тексту: каждая ломает
# якорь своего правила; guard проверяет единственность вхождения старого —
# токен, по которому ключуется правило, а не более длинную фразу.
MUTATIONS = [
    # Пробы адресны: каждая зажигает РОВНО своё правило (assert == [rule] ниже);
    # тексты new выбраны нейтральными к чужим якорям — «ask for the task»
    # вводится без разрушения «asks nothing», бан root/режима — без разрушения
    # якорей root-default/mode-auto (гейт-находка dwfrun-92e63bc9).
    ("scope-hint", "Scope hint: `$ARGUMENTS`",
     "Task hint: `$ARGUMENTS`"),
    ("no-ask-ceremony", "a bare run starts at once",
     "a bare run stops to ask for the task; nothing else"),
    ("no-root-ceremony", "For a live repo recommend a dedicated",
     "For a live repo, pick the `root` first, then recommend a dedicated"),
    ("no-mode-ceremony", "nothing to choose",
     "choose the mode manually"),
    ("root-default", "pass `root` only to point the run somewhere",
     "the operator must always pass `root`"),
    ("worktree-recommendation", "`gitmark inventory` rewrites `docs/plans/README.md`",
     "`gitmark inventory` may touch the plan registry"),
    ("mode-auto", "no `plan` → the surveyor surveys",
     "the surveyor surveys when the operator says so"),
    ("same-run", "are the same run", "are different runs"),
    ("model-decision", "The surveyor runs on the `surveyor` role",
     "The surveyor runs on the current chat model"),
    ("role-preflight", "every role whose placeholder the template carries",
     "whatever roles seem needed at the time"),
    ("fresh-instantiation", "never reuse an old one", "reuse is fine"),
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
    """Каждая мутация зажигает ровно своё правило — якорь живой, а не
    всегда-true, и проба адресна: чужое правило в нарушениях означает, что
    били якорь чужого правила (гейт-находка dwfrun-92e63bc9: мисадресованный
    old с изготовляющим new проходил молча при членстве вместо равенства).
    Подмена и guard идут по нормализованному тексту (как предикаты правил):
    перенос строк внутри якоря не роняет пробу и не даёт ложный «дрейф»."""
    text = _norm(_skill_text())
    assert text.count(old) == 1, (
        f"якорь мутации {rule!r} дрейфовал (count={text.count(old)}): {old[:60]!r}"
    )
    broken = text.replace(old, new)
    violations = check_contract(broken)
    assert violations == [rule], (
        f"мутация {rule!r} не зажгла ровно своё правило — проба мертва или "
        f"неадресна; нарушения: {violations}"
    )


def test_model_inversion_by_addition_is_banned():
    """Гейт-находка (confirm dwfrun-92e63bc9): «инверсия добавлением» — текст,
    снова разрешающий модель чата рядом с нетронутыми presence-якорями, —
    обязана ронять матрицу, как и подменная инверсия из MUTATIONS; здесь
    якоря правила остаются целы, срабатывает только бан-лист модели."""
    text = _norm(_skill_text())
    anchor = "Steer the cost with `/roles set"
    assert text.count(anchor) == 1
    added = text.replace(
        anchor,
        "Or for a cheap run pass `subagent_model` (the current chat model). "
        + anchor)
    violations = check_contract(added)
    assert violations == ["model-decision"], (
        f"бан-лист модели не зажёгся на инверсии добавлением: {violations}")
