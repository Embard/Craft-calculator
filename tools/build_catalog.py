#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает каталог сайта из файлов админа.

Положите миссию, profiles и моды в ../incoming и запустите этот скрипт.
Он пишет js/generated.js — страницы сайта читают его сразу.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
import json
import re
import shutil
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
INCOMING = ROOT / "incoming"
MISSION = INCOMING / "mission"
PROFILES = INCOMING / "profiles"
WORKSHOP = INCOMING / "workshop"
ICONS_IN = INCOMING / "icons"
OVERRIDES = INCOMING / "overrides"
SOURCES = INCOMING / "sources"
DATA = ROOT / "data"
IMG_ITEMS = ROOT / "img" / "items"
GENERATED_JS = ROOT / "js" / "generated.js"
SPLATOON_PAGE = "https://s-platoon.ru/online-tools/items/"
SPLATOON_THUMB = "https://s-platoon.ru/uploads/dayz-items/thumb/"
SPLATOON_CACHE = INCOMING / "splatoon-catalog.js"

# Имена как на сервере. Другие xml/json парсер не трогает.
SERVER_SOURCE_FILES = ("types.xml", "Loot.json", "HP_Crafter.json", "SearchForLoot.json")
SERVER_TRADER_FILES = (
    "TraderPlusPriceConfig.json",
    "TraderPlusIDsConfig.json",
    "ZoneCore_npcs.json",
)
SERVER_CE_DIR = "Mod_ce"

CATEGORY_LABELS = {
    "weapons": "Оружие",
    "explosives": "Взрывчатка",
    "clothes": "Одежда",
    "containers": "Контейнеры и рюкзаки",
    "food": "Еда",
    "tools": "Инструменты",
    "craftingbase": "Крафт",
    "books": "Книги",
    "recipes": "Рецепты",
    "vehiclesparts": "Запчасти транспорта",
    "vehicleparts": "Запчасти транспорта",
    "vehicles": "Транспорт",
    "armor": "Броня",
    "material": "Материал",
    "medicine": "Медицина",
    "medica": "Медицина",
    "ammo": "Патроны",
    "magazines": "Магазины",
    "buildings": "Стройка",
    "animals": "Животные",
    "electronics": "Электроника",
    "lootdispatch": "Лут",
}

USAGE_LABELS = {
    "Military": "На военных объектах",
    "Police": "В полицейских участках",
    "Medic": "На медицинских объектах",
    "Medical": "На медицинских объектах",
    "Firefighter": "В пожарных частях",
    "Town": "В городах",
    "Village": "В деревнях",
    "Coast": "На побережье",
    "Farm": "На фермах",
    "Industrial": "На заводах и складах",
    "Hunting": "В охотничьих домиках",
    "School": "В школах",
    "Office": "В офисах",
    "Prison": "В тюрьмах",
    "Lunapark": "В парках аттракционов",
    "Historical": "В исторических местах",
    "Restaurant": "В кафе и ресторанах",
    "Contaminated": "В заражённых зонах",
    "Camp": "В лагерях",
    "Work": "На рабочих местах",
    "Railway": "На железной дороге",
    "Airfield": "На аэродромах",
}

VALUE_LABELS = {
    "Tier1": "тир 1, побережье",
    "Tier2": "тир 2, середина",
    "Tier3": "тир 3, дальние деревни",
    "Tier4": "тир 4, север",
    "Unique": "уникальный",
}

PLACE_LABELS = {
    "Civilian": "Гражданские дома",
    "Industrial": "Заводы и склады",
    "Farm": "Фермы и сараи",
    "Hunting": "Охотничьи домики",
    "Police": "Полицейские участки",
    "Medical": "Больницы и медпункты",
    "Military": "Военные объекты",
}

SUBCAT_LABELS = {
    "Food": "еда",
    "Clothing": "одежда",
    "Tools": "инструменты и барахло",
    "Unique": "уникальные предметы",
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


def _http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 GranZakataHandbook"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def fetch_splatoon_classnames() -> set[str]:
    text = ""
    try:
        page = _http_get(SPLATOON_PAGE).decode("utf-8", "replace")
        match = re.search(r"https://s-platoon\.ru/uploads/pages_media/[^\"']+app-ite[^\"']+\.js", page)
        catalog_url = match.group(0) if match else ""
        if catalog_url:
            text = _http_get(catalog_url).decode("utf-8", "replace")
            SPLATOON_CACHE.write_text(text, encoding="utf-8")
            print(f"s-platoon catalog: {catalog_url}")
    except Exception as exc:
        print(f"s-platoon download failed: {exc}")
    if not text and SPLATOON_CACHE.exists():
        text = SPLATOON_CACHE.read_text(encoding="utf-8", errors="replace")
        print("s-platoon catalog: cache")
    marker = "window.SPL_DAYZ_ITEMS="
    if marker not in text:
        return set()
    raw = text.split(marker, 1)[1]
    raw = raw.strip()
    if raw.endswith(";"):
        raw = raw[:-1]
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"s-platoon json failed: {exc}")
        return set()
    names = {item.get("c") for item in items if isinstance(item, dict) and item.get("c")}
    print(f"s-platoon images: {len(names)}")
    return names


def splatoon_thumb(classname: str) -> str:
    return SPLATOON_THUMB + quote(classname, safe="") + ".webp"


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
        return "не в экономике"
    if nominal >= 100:
        return "очень часто"
    if nominal >= 50:
        return "часто"
    if nominal >= 25:
        return "средняя редкость"
    if nominal >= 10:
        return "редко"
    return "очень редко"


def clean_display_name(value: object, classname: str) -> str:
    if not isinstance(value, str):
        return humanize_classname(classname)
    name = value.strip()
    if not name or name.startswith("#") or name.startswith("STR_"):
        return humanize_classname(classname)
    return name


def where_from_types(item: dict) -> str:
    places = [USAGE_LABELS.get(u, u) for u in item.get("usage") or []]
    tiers = [VALUE_LABELS.get(v, v) for v in item.get("value") or []]
    parts = []
    if places:
        parts.append("Ищется: " + ", ".join(places) + ".")
    if tiers:
        parts.append("Зоны: " + ", ".join(tiers) + ".")
    nominal = item.get("nominal")
    if nominal not in (None, 0):
        parts.append(f"На карте цель экономики — около {nominal} шт.")
    if not parts:
        return "В файлах сервера нет точки спавна. Проверьте торговца, квест или крафт."
    return " ".join(parts)


def where_from_loot(item: dict) -> str:
    loot = item.get("loot") or []
    if not loot:
        return where_from_types(item)
    places = []
    seen = set()
    for zone in loot[:8]:
        house = zone.get("house") or ""
        if not house or house in seen:
            continue
        seen.add(house)
        bit = house
        if zone.get("tier"):
            bit += f" ({zone['tier']})"
        if zone.get("chance"):
            bit += f", шанс {zone['chance']}"
        places.append(bit)
    text = "Лут: " + "; ".join(places) + "."
    base = where_from_types({**item, "usage": item.get("usage") or [], "value": item.get("value") or []})
    if base.startswith("В файлах"):
        return text
    return text + " " + base


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


def _price_number(raw) -> int | None:
    if raw in (None, "", "-1", -1):
        return None
    try:
        value = int(float(str(raw).strip()))
    except ValueError:
        return None
    return value if value >= 0 else None


def _format_money(value: int | None, currency: str) -> str:
    if value is None:
        return "—"
    if currency == "золото":
        return f"{value} зол."
    return f"{value} ₽"


def _currency_label(accepted: list | None) -> str:
    joined = " ".join(str(x) for x in (accepted or [])).lower()
    if "nugget" in joined or "goldbar" in joined:
        return "золото"
    return "рубли"


def parse_zone_traders(path: Path) -> dict[int, dict]:
    """DialogId / TraderPlus Id → NPC."""
    raw = load_json(path, {})
    traders: dict[int, dict] = {}
    for npc in raw.get("NPCs") or []:
        if not isinstance(npc, dict):
            continue
        trader_ids = []
        for link in npc.get("Links") or []:
            if isinstance(link, dict) and str(link.get("Type", "")).lower() == "traderplus":
                try:
                    trader_ids.append(int(link.get("Id")))
                except (TypeError, ValueError):
                    continue
        if not trader_ids and npc.get("DialogId") is not None:
            try:
                trader_ids.append(int(npc.get("DialogId")))
            except (TypeError, ValueError):
                pass
        pos = npc.get("Position") or []
        for trader_id in trader_ids:
            traders[trader_id] = {
                "id": trader_id,
                "name": npc.get("DisplayName") or f"Торговец {trader_id}",
                "shop": next(
                    (
                        link.get("Label")
                        for link in (npc.get("Links") or [])
                        if isinstance(link, dict)
                        and str(link.get("Type", "")).lower() == "traderplus"
                        and int(link.get("Id", -1)) == trader_id
                    ),
                    "",
                ),
                "position": pos,
            }
    return traders


def parse_trader_ids(path: Path) -> dict[int, dict]:
    raw = load_json(path, {})
    mapping: dict[int, dict] = {}
    for entry in raw.get("IDs") or []:
        if not isinstance(entry, dict) or entry.get("Id") is None:
            continue
        try:
            trader_id = int(entry["Id"])
        except (TypeError, ValueError):
            continue
        mapping[trader_id] = {
            "categories": list(entry.get("Categories") or []),
            "currency": _currency_label(entry.get("CurrenciesAccepted")),
        }
    return mapping


def parse_trader_products(path: Path) -> dict[str, list[dict]]:
    """CategoryName → product rows."""
    raw = load_json(path, {})
    by_category: dict[str, list[dict]] = {}
    for cat in raw.get("TraderCategories") or []:
        if not isinstance(cat, dict):
            continue
        category = cat.get("CategoryName") or "Прочее"
        products = []
        for product in cat.get("Products") or []:
            classname = None
            buy_raw = None
            sell_raw = None
            if isinstance(product, str):
                # ClassName,Coefficient,MaxStock,TradeQuantity,BuyPrice,SellPrice
                parts = [p.strip() for p in product.split(",")]
                if not parts or not parts[0]:
                    continue
                classname = parts[0]
                buy_raw = parts[4] if len(parts) > 4 else None
                sell_raw = parts[5] if len(parts) > 5 else None
            elif isinstance(product, dict):
                classname = product.get("ClassName") or product.get("Classname") or product.get("Name")
                buy_raw = product.get("BuyPrice", product.get("Buy", product.get("MaxPriceThreshold")))
                sell_raw = product.get("SellPrice", product.get("Sell", product.get("MinPriceThreshold")))
            if not classname:
                continue
            products.append(
                {
                    "id": classname,
                    "buy": _price_number(buy_raw),
                    "sell": _price_number(sell_raw),
                }
            )
        by_category[category] = products
    return by_category


def collect_prices() -> list[dict]:
    """Цены с привязкой к NPC из TraderPlus + ZoneCore."""
    price_path = SOURCES / "TraderPlusPriceConfig.json"
    ids_path = SOURCES / "TraderPlusIDsConfig.json"
    npc_path = SOURCES / "ZoneCore_npcs.json"

    # Fallback: старый путь profiles, если админ положил туда
    if not price_path.exists():
        for path in iter_files(PROFILES, ("*TraderPlusPrice*.json", "*PriceConfig*.json")):
            price_path = path
            break
    if not ids_path.exists():
        for path in iter_files(PROFILES, ("*TraderPlusIDs*.json", "*IDsConfig*.json")):
            ids_path = path
            break
    if not npc_path.exists():
        for path in iter_files(PROFILES, ("*ZoneCore*npc*.json", "*npc*.json")):
            npc_path = path
            break

    if not price_path.exists():
        return []

    products_by_cat = parse_trader_products(price_path)
    trader_ids = parse_trader_ids(ids_path) if ids_path.exists() else {}
    npcs = parse_zone_traders(npc_path) if npc_path.exists() else {}

    category_owners: dict[str, list[dict]] = {}
    for trader_id, meta in trader_ids.items():
        npc = npcs.get(trader_id, {})
        owner = {
            "traderId": trader_id,
            "npc": npc.get("name") or f"Торговец #{trader_id}",
            "shop": npc.get("shop") or "",
            "currency": meta.get("currency") or "рубли",
        }
        for category in meta.get("categories") or []:
            category_owners.setdefault(category, []).append(owner)

    prices: list[dict] = []
    seen = set()
    for category, products in products_by_cat.items():
        owners = category_owners.get(category)
        if not owners:
            owners = [
                {
                    "traderId": None,
                    "npc": category,
                    "shop": category,
                    "currency": "рубли",
                }
            ]
        for product in products:
            for owner in owners:
                key = (product["id"], owner.get("traderId"), owner["npc"], category, product["buy"], product["sell"])
                if key in seen:
                    continue
                seen.add(key)
                currency = owner["currency"]
                buy = product["buy"]
                sell = product["sell"]
                prices.append(
                    {
                        "id": product["id"],
                        "item": product["id"],
                        "trader": owner["npc"],
                        "npc": owner["npc"],
                        "shop": owner.get("shop") or category,
                        "category": category,
                        "traderId": owner.get("traderId"),
                        "currency": currency,
                        "buy": _format_money(buy, currency) if buy is not None else "не продаёт",
                        "sell": _format_money(sell, currency) if sell is not None else "не покупает",
                        "buyValue": buy,
                        "sellValue": sell,
                        "canBuy": buy is not None,
                        "canSell": sell is not None,
                    }
                )
    return prices


def attach_traders_to_items(catalog: dict[str, dict], prices: list[dict]) -> None:
    by_item: dict[str, list[dict]] = {}
    for row in prices:
        by_item.setdefault(row["id"], []).append(row)
    for item_id, item in catalog.items():
        rows = by_item.get(item_id) or by_item.get(item.get("classname") or "", [])
        if not rows:
            item["traders"] = []
            continue
        # компактный список для карточки предмета
        compact = []
        seen = set()
        for row in rows:
            key = (row.get("npc"), row.get("buyValue"), row.get("sellValue"), row.get("category"))
            if key in seen:
                continue
            seen.add(key)
            compact.append(
                {
                    "npc": row.get("npc") or row.get("trader"),
                    "shop": row.get("shop") or "",
                    "category": row.get("category") or "",
                    "buy": row.get("buy"),
                    "sell": row.get("sell"),
                    "canBuy": bool(row.get("canBuy")),
                    "canSell": bool(row.get("canSell")),
                }
            )
        item["traders"] = compact


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
    skip = {"hp_crafter.json", "loot.json", "searchforloot.json", "recipes.json", "recipes.html"}
    for path in iter_files(INCOMING, ("*recipe*.json", "*craft*.json")):
        if "overrides" in path.parts:
            continue
        if path.name.lower() in skip:
            continue
        if path.name.lower().endswith(".html"):
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


def parse_loot_names(path: Path) -> dict[str, str]:
    raw = load_json(path, {})
    names: dict[str, str] = {}
    if not isinstance(raw, dict):
        return names
    for classname, value in raw.items():
        names[classname] = clean_display_name(value, classname)
    return names


def parse_hp_crafter(path: Path) -> tuple[dict[str, list[dict]], dict[str, dict], dict[str, list[str]]]:
    craft: dict[str, list[dict]] = {}
    meta: dict[str, dict] = {}
    categories: dict[str, list[str]] = {}
    raw = load_json(path, {})
    classes = raw.get("m_CraftClasses") if isinstance(raw, dict) else {}
    if not isinstance(classes, dict):
        return craft, meta, categories
    for cat in classes.get("CraftCategories") or []:
        if not isinstance(cat, dict):
            continue
        cat_name = cat.get("CategoryName") or "Прочее"
        categories.setdefault(cat_name, [])
        for item in cat.get("CraftItems") or []:
            if not isinstance(item, dict):
                continue
            result = item.get("Result")
            if not result:
                continue
            comps = []
            for component in item.get("CraftComponents") or []:
                if not isinstance(component, dict) or not component.get("Classname"):
                    continue
                comps.append({"id": component["Classname"], "qty": int(component.get("Amount") or 1)})
            craft[result] = comps
            meta[result] = {
                "recipe_name": item.get("RecipeName") or "",
                "craft_type": item.get("CraftType") or "craftpic",
                "category": cat_name,
                "result_count": item.get("ResultCount") or 1,
            }
            if result not in categories[cat_name]:
                categories[cat_name].append(result)
    return craft, meta, categories


def parse_search_for_loot(path: Path) -> dict[str, list[dict]]:
    loot: dict[str, list[dict]] = {}
    raw = load_json(path, {})
    for cat in raw.get("SFLLootCategory") or []:
        if not isinstance(cat, dict):
            continue
        cat_name = cat.get("name") or ""
        rarity = cat.get("rarity", 50)
        parts = cat_name.split("_")
        prefix = parts[0] if parts else ""
        tier = "—"
        sub = "—"
        for part in parts:
            match = re.match(r"^Tier(\d+)$", part)
            if match:
                tier = "T" + str(min(int(match.group(1)), 4))
            if part in SUBCAT_LABELS:
                sub = part
        if "Unique" in cat_name:
            tier = "Uniq"
        chance = f"{int(float(rarity))}%"
        house = PLACE_LABELS.get(prefix, prefix)
        for classname in cat.get("loot") or []:
            if not classname:
                continue
            loot.setdefault(classname, []).append(
                {
                    "house": house,
                    "category": SUBCAT_LABELS.get(sub, sub),
                    "tier": tier,
                    "chance": chance,
                }
            )
    for classname, zones in loot.items():
        seen = set()
        unique = []
        for zone in zones:
            key = (zone["house"], zone["category"], zone["tier"])
            if key in seen:
                continue
            seen.add(key)
            unique.append(zone)
        loot[classname] = unique
    return loot


def iter_server_ce_files():
    ce_dir = SOURCES / SERVER_CE_DIR
    if not ce_dir.exists():
        return
    for path in sorted(ce_dir.glob("*.xml")):
        yield path


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
    # «крафт» в карточке только для стола HP_Crafter; флаг types.xml тут не используем
    nominal = raw.get("nominal")
    name = names.get(classname) or humanize_classname(classname)
    name = clean_display_name(name, classname)
    return {
        "id": classname,
        "classname": classname,
        "name": name,
        "category": (raw.get("category") or "other").lower(),
        "categoryLabel": category_label(raw.get("category")),
        "image": find_icon(classname, icons),
        "craftable": False,
        "description": "",
        "where": where_from_types(raw),
        "tier": (raw.get("value") or ["—"])[0],
        "rarity": rarity_from(nominal, False),
        "usage": raw.get("usage") or [],
        "value": raw.get("value") or [],
        "nominal": nominal,
        "min": raw.get("min"),
        "loot": [],
        "recipe": [],
        "traders": [],
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
    compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    (DATA / "catalog.json").write_text(compact, encoding="utf-8")
    (DATA / "status.json").write_text(json.dumps(payload.get("status", {}), ensure_ascii=False, indent=2), encoding="utf-8")
    GENERATED_JS.write_text("window.GZ_GENERATED = " + compact + ";\n", encoding="utf-8")
    print(f"wrote {GENERATED_JS}")


def main() -> None:
    for folder in (MISSION, PROFILES, WORKSHOP, ICONS_IN, OVERRIDES, SOURCES):
        folder.mkdir(parents=True, exist_ok=True)
    (SOURCES / SERVER_CE_DIR).mkdir(parents=True, exist_ok=True)

    missing = []
    source_types = SOURCES / "types.xml"
    source_names = SOURCES / "Loot.json"
    source_craft = SOURCES / "HP_Crafter.json"
    source_loot = SOURCES / "SearchForLoot.json"
    has_sources = source_types.exists()
    if not has_sources:
        missing.append("incoming/sources/types.xml")
    for name in SERVER_SOURCE_FILES:
        if not (SOURCES / name).exists():
            missing.append(f"incoming/sources/{name}")
    if not any((SOURCES / SERVER_CE_DIR).glob("*.xml")):
        missing.append("incoming/sources/Mod_ce — нет XML модов")
    if not folder_has_files(PROFILES) and not (SOURCES / "TraderPlusPriceConfig.json").exists():
        missing.append("incoming/sources/TraderPlusPriceConfig.json — нет цен торговцев")
    for name in SERVER_TRADER_FILES:
        if not (SOURCES / name).exists() and name != "TraderPlusPriceConfig.json":
            missing.append(f"incoming/sources/{name}")
    if not folder_has_files(WORKSHOP) and not folder_has_files(ICONS_IN):
        missing.append("incoming/icons — нет PNG иконок")

    override_items = load_json(OVERRIDES / "items.json", {})
    override_names = load_json(OVERRIDES / "names.json", {})
    override_recipes = load_json(OVERRIDES / "recipes.json", {})

    names = {}
    names.update(parse_stringtables())
    names.update(parse_loot_names(source_names))
    names.update(override_names)

    hp_recipes, craft_meta, craft_categories = parse_hp_crafter(source_craft)
    loot_index = parse_search_for_loot(source_loot)

    types_items = []
    if source_types.exists():
        types_items.extend(parse_types_xml(source_types))
        print(f"parsed {source_types.name}")
    for path in iter_server_ce_files():
        if "spawnable" in path.name.lower():
            for row in parse_spawnable(path):
                classname = row.get("item")
                if not classname:
                    continue
                chance = row.get("chance")
                chance_text = (
                    f"{float(chance) * 100:.0f}%"
                    if chance and str(chance).replace(".", "", 1).isdigit()
                    else (chance or "")
                )
                loot_index.setdefault(classname, []).append(
                    {
                        "house": row.get("place") or "неизвестно",
                        "category": row.get("kind") or "лут",
                        "tier": "",
                        "chance": chance_text,
                    }
                )
            continue
        types_items.extend(parse_types_xml(path))
        print(f"parsed Mod_ce/{path.name}")

    if not types_items:
        for path in iter_files(MISSION, ("*.xml",)):
            if "types" in path.name.lower() and "spawnable" not in path.name.lower():
                types_items.extend(parse_types_xml(path))

    recipes = {}
    recipes.update(collect_json_recipes())
    recipes.update(collect_script_recipes())
    recipes.update(hp_recipes)
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
    splatoon = fetch_splatoon_classnames()
    catalog: dict[str, dict] = {}

    for raw in types_items:
        item = build_item(raw, names, icons)
        local = item.get("image") or ""
        if not local and raw["classname"] in splatoon:
            item["image"] = splatoon_thumb(raw["classname"])
        item["loot"] = loot_index.get(raw["classname"], [])
        if raw["classname"] in hp_recipes:
            item["recipe"] = hp_recipes[raw["classname"]]
            item["craftable"] = True
            item["rarity"] = "крафт"
            item["where"] = "Крафт на станке HP_Crafter."
        else:
            item["craftable"] = False
            item["recipe"] = []
            if item["loot"]:
                item["where"] = where_from_loot(item)
                if (item.get("nominal") or 0) <= 0:
                    # есть точки в SearchForLoot, но nominal=0
                    chances = []
                    for zone in item["loot"]:
                        ch = str(zone.get("chance") or "").replace("%", "")
                        if ch.replace(".", "", 1).isdigit():
                            chances.append(float(ch))
                    avg = sum(chances) / len(chances) if chances else 50
                    # rarity шкалуем от шанса SFL
                    item["rarity"] = rarity_from(100 if avg >= 80 else 50 if avg >= 50 else 25 if avg >= 30 else 10 if avg >= 15 else 5, False)
        meta = craft_meta.get(raw["classname"])
        if meta:
            item["craftMeta"] = meta
            if meta.get("recipe_name") and not item.get("description"):
                item["description"] = meta["recipe_name"]
        catalog[item["id"]] = item

    for recipe_id, parts in hp_recipes.items():
        if recipe_id in catalog:
            catalog[recipe_id]["recipe"] = parts
            catalog[recipe_id]["craftable"] = True
            if not catalog[recipe_id].get("image") and recipe_id in splatoon:
                catalog[recipe_id]["image"] = splatoon_thumb(recipe_id)
            continue
        meta = craft_meta.get(recipe_id, {})
        image = find_icon(recipe_id, icons)
        if not image and recipe_id in splatoon:
            image = splatoon_thumb(recipe_id)
        catalog[recipe_id] = {
            "id": recipe_id,
            "classname": recipe_id,
            "name": names.get(recipe_id) or humanize_classname(recipe_id),
            "category": "craftingbase",
            "categoryLabel": meta.get("category") or "Крафт",
            "image": image,
            "craftable": True,
            "description": meta.get("recipe_name") or "",
            "where": "Получается крафтом на станке.",
            "tier": "—",
            "rarity": "крафт",
            "usage": [],
            "value": [],
            "loot": loot_index.get(recipe_id, []),
            "recipe": parts,
            "craftMeta": meta,
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
            classname = merged.get("classname") or item_id
            if not merged.get("image") and classname in splatoon:
                merged["image"] = splatoon_thumb(classname)
        catalog[merged["id"]] = merged

    for item_id, item in catalog.items():
        if not item.get("image") and item_id in splatoon:
            item["image"] = splatoon_thumb(item_id)
        elif not item.get("image") and item.get("classname") in splatoon:
            item["image"] = splatoon_thumb(item["classname"])

    prices = collect_prices()
    for row in prices:
        item = catalog.get(row["id"])
        if item:
            row["item"] = item["name"]
            row["image"] = item.get("image") or ""
    attach_traders_to_items(catalog, prices)

    craftable = [
        item_id
        for item_id in hp_recipes
        if item_id in catalog
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
        "fromServer": has_sources,
    }

    payload = {
        "status": status,
        "items": catalog,
        "craftable": craftable,
        "craftCategories": craft_categories,
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
