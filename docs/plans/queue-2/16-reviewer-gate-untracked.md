---
node_type: ticket
title: Untracked-файлы диффа мимо reviewer-гейта
service: _platform
status: draft
updated: 2026-10-03
links:
  part_of: [README.md]
---

# 16: Untracked-файлы диффа мимо reviewer-гейта

**What to build:** гейт шага 6 (`reviewer.workflow.ts`) обязан ревьюить весь
дифф тикета, включая новые (untracked) файлы. Сейчас карта файлов строится на
`git.changedFiles(base)` — tracked history only, и первый ран гейта тикета 09
отревьюил 2 из 4 файлов; спасли ручной `git add -A` и перезапуск. Дополнить
карту файлов из `git.status().untracked` (или эквивалентно — сделать стейджинг
диффа обязательным шагом перед гейтом в SKILL.md ship-а).

**Blocked by:** None (can start immediately).

- [ ] reviewer-ран на диффе с новым (незакоммиченным) файлом ревьюит его наравне
      с изменёнными — проверено живым прогоном с новым файлом
- [ ] SKILL.md ship-а или сам workflow не позволяют прогону с частичным
      покрытием (вывод называет файлы, попавшие в ревью)
- [ ] `gitmark lint` + `pytest` зелёные
