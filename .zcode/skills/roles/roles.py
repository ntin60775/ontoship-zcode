#!/usr/bin/env python3
"""OntoShip roles — resolve and assign subagent model roles across three layers.

Layers (most specific wins, merged per role name):
    plugin default   <plugin>/defaults/roles.md       (next to this script: ../../)
    user global      ~/.zcode/ontoship/roles.md       (override: $ONTOSHIP_HOME)
    project          <root>/.zcode/ontoship/roles.md

File format — frontmatter with a `roles:` block, two levels deep:

    ---
    roles:
      reviewer:
        model: account:provider/model-id
        level: max            # optional; a reasoning level of that model
    ---

A broken layer file is an error, never silently skipped (fail-closed): the effective
configuration would be untrustworthy. Pure python stdlib.

Commands:
    roles.py resolve [--root DIR] [--json]     effective roles + provenance per layer
    roles.py set <role> <model>[$level] [--project] [--root DIR]
    roles.py unset <role> [--user] [--root DIR]
    roles.py version
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

VERSION = "0.1.0"

DEFAULTS_REL = ("defaults", "roles.md")
USER_REL = (".zcode", "ontoship", "roles.md")
PROJECT_REL = (".zcode", "ontoship", "roles.md")
ROLE_RE = re.compile(r"^[a-z][a-z0-9-]*$")
MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*\$?[\w-]*$")
ALLOWED_KEYS = {"model", "level"}
LEVEL_RE = re.compile(r"^[a-z][a-z0-9-]*$")


class RolesError(Exception):
    pass


def _frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise RolesError("нет frontmatter (файл должен начинаться с '---')")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise RolesError("frontmatter не закрыт (нет второй '---')")
    return "\n".join(lines[1:end])


def parse_roles(text: str, source: str) -> dict:
    """Parse the `roles:` block → {name: {model, level?}}. Strict: a typo must not
    silently disable a role."""
    fm = _frontmatter(text)
    roles, current, in_roles = {}, None, False
    for lineno, raw in enumerate(fm.splitlines(), start=2):
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key = raw.strip()
        if indent == 0:
            if key == "roles:":
                in_roles = True
                continue
            in_roles = False
            continue
        if not in_roles:
            continue
        if indent == 2 and key.endswith(":"):
            name = key[:-1]
            if not ROLE_RE.match(name):
                raise RolesError(f"{source}:{lineno}: имя роли '{name}' не подходит под {ROLE_RE.pattern}")
            current = roles.setdefault(name, {})
            continue
        if indent >= 4 and ":" in key and current is not None:
            k, _, v = key.partition(":")
            k, v = k.strip(), v.strip()
            if k not in ALLOWED_KEYS:
                raise RolesError(f"{source}:{lineno}: недопустимый ключ '{k}' (разрешены {sorted(ALLOWED_KEYS)})")
            if not v:
                raise RolesError(f"{source}:{lineno}: пустое значение '{k}'")
            current[k] = v
            continue
        raise RolesError(f"{source}:{lineno}: не понял строку '{raw}' (ожидается '  role:' или '    key: value')")
    for name, cfg in roles.items():
        if "model" not in cfg:
            raise RolesError(f"{source}: роль '{name}' без 'model'")
    return roles


def load_layer(path: Path, label: str) -> dict:
    """→ {name: {model, level?, _source, _file}}. Missing file → {} (not an error);
    broken file → RolesError (fail-closed)."""
    if not path.exists():
        return {}
    roles = parse_roles(path.read_text("utf-8"), str(path))
    for cfg in roles.values():
        cfg["_source"] = label
        cfg["_file"] = str(path)
    return roles


def default_layer_path() -> Path:
    return Path(__file__).resolve().parents[2].joinpath(*DEFAULTS_REL)


def user_layer_path() -> Path:
    home = os.environ.get("ONTOSHIP_HOME") or str(Path.home())
    return Path(home).joinpath(*USER_REL)


def project_layer_path(root: Path) -> Path:
    return root.joinpath(*PROJECT_REL)


def resolve(root: Path, default_path: Path | None = None,
            user_path: Path | None = None, project_path: Path | None = None) -> dict:
    """Merge plugin → user → project, per role name. → {name: {model, level?, _source, _file}}."""
    merged: dict = {}
    layers = [
        (default_path or default_layer_path(), "plugin-default"),
        (user_path or user_layer_path(), "user"),
        (project_path or project_layer_path(root), "project"),
    ]
    for path, label in layers:
        for name, cfg in load_layer(path, label).items():
            merged[name] = cfg
    return merged


def _split_model(arg: str) -> tuple:
    model, sep, level = arg.rpartition("$")
    if not sep:
        if "$" in arg:
            raise RolesError(f"битая пара модель$уровень: '{arg}'")
        return arg, None
    if not model or not level:
        raise RolesError(f"битая пара модель$уровень: '{arg}'")
    if not LEVEL_RE.match(level):
        raise RolesError(f"уровень '{level}' не подходит под {LEVEL_RE.pattern}")
    return model, level


def _render(roles: dict) -> str:
    out = ["---", "roles:"]
    for name in sorted(roles):
        cfg = roles[name]
        out.append(f"  {name}:")
        out.append(f"    model: {cfg['model']}")
        if cfg.get("level"):
            out.append(f"    level: {cfg['level']}")
    out += ["---", ""]
    return "\n".join(out)


def _write_layer(path: Path, role: str, model: str, level: str | None):
    if path.exists():
        roles = parse_roles(path.read_text("utf-8"), str(path))  # broken → no write
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        roles = {}
    roles[role] = {"model": model}
    if level:
        roles[role]["level"] = level
    path.write_text(_render(roles), "utf-8")


def cmd_set(role: str, model_arg: str, project: bool, root: Path) -> str:
    if not ROLE_RE.match(role):
        raise RolesError(f"имя роли '{role}' не подходит под {ROLE_RE.pattern}")
    if not MODEL_RE.match(model_arg):
        raise RolesError(f"не похоже на модель[$уровень]: '{model_arg}'")
    model, level = _split_model(model_arg)
    path = project_layer_path(root) if project else user_layer_path()
    _write_layer(path, role, model, level)
    layer = "project" if project else "user"
    return f"{role} → {model}{('$' + level) if level else ''} записано в {layer}-слой ({path})"


def cmd_unset(role: str, user_layer: bool, root: Path) -> str:
    path = user_layer_path() if user_layer else project_layer_path(root)
    label = "user" if user_layer else "project"
    if not path.exists():
        return f"{label}-слой ({path}) не существует — снимать нечего"
    roles = parse_roles(path.read_text("utf-8"), str(path))
    if role not in roles:
        return f"роли '{role}' в {label}-слое нет — снимать нечего"
    del roles[role]
    path.write_text(_render(roles), "utf-8")
    return f"роль '{role}' снята с {label}-слоя — значение возьмётся из более общего слоя"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="roles.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    rs = sub.add_parser("resolve", help="эффективные роли + провенанс")
    rs.add_argument("--root", default=".", help="корень проекта")
    rs.add_argument("--json", action="store_true")
    st = sub.add_parser("set", help="записать роль (по умолчанию — user-слой)")
    st.add_argument("role")
    st.add_argument("model", help="model[$level], точная строка из ListModels")
    st.add_argument("--project", action="store_true", help="записать в проектный слой")
    st.add_argument("--root", default=".")
    us = sub.add_parser("unset", help="снять роль со слоя (по умолчанию — project)")
    us.add_argument("role")
    us.add_argument("--user", action="store_true", help="снять с user-слоя вместо проектного")
    us.add_argument("--root", default=".")
    sub.add_parser("version", help="версия")
    a = ap.parse_args(argv)

    try:
        if a.cmd == "version":
            print(f"roles {VERSION}")
        elif a.cmd == "resolve":
            roles = resolve(Path(a.root))
            if a.json:
                print(json.dumps(roles, ensure_ascii=False, indent=2))
            else:
                if not roles:
                    print("ролей нет (defaults/roles.md рядом со скиллом пуст?)")
                for name in sorted(roles):
                    cfg = roles[name]
                    lvl = f"${cfg['level']}" if cfg.get("level") else ""
                    print(f"{name}: {cfg['model']}{lvl}  ← {cfg['_source']} ({cfg['_file']})")
        elif a.cmd == "set":
            print(cmd_set(a.role, a.model, a.project, Path(a.root)))
        elif a.cmd == "unset":
            print(cmd_unset(a.role, a.user, Path(a.root)))
    except RolesError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
