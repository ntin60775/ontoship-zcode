"""Redact-матрица queue-2/15: node-набор кейсов прогоняется по всем копиям
redact в workflow-файлах (ship reviewer/confirm, code-review, architecture).
Сам набор — tests/redact_matrix.mjs; мост в pytest-сюиту проверяет не только
exit-код, но и нижний порог числа кейсов (урок гейта 15: набор, молча
усохший до пустого, зелёен и бесполезен)."""
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MIN_CASES = 40


def test_redact_matrix_all_copies():
    r = subprocess.run(
        ["node", str(REPO / "tests" / "redact_matrix.mjs")],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, f"redact-матрица упала:\n{r.stdout}\n{r.stderr}"
    m = re.search(r"кейсов: (\d+), упало: 0", r.stdout)
    assert m, f"неожиданный вывод матрицы: {r.stdout!r}"
    assert int(m.group(1)) >= MIN_CASES, (
        f"набор кейсов усох: {m.group(1)} < {MIN_CASES} — матрица перестала покрывать форматы"
    )
