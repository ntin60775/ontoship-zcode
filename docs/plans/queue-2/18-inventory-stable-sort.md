---
node_type: ticket
title: Стабильная сортировка inventory
service: _platform
status: draft
updated: 2026-10-03
links:
  part_of: [README.md]
---

# 18: Стабильная сортировка inventory

**What to build:** `gitmark inventory` строит таблицу навыков из payload-каталога,
который резолвится относительно движка: dev-экземпляр (`skills/kb-search/`) видит
`skills/` и дописывает новые навыки в конец таблицы, вендорный (`.zcode/skills/`)
— видит `.zcode/skills/` и сортирует алфавитно. Контент один, порядок разный →
I7 «рассинхрон» на каждом self-update нового скилла (воспроизведено в 08 и 09).
Единая детерминированная сортировка строк реестра (по имени навыка) в `gitmark.py`,
чтобы обе инкарнации давали побайтно одинаковую таблицу.

**Blocked by:** None (can start immediately).

- [ ] генерация из `skills/` и из `.zcode/` даёт побайтно одинаковый
      `docs/reference/commands.md`
- [ ] тест в `tests/test_gitmark.py`: таблица отсортирована по имени навыка
      независимо от порядка обхода каталога
- [ ] `pytest` + `gitmark lint --strict` зелёные
