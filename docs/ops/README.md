---
node_type: index
title: Ops
service: _platform
status: active
updated: 2026-10-04
links:
  part_of: [../README.md]
---

# Ops

Operational procedures for the plugin itself.

- [install.md](install.md) — установка/обновление плагина раннером маркетплейса,
  релизный цикл, политика `.zcode/`.
- [deploy-check.md](deploy-check.md) — проверка вендоренной раскладки одной
  командой (запуск из проекта-потребителя; зелёный/FAIL/WARN).
- [session-start-hook.md](session-start-hook.md) — хук свежести индекса:
  регистрация в `.zcode/config.json` (данные проекта), поведение, проверка.
- [hygiene.md](hygiene.md) — ночная гигиена KB: lint+index+map по расписанию,
  лог ночных ERR, потребление SessionStart-хуком.
