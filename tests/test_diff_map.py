"""Мост к node-кейсам карты диффа (queue-2/16): парсеры numstat/untracked
из skills/ship/reviewer.workflow.ts прогоняются tests/diff_map.mjs. Как и в
redact-мосте (queue-2/15), проверяется не только exit-код, но и нижний порог
числа кейсов — усохший набор зелёен и бесполезен."""
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MIN_CASES = 18


def test_diff_map_parsers():
    r = subprocess.run(
        ["node", str(REPO / "tests" / "diff_map.mjs")],
        capture_output=True,
        encoding="utf-8",  # кириллический вывод матрицы: не доверяем локали (гейт 16)
        timeout=60,
    )
    assert r.returncode == 0, f"diff_map упала:\n{r.stdout}\n{r.stderr}"
    m = re.search(r"кейсов: (\d+), упало: 0", r.stdout)
    assert m, f"неожиданный вывод diff_map: {r.stdout!r}"
    assert int(m.group(1)) >= MIN_CASES, (
        f"набор кейсов усох: {m.group(1)} < {MIN_CASES} — парсеры перестали покрывать форматы"
    )
