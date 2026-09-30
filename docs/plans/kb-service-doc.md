---
node_type: plan
title: Задокументировать сервис kb-search в KB плагина
service: _platform
status: draft
updated: 2026-09-30
tags: [plan, kb, services, dogfood]
links:
  relates_to: [../reference/commands.md, ../ontology.md]
  documents: [../../skills/kb-search/gitmark.py]
---

# Контракт: сервис-документация kb-search

## Goal

У движка `gitmark.py` — сердца плагина — нет сервис-страницы в собственной KB:
поиск по «что умеет движок» отвечает только реестром и AGENTS.md. Нужна сервис-дока
по онтологии, чтобы KB сама соблюдала дисциплину, которую требует от потребителей.

## Done

- `docs/services/kb-search/README.md` (`node_type: service`) существует: что это,
  команды движка (index/search/map/serve/stat/lint/inventory/version), где живёт,
  как вызывать из скилла; ссылки `documents` на движок и `depends_on` на онтологию.
- `docs/services/README.md` — индекс папки со строкой на сервис.
- `gitmark search "gitmark cli"` находит новую доку; `gitmark lint` зелёный.

## Scope

- `docs/services/kb-search/README.md` (новое), `docs/services/README.md` (новое) —
  только KB нового репо, payload не трогается.

## Constraints

- `no-deploy` — контура деплоя нет; шаг prod-проверок = поиск+линт из Done.
- Запуск руками оператора; один файл-план = один срез.
