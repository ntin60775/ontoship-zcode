---
node_type: index
title: Ops
service: _platform
status: active
updated: 2026-09-30
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
