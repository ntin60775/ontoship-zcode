"""Матрица вердикта конфирмера (crossreview-adoption/02): node-набор кейсов
прогоняется по функции verdict, извлечённой из живого confirm.workflow.ts
(verified/unconfirmed/unverified — отказ проверки не равен опровержению).
Мост в pytest-сюиту проверяет exit-код и нижний порог числа кейсов (урок
гейта 15: набор, молча усохший до пустого, зелёен и бесполезен)."""
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MIN_CASES = 8


def test_verdict_matrix():
    r = subprocess.run(
        ["node", str(REPO / "tests" / "verdict_matrix.mjs")],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, f"verdict-матрица упала:\n{r.stdout}\n{r.stderr}"
    m = re.search(r"кейсов: (\d+), упало: 0", r.stdout)
    assert m, f"неожиданный вывод матрицы: {r.stdout!r}"
    assert int(m.group(1)) >= MIN_CASES, (
        f"набор кейсов усох: {m.group(1)} < {MIN_CASES} — матрица перестала покрывать отображение"
    )
