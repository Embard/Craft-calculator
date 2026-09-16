#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает каталог сайта из файлов админа.

Положите миссию, profiles и моды в ../incoming и запустите этот скрипт.
Он пишет js/generated.js — страницы сайта читают его сразу.
"""

from __future__ import annotations

import json
import re
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCOMING = ROOT / "incoming"
MISSION = INCOMING / "mission"
PROFILES = INCOMING / "profiles"
WORKSHOP = INCOMING / "workshop"
ICONS_IN = INCOMING / "icons"
OVERRIDES = INCOMING / "overrides"
DATA = ROOT / "data"
IMG_ITEMS = ROOT / "img" / "items"
GENERATED_JS = ROOT / "js" / "generated.js"

CATEGORY_LABELS = {
    "weapons": "Оружие",
    "explosives": "Взрывчатка",
    "clothes": "Одежда",
    "containers": "Контейнеры",
    "food": "Еда",
    "tools": "Инструменты",
    "craftingbase": "Крафт",
    "books": "Книги",
    "recipes": "Рецепты",
    "vehiclesparts": "Запчасти",
    "armor": "Броня",
    "material": "Материал",
    "medicine": "Медицина",
    "ammo": "Патроны",
    "magazines": "Магазины",
}

USAGE_LABELS = {
    "Military": "военные объекты",
    "Police": "полиция",
    "Medic": "больницы и медпункты",
    "Firefighter": "пожарные части",
    "Town": "города",
    "Village": "деревни",
    "Coast": "побережье",
    "Farm": "фермы",
    "Industrial": "промзоны",
    "Hunting": "охотничьи угодья",
    "School": "школы",
    "Office": "офисы",
    "Prison": "тюрьмы",
    "Lunapark": "аттракционы",
    "Historical": "исторические места",
}

VALUE_LABELS = {
    "Tier1": "тир 1, побережье",
    "Tier2": "тир 2",
    "Tier3": "тир 3",
    "Tier4": "тир 4, глубокая карта",
    "Unique": "уникальный",
}


def rel_or_name(path: Path) -> str:
    try:
        return str(path.relative_to(INCOMING)).replace("\\", "/")
    except ValueError:
        return path.name


def iter_files(folder: Path, patterns: tuple[str, ...]):
    if not folder.exists():
        return
    for pattern in patterns:
        yield from folder.rglob(pattern)


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        print(f"skip broken json {path}: {exc}")
        return default


def xml_text(node: ET.Element, tag: str) -> str | None:
    child = node.find(tag)
    return child.text.strip() if child is not None and child.text else None


def parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def humanize_classname(name: str) -> str:
    clean = re.sub(r"[_\-]+", " ", name)
    clean = re.sub(r"([a-z])([A-Z])", r"\1 \2", clean)
    clean = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", clean)
    return re.sub(r"\s+", " ", clean).strip()


def category_label(raw: str | None) -> str:
    if not raw:
        return "Прочее"
    return CATEGORY_LABELS.get(raw.lower(), raw)


def rarity_from(nominal: int | None, crafted: bool) -> str:
    if crafted:
        return "крафт"
    if nominal is None:
        return "—"
    if nominal <= 0:
        return "не в луте"
    if nominal <= 4:
        return "очень редкий"
    if nominal <= 15:
        return "редкий"
    if nominal <= 40:
        return "обычный"
    return "частый"


def where_from_types(item: dict) -> str:
    if item.get("crafted"):
        return "Не лутается в готовом виде — только крафт или выдача."
    places = [USAGE_LABELS.get(u, u) for u in item.get("usage") or []]
    tiers = [VALUE_LABELS.get(v, v) for v in item.get("value") or []]
    parts = []
    if places:
        parts.append("Ищется: " + ", ".join(places) + ".")
    if tiers:
        parts.append("Зоны: " + ", ".join(tiers) + ".")
    nominal = item.get("nominal")
    if nominal is not None:
        parts.append(f"На карте цель экономики — около {nominal} шт.")
    if not parts:
        return "В файлах сервера нет точки спавна. Проверьте торговца, квест или крафт."
    return " ".join(parts)


def parse_types_xml(path: Path) -> list[dict]:
    items = []
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        print(f"skip broken xml {path}: {exc}")
        return items
    for node in tree.getroot().findall("type"):
        classname = node.get("name")
        if not classname:
            continue
        flags = node.find("flags")
        crafted = flags.get("crafted") == "1" if flags is not None else False
        items.append(
            {
                "classname": classname,
                "nominal": parse_int(xml_text(node, "nominal")),
                "min": parse_int(xml_text(node, "min")),
                "lifetime": parse_int(xml_text(node, "lifetime")),
                "restock": parse_int(xml_text(node, "restock")),
                "category": (node.find("category").get("name") if node.find("category") is not None else None),
                "usage": [u.get("name") for u in node.findall("usage") if u.get("name")],
                "value": [v.get("name") for v in node.findall("value") if v.get("name")],
                "crafted": crafted,
            }
        )
    return items


def parse_spawnable(path: Path) -> list[dict]:
    rows = []
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        print(f"skip broken xml {path}: {exc}")
        return rows
    for node in tree.getroot().findall("type"):
        parent = node.get("name")
        for cargo in node.findall("cargo"):
            parent_chance = cargo.get("chance")
            if cargo.get("preset"):
                rows.append(
                    {
                        "item": cargo.get("preset"),
                        "place": parent,
                        "kind": "preset",
                        "chance": parent_chance,
                    }
                )
            for entry in cargo.findall("item"):
                rows.append(
                    {
                        "item": entry.get("name"),
                        "place": parent,
                        "kind": "контейнер",
                        "chance": entry.get("chance") or parent_chance,
                    }
                )
        for att in node.findall("attachments"):
            parent_chance = att.get("chance")
            if att.get("preset"):
                rows.append(
                    {
                        "item": att.get("preset"),
                        "place": parent,
                        "kind": "preset",
                        "chance": parent_chance,
                    }
                )
            for entry in att.findall("item"):
                rows.append(
                    {
                        "item": entry.get("name"),
                        "place": parent,
                        "kind": "обвес",
                        "chance": entry.get("chance") or parent_chance,
                    }
                )
    return rows


def parse_stringtables() -> dict[str, str]:
    names: dict[str, str] = {}
    for path in iter_files(INCOMING, ("stringtable.csv",)):
        try:
            text = path.read_text(encoding="utf-8-sig", errors="ignore")
        except OSError:
            continue
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            continue
        header = [part.strip().strip('"') for part in lines[0].split(";")]
        if len(header) == 1:
            header = [part.strip().strip('"') for part in lines[0].split(",")]
            sep = ","
        else:
            sep = ";"
        lang_idx = 0
        for candidate in ("russian", "ru", "original", "english"):
            for i, col in enumerate(header):
                if col.lower() == candidate:
                    lang_idx = i
                    break
            else:
                continue
            break
        for line in lines[1:]:
            parts = [part.strip().strip('"') for part in line.split(sep)]
            if len(parts) <= lang_idx:
                continue
            key = parts[0]
            value = parts[lang_idx]
            if not key or not value:
                continue
            short = key.split("_")[-1] if "_" in key else key
            names[key] = value
            names[short] = value
    return names


def parse_traderplus(obj, trader_name: str, prices: list[dict]) -> None:
    if isinstance(obj, list):
        for entry in obj:
            parse_traderplus(entry, trader_name, prices)
        return
    if not isinstance(obj, dict):
        return

    category = (
        obj.get("CategoryName")
        or obj.get("Category")
        or obj.get("m_Name")
        or trader_name
    )

    products = obj.get("Products") or obj.get("Items") or obj.get("m_TraderPlusItems") or []
    if isinstance(products, list):
        for product in products:
            if isinstance(product, str):
                parts = [p.strip() for p in product.split(",")]
                if not parts or not parts[0]:
                    continue
                classname = parts[0]
                buy = parts[2] if len(parts) > 2 else ""
                sell = parts[3] if len(parts) > 3 else ""
                prices.append(
                    {
                        "id": classname,
                        "item": classname,
                        "trader": category,
                        "buy": buy if buy not in {"", "-1"} else "не покупает",
                        "sell": sell if sell not in {"", "-1"} else "не принимает",
                    }
                )
            elif isinstance(product, dict):
                classname = product.get("ClassName") or product.get("Classname") or product.get("Name")
                if not classname:
                    continue
                buy = product.get("BuyPrice", product.get("Buy", product.get("MaxPriceThreshold")))
                sell = product.get("SellPrice", product.get("Sell", product.get("MinPriceThreshold")))
                prices.append(
                    {
                        "id": classname,
                        "item": classname,
                        "trader": category,
                        "buy": "не покупает" if buy in (None, -1, "-1") else str(buy),
                        "sell": "не принимает" if sell in (None, -1, "-1") else str(sell),
                    }
                )

    for key in ("TraderCategories", "Categories", "MarketItems", "Items"):
        if key in obj:
            parse_traderplus(obj[key], category or trader_name, prices)


def collect_prices() -> list[dict]:
    prices: list[dict] = []
    for path in iter_files(PROFILES, ("*.json",)):
        low = path.name.lower()
        if not any(token in low for token in ("trader", "market", "price", "product")):
            continue
        data = load_json(path, None)
        if data is None:
            continue
        parse_traderplus(data, path.stem, prices)
    return prices


def collect_script_recipes() -> dict[str, list[dict]]:
    recipes: dict[str, list[dict]] = {}
    add_ing = re.compile(r'AddIngredient\([^,]+,\s*"([^"]+)"', re.I)
    add_res = re.compile(r'AddResult\(\s*"([^"]+)"', re.I)
    for path in iter_files(WORKSHOP, ("*.c",)):
        if "recipe" not in path.name.lower() and "craft" not in str(path).lower():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        results = add_res.findall(text)
        ingredients = add_ing.findall(text)
        if not results or not ingredients:
            continue
        for result in results:
            recipes.setdefault(result, [])
            for ingredient in ingredients:
                if not any(part["id"] == ingredient for part in recipes[result]):
                    recipes[result].append({"id": ingredient, "qty": 1})
    return recipes


def collect_json_recipes() -> dict[str, list[dict]]:
    recipes: dict[str, list[dict]] = {}
    for path in iter_files(INCOMING, ("*recipe*.json", "*craft*.json")):
        if "overrides" in path.parts:
            continue
        data = load_json(path, None)
        if not isinstance(data, (dict, list)):
            continue
        entries = data.values() if isinstance(data, dict) else data
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            result = entry.get("result") or entry.get("Result") or entry.get("id") or entry.get("classname")
            ingredients = entry.get("recipe") or entry.get("ingredients") or entry.get("Items") or []
            if not result or not isinstance(ingredients, list):
                continue
            parsed = []
            for ing in ingredients:
                if isinstance(ing, dict) and (ing.get("id") or ing.get("ClassName")):
                    parsed.append(
                        {
                            "id": ing.get("id") or ing.get("ClassName"),
                            "qty": int(ing.get("qty") or ing.get("Quantity") or 1),
                        }
                    )
            if parsed:
                recipes[result] = parsed
    return recipes


def find_icon(classname: str, copied: dict[str, str]) -> str:
    if classname in copied:
        return copied[classname]
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        candidate = IMG_ITEMS / f"{classname}{ext}"
        if candidate.exists():
            return f"img/items/{candidate.name}"
        lower = IMG_ITEMS / f"{classname.lower()}{ext}"
        if lower.exists():
            return f"img/items/{lower.name}"
    return ""


def copy_icons(classnames: set[str]) -> dict[str, str]:
    copied: dict[str, str] = {}
    wanted = {name.lower(): name for name in classnames}
    IMG_ITEMS.mkdir(parents=True, exist_ok=True)
    sources = []
    sources.extend(iter_files(ICONS_IN, ("*.png", "*.jpg", "*.jpeg", "*.webp")))
    sources.extend(iter_files(WORKSHOP, ("*.png", "*.jpg", "*.jpeg", "*.webp")))
    for src in sources:
        key = src.stem
        match = wanted.get(key.lower())
        if not match:
            continue
        dest = IMG_ITEMS / f"{match}{src.suffix.lower()}"
        if dest.exists():
            copied[match] = f"img/items/{dest.name}"
            continue
        try:
            shutil.copy2(src, dest)
            copied[match] = f"img/items/{dest.name}"
        except OSError as exc:
            print(f"icon copy failed {src}: {exc}")
    return copied


def folder_has_files(folder: Path) -> bool:
    if not folder.exists():
        return False
    return any(path.is_file() and path.name != ".gitkeep" for path in folder.rglob("*"))


def build_item(raw: dict, names: dict[str, str], icons: dict[str, str]) -> dict:
    classname = raw["classname"]
    crafted = bool(raw.get("crafted"))
    nominal = raw.get("nominal")
    name = names.get(classname) or humanize_classname(classname)
    return {
        "id": classname,
        "classname": classname,
        "name": name,
        "category": (raw.get("category") or "other").lower(),
        "categoryLabel": category_label(raw.get("category")),
        "image": find_icon(classname, icons),
        "craftable": crafted,
        "description": "",
        "where": where_from_types(raw),
        "tier": (raw.get("value") or ["—"])[0],
        "rarity": rarity_from(nominal, crafted),
        "usage": raw.get("usage") or [],
        "value": raw.get("value") or [],
        "nominal": nominal,
        "min": raw.get("min"),
        "loot": [],
        "recipe": [],
    }


def merge_override(item: dict, override: dict) -> dict:
    merged = dict(item)
    for key, value in override.items():
        if value not in (None, "", [], {}):
            merged[key] = value
    merged["id"] = override.get("id") or item.get("id")
    return merged


def write_generated(payload: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "catalog.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "status.json").write_text(json.dumps(payload.get("status", {}), ensure_ascii=False, indent=2), encoding="utf-8")
    js = "window.GZ_GENERATED = " + json.dumps(payload, ensure_ascii=False) + ";\n"
    GENERATED_JS.write_text(js, encoding="utf-8")
    print(f"wrote {GENERATED_JS}")


def main() -> None:
    for folder in (MISSION, PROFILES, WORKSHOP, ICONS_IN, OVERRIDES):
        folder.mkdir(parents=True, exist_ok=True)

    missing = []
    if not folder_has_files(MISSION):
        missing.append("incoming/mission — нет файлов миссии")
    if not folder_has_files(PROFILES):
        missing.append("incoming/profiles — нет цен и конфигов торговцев")
    if not folder_has_files(WORKSHOP) and not folder_has_files(ICONS_IN):
        missing.append("incoming/workshop или incoming/icons — нет картинок")

    override_items = load_json(OVERRIDES / "items.json", {})
    override_names = load_json(OVERRIDES / "names.json", {})
    override_recipes = load_json(OVERRIDES / "recipes.json", {})
    string_names = parse_stringtables()
    names = {**string_names, **override_names}

    types_items = []
    for path in iter_files(MISSION, ("*.xml",)):
        if "types" in path.name.lower() and "spawnable" not in path.name.lower():
            types_items.extend(parse_types_xml(path))

    spawn_rows = []
    for path in iter_files(MISSION, ("*spawnabletypes*.xml", "cfgrandompresets.xml")):
        spawn_rows.extend(parse_spawnable(path))

    loot_index: dict[str, list[dict]] = {}
    for row in spawn_rows:
        item = row.get("item")
        if not item:
            continue
        chance = row.get("chance")
        chance_text = f"{float(chance) * 100:.0f}%" if chance and str(chance).replace(".", "", 1).isdigit() else (chance or "")
        loot_index.setdefault(item, []).append(
            {
                "house": row.get("place") or "неизвестно",
                "category": row.get("kind") or "лут",
                "tier": "",
                "chance": chance_text,
            }
        )

    recipes = {}
    recipes.update(collect_json_recipes())
    recipes.update(collect_script_recipes())
    recipes.update(override_recipes)

    classnames = {item["classname"] for item in types_items}
    classnames.update(override_items.keys())
    for item in override_items.values():
        if isinstance(item, dict) and item.get("classname"):
            classnames.add(item["classname"])
        if isinstance(item, dict) and item.get("id"):
            classnames.add(item["id"])
    classnames.update(recipes.keys())
    for parts in recipes.values():
        for part in parts:
            if part.get("id"):
                classnames.add(part["id"])

    icons = copy_icons(classnames)
    catalog: dict[str, dict] = {}

    for raw in types_items:
        item = build_item(raw, names, icons)
        item["loot"] = loot_index.get(raw["classname"], [])
        if raw["classname"] in recipes:
            item["recipe"] = recipes[raw["classname"]]
            item["craftable"] = True
        catalog[item["id"]] = item

    for recipe_id, parts in recipes.items():
        if recipe_id in catalog:
            continue
        catalog[recipe_id] = {
            "id": recipe_id,
            "classname": recipe_id,
            "name": names.get(recipe_id) or humanize_classname(recipe_id),
            "category": "craftingbase",
            "categoryLabel": "Крафт",
            "image": find_icon(recipe_id, icons),
            "craftable": True,
            "description": "",
            "where": "Получается крафтом.",
            "tier": "—",
            "rarity": "крафт",
            "usage": [],
            "value": [],
            "loot": loot_index.get(recipe_id, []),
            "recipe": parts,
        }

    for item_id, override in override_items.items():
        if not isinstance(override, dict):
            continue
        base = catalog.get(item_id) or catalog.get(override.get("classname", ""), {})
        merged = merge_override(
            base
            or {
                "id": item_id,
                "classname": override.get("classname") or item_id,
                "name": item_id,
                "category": "other",
                "categoryLabel": "Прочее",
                "image": "",
                "craftable": False,
                "description": "",
                "where": "",
                "tier": "—",
                "rarity": "—",
                "usage": [],
                "value": [],
                "loot": [],
                "recipe": [],
            },
            override,
        )
        if not merged.get("image"):
            merged["image"] = find_icon(merged.get("classname") or item_id, icons) or find_icon(item_id, icons)
        if (merged.get("recipe") or merged.get("craftable")) and merged.get("rarity") in (None, "", "—"):
            merged["rarity"] = "крафт"
        catalog[merged["id"]] = merged

    prices = collect_prices()
    for row in prices:
        item = catalog.get(row["id"])
        if item:
            row["item"] = item["name"]
            row["image"] = item.get("image") or ""

    craftable = [
        item_id
        for item_id, item in catalog.items()
        if item.get("craftable") or item.get("recipe")
    ]
    craftable.sort(key=lambda item_id: catalog[item_id].get("name") or item_id)

    status = {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "items": len(catalog),
        "craftable": len(craftable),
        "prices": len(prices),
        "lootRows": sum(len(item.get("loot") or []) for item in catalog.values()),
        "icons": sum(1 for item in catalog.values() if item.get("image")),
        "missing": missing,
        "fromServer": folder_has_files(MISSION),
    }

    payload = {
        "status": status,
        "items": catalog,
        "craftable": craftable,
        "prices": prices,
    }
    write_generated(payload)
    print(
        f"готово: {status['items']} предметов, {status['craftable']} крафт, "
        f"{status['prices']} цен, {status['icons']} картинок"
    )
    if missing:
        print("ещё можно добавить:")
        for line in missing:
            print(" -", line)


if __name__ == "__main__":
    main()
