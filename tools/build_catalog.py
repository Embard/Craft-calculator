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

CATEGORY_ALIASES = {
    "lootdispatch": "vehiclesparts",
    "vehicleparts": "vehiclesparts",
    "medica": "medicine",
}

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
    "vehiclesparts": "Авто",
    "vehicles": "Авто",
    "medicine": "Медицина",
    "ammo": "Патроны",
    "magazines": "Магазины",
    "buildings": "Стройка",
    "animals": "Животные",
    "electronics": "Электроника",
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


def splatoon_lookup(classname: str, splatoon: set[str], splatoon_ci: dict[str, str] | None = None) -> str:
    """Exact classname, then case-insensitive match against S-Platoon catalog."""
    if not classname:
        return ""
    if classname in splatoon:
        return classname
    if splatoon_ci is None:
        return ""
    return splatoon_ci.get(classname.lower(), "")


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


def normalize_category(raw: str | None) -> str:
    key = (raw or "other").strip().lower() or "other"
    return CATEGORY_ALIASES.get(key, key)


def category_label(raw: str | None) -> str:
    if not raw:
        return "Прочее"
    key = normalize_category(raw)
    return CATEGORY_LABELS.get(key, raw)


def rarity_from(nominal: int | None, crafted: bool) -> str:
    if crafted:
        return "можно скрафтить"
    if nominal is None:
        return "—"
    if nominal <= 0:
        return "не встречается на карте"
    if nominal >= 100:
        return "очень часто"
    if nominal >= 50:
        return "часто"
    if nominal >= 25:
        return "средняя редкость"
    if nominal >= 10:
        return "редко"
    return "очень редко"


def refine_unmapped_rarity(catalog: dict[str, dict]) -> None:
    """Для nominal=0 пишем понятнее: крафт / купить у торговца / не на карте."""
    old_labels = {"не в экономике", "не встречается на карте"}
    for item in catalog.values():
        rarity = str(item.get("rarity") or "")
        nominal = item.get("nominal")
        zero_economy = nominal is not None and int(nominal) <= 0
        if not zero_economy and rarity not in old_labels:
            if rarity == "не встречается на карте":
                item["where"] = "—"
            continue

        craftable = bool(item.get("craftable") or (item.get("recipe") and len(item["recipe"])))
        traders = item.get("traders") or []
        can_buy = any(
            t.get("canBuy") or (t.get("buy") and t.get("buy") not in ("не продаёт", "—", "", None))
            for t in traders
        )
        can_sell_only = (not can_buy) and any(
            t.get("canSell") or (t.get("sell") and t.get("sell") not in ("не покупает", "—", "", None))
            for t in traders
        )

        if craftable and can_buy:
            item["rarity"] = "крафт / у торговца"
            if not str(item.get("where") or "").startswith("Крафт"):
                item["where"] = "—"
        elif craftable:
            item["rarity"] = "можно скрафтить"
            if not str(item.get("where") or "").startswith("Крафт"):
                item["where"] = "Крафт на станке HP_Crafter."
        elif can_buy:
            item["rarity"] = "у торговца"
            item["where"] = "—"
        else:
            item["rarity"] = "не встречается на карте"
            item["where"] = "—"


def clean_display_name(value: object, classname: str) -> str:
    if not isinstance(value, str):
        return humanize_classname(classname)
    name = value.strip()
    if not name or name.startswith("#") or name.startswith("STR_"):
        return humanize_classname(classname)
    return name


def where_from_types(item: dict) -> str:
    nominal = item.get("nominal")
    # nominal=0 / None — предмет не в экономике карты, usage в types.xml не значит спавн
    if nominal is None or int(nominal) <= 0:
        return "—"
    places = [USAGE_LABELS.get(u, u) for u in item.get("usage") or []]
    tiers = [VALUE_LABELS.get(v, v) for v in item.get("value") or []]
    parts = []
    if places:
        parts.append("Ищется: " + ", ".join(places) + ".")
    if tiers:
        parts.append("Зоны: " + ", ".join(tiers) + ".")
    parts.append(f"На карте цель экономики — около {nominal} шт.")
    if not parts:
        return "—"
    return " ".join(parts)


def where_from_loot(item: dict) -> str:
    nominal = item.get("nominal")
    if nominal is None or int(nominal) <= 0:
        return "—"
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
    if base == "—":
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


def _blocked_photo_md5() -> set[str]:
    path = ROOT / "tools" / "icon_dumper" / "blocked_photo_md5.txt"
    if not path.is_file():
        return set()
    return {
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }


def _file_md5(path: Path) -> str:
    import hashlib

    return hashlib.md5(path.read_bytes()).hexdigest().lower()


def copy_icons(classnames: set[str]) -> dict[str, str]:
    copied: dict[str, str] = {}
    wanted = {name.lower(): name for name in classnames}
    blocked = _blocked_photo_md5()
    IMG_ITEMS.mkdir(parents=True, exist_ok=True)
    sources = []
    sources.extend(iter_files(ICONS_IN, ("*.png", "*.jpg", "*.jpeg", "*.webp")))
    sources.extend(iter_files(WORKSHOP, ("*.png", "*.jpg", "*.jpeg", "*.webp")))
    for src in sources:
        key = src.stem
        match = wanted.get(key.lower())
        if not match:
            continue
        if blocked:
            try:
                if _file_md5(src) in blocked:
                    print(f"icon skip blocked photo {src.name}")
                    continue
            except OSError:
                pass
        dest = IMG_ITEMS / f"{match}{src.suffix.lower()}"
        if dest.exists():
            if blocked:
                try:
                    if _file_md5(dest) in blocked:
                        dest.unlink(missing_ok=True)
                        print(f"icon removed blocked photo {dest.name}")
                    else:
                        copied[match] = f"img/items/{dest.name}"
                        continue
                except OSError:
                    copied[match] = f"img/items/{dest.name}"
                    continue
            else:
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
        "category": normalize_category(raw.get("category")),
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


def classify_image_source(image: str) -> str:
    """Откуда взялась картинка в каталоге (без смены приоритетов)."""
    if not image:
        return "missing"
    lower = image.replace("\\", "/").lower()
    if lower.startswith("img/items/") or "/img/items/" in lower:
        return "local"
    if "s-platoon.ru" in lower:
        return "splatoon"
    return "other"


def _camel_tokens(classname: str) -> list[str]:
    parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", classname.replace("_", " "))
    return [p for p in parts if p]


# Жёсткий ignore: карта / прокси / триггеры — не инвентарные предметы.
_HARD_IGNORE_PREFIXES = (
    "Proxy",
    "Land_",
    "StaticObj_",
    "Static_",
    "Trigger",
    "AreaDamage",
    "EffectParticle",
    "EffectArea",
    "ContaminatedArea",
)

# Категории с явным пользовательским назначением (nominal=0 сам по себе не повод для ignore).
_USER_ITEM_CATEGORIES = {
    "weapons",
    "explosives",
    "clothes",
    "containers",
    "food",
    "tools",
    "medicine",
    "ammo",
    "magazines",
    "electronics",
    "craftingbase",
    "books",
}

_SOFT_TECH_TOKENS = {"ai", "abstract", "scripted", "dummy", "placeholder", "spawner", "zone", "effect", "debug"}


def has_usable_image(item: dict) -> bool:
    image = str(item.get("image") or "").strip()
    if not image:
        return False
    if image.startswith("http://") or image.startswith("https://"):
        return True
    return (ROOT / image.replace("\\", "/")).is_file()


def is_infected_classname(classname: str) -> bool:
    cn = classname or ""
    low = cn.lower()
    return (
        cn.startswith("Zmb")
        or cn.startswith("Zombie")
        or cn.startswith("Infected")
        or "ZombieBase" in cn
        or "_zmb_" in low
        or low.startswith("zmb_")
        or "ecolog" in low
    )


def is_animal_item(item: dict, classname: str) -> bool:
    if normalize_category(item.get("category")) == "animals":
        return True
    cn = classname or ""
    return cn.startswith("Animal_") or cn.startswith("AnimalBase")


def is_ai_entity(classname: str) -> bool:
    """NPC/AI-сущности, не предметы вроде AI-2 / Aimpoint."""
    cn = classname or ""
    markers = (
        "eAI_",
        "eAI",
        "ExpansionAI",
        "AI_Survivor",
        "AIPatrol",
        "AIAgent",
        "AI_Agent",
        "NBC_AI",
        "DayZCreatureAI",
    )
    if any(cn.startswith(m) or m in cn for m in markers):
        # аптечки AI-2 / AI-3 (RZ_Med_AI*) — предметы, не NPC
        if re.search(r"(Med|Injector|Syringe|Ammo|Mag_|Optic|Aimpoint)", cn, re.I):
            return False
        return True
    return False


_AUTO_CLASSNAME_RE = re.compile(
    r"("
    r"Doors?_|_Doors?_|Door_\d|_Door_|_Wheel\b|Wheel$|_trunk|_tent\b|"
    r"(?:Doors_)?hood(?:_|$)|(?<![A-Za-z])Hood(?![A-Za-z])|(?<=[a-z])Hood(?=_|$)|"
    r"CarBattery|TruckBattery|CarRadiator|SparkPlug|GlowPlug|EngineBelt|EngineOil|"
    r"CarWheel|TruckWheel|CivSedan|CivilianSedan|Hatchback|Offroad|Sedan_|Van_|Bus_|"
    r"Kamaz_|kamaz_|gaz_|GAZ_|ZIL_|zil_|Uaz_|UAZ_|Niva|Camper|"
    r"kraz_|Kraz_|V3S_|Transit|Vehicle|"
    r"Headlight|BrakeLight|CarTent|Truck_01|Boat_|TireRepair|CanisterGasoline|CarLock|sl_winch"
    r")",
    re.I,
)

_VEHICLE_PART_RE = re.compile(
    r"(?i)(Doors?_|_Doors?_|Door_\d|_Door_|Hood|Trunk|Wheel|Battery|Radiator|"
    r"_tent|Winch|CarLock|SparkPlug|GlowPlug|EngineOil|Headlight|BrakeLight|"
    r"TireRepair|CanisterGasoline|HydraulicJack)"
)

_WHOLE_VEHICLE_RE = re.compile(
    r"^(?:"
    r"CivilianSedan|OffroadHatchback|Offroad_02|Hatchback_02|Sedan_02|"
    r"Truck_01_Covered|Camper|Kamaz_|kamaz_|UAZ_|Uaz_|ZIL|Zil|"
    r"gaz_|GAZ_|Gaz_|kraz_|Kraz_|V3S|Transit|Niva|Boat_01"
    r")",
    re.I,
)


def is_wreck_or_static(classname: str) -> bool:
    cn = classname or ""
    return cn.startswith(("Land_", "StaticObj_", "Proxy")) or ("Wreck" in cn)


def is_whole_vehicle(item: dict, classname: str | None = None) -> bool:
    """Целая машина/лодка, которую видно в мире (не дверь/капот/колесо)."""
    cn = classname or str(item.get("classname") or item.get("id") or "")
    if not cn or is_wreck_or_static(cn):
        return False
    cat = normalize_category(item.get("category"))
    if cat in {"clothes", "weapons", "food", "ammo", "magazines"}:
        return False
    if re.search(r"(?i)Magazine|Book|gazebo|hoodie|hooded|Barricade", cn):
        return False
    name = str(item.get("name") or "").lower()
    if any(x in name for x in ("капот", "колесо", "двер", "багажник", "брезентовый тент", "радиатор")):
        return False
    if _VEHICLE_PART_RE.search(cn) and not re.match(r"(?i)Truck_01_Covered", cn):
        # Truck_01_Hood — деталь; Truck_01_Covered — машина
        if re.search(r"(?i)(Doors?_|Door_\d|Hood|Trunk|Wheel|Battery|Radiator|_tent)", cn):
            return False
    if _WHOLE_VEHICLE_RE.match(cn):
        return True
    if cat == "vehicles" and not _VEHICLE_PART_RE.search(cn):
        return True
    return False


def is_auto_item(item: dict, classname: str | None = None) -> bool:
    """Транспорт и детали машин (в т.ч. ошибочно попавшие в other/tools)."""
    cn = classname or str(item.get("classname") or item.get("id") or "")
    cat = normalize_category(item.get("category"))
    if cat == "clothes":
        return False
    if re.search(r"(?i)hoodie|hooded", cn):
        return False
    if "Barricade" in cn or "DoorBarricade" in cn:
        return False
    if is_whole_vehicle(item, cn):
        return True
    if cat in {"vehiclesparts", "vehicles"}:
        return True
    if _AUTO_CLASSNAME_RE.search(cn):
        if cat in {"tools", "other"} and re.search(r"(?i)hoodie|hooded|Jacket|Pants|Shirt", cn):
            return False
        return True
    name = str(item.get("name") or "").lower()
    if cat == "other" and any(
        marker in name
        for marker in (
            "брезентовый тент",
            "капот ",
            "колесо ",
            "багажник",
            "радиатор",
        )
    ):
        return True
    return False


def item_sold_by_trader(item: dict) -> bool:
    traders = item.get("traders") or []
    for row in traders:
        if not isinstance(row, dict):
            continue
        if row.get("canBuy"):
            return True
        buy = row.get("buy")
        if buy and buy not in ("не продаёт", "—", "", None):
            return True
    return False


def sold_at_auto_trader(item: dict) -> bool:
    """Магазины «Автозапчасти» / «Транспорт» (не любой трейдер)."""
    for row in item.get("traders") or []:
        if not isinstance(row, dict):
            continue
        if not (row.get("canBuy") or (row.get("buy") and row.get("buy") not in ("не продаёт", "—", "", None))):
            continue
        shop = str(row.get("shop") or "")
        if shop in {"Автозапчасти", "Транспорт"}:
            return True
    return False


def should_hide_from_items_book(item: dict) -> bool:
    """Скрыть из книги предметов (в крафте/ценах запись может остаться)."""
    classname = str(item.get("classname") or item.get("id") or "")
    name = str(item.get("name") or "")
    if is_infected_classname(classname):
        return True
    if is_animal_item(item, classname):
        return True
    if is_ai_entity(classname):
        return True
    if is_wreck_or_static(classname):
        return True
    # Бугры (тайники) и БТР — не нужны в книге
    if classname.startswith(("UndergroundStash", "Sib_underground_stash")) or name.strip() == "Бугор":
        return True
    if classname.startswith("BTR_") or name.strip().startswith("БТР"):
        return True
    # Базовый забор (иконка с s-platoon пустая / бесполезна)
    if classname == "Fence" or name.strip() == "Забор":
        return True
    # Кейсы-«сервисы» — убраны по запросу (водовоз/повар/утилизатор/чинилки)
    if classname in {
        "Xom_Aquarius_Case",
        "Xom_Repair_Case_Ruined",
        "Xom_Cooker_Case",
        "Xom_Utilizer_Case",
        "Xom_Repair_Case",
    }:
        return True
    name_l = name.lower().replace("ё", "е")
    if any(
        marker in name_l
        for marker in (
            "кейс-водовоз",
            "кейс-восстановитель",
            "кейс-повар",
            "кейс-утилизатор",
            "кейс-чинилка",
        )
    ):
        return True
    # Кишки / guts
    if "кишк" in name_l or classname in {"Guts", "SmallGuts", "AfroGuts", "Urban3ZombieGuts"}:
        return True
    if classname.endswith("Guts") or "ZombieGuts" in classname:
        return True
    # Костры
    name_norm = name_l.replace("ё", "е").strip()
    if name_norm == "костер" or name_norm.startswith("костер "):
        return True
    if classname in {
        "Fireplace",
        "FireplaceFireBarrel",
        "FireplaceIndoor",
        "OvenIndoor",
        "XWS_Fireplace_Eternal",
    }:
        return True
    if "fireplace" in classname.lower() and "kit" not in classname.lower():
        return True
    # Курильщик (Urban3 creature)
    if name.strip() == "Курильщик" or classname.startswith("Creature_Urban3"):
        return True
    # Ворота (RaG BB) — не путать с «воротник»
    if classname.startswith("RaG_BB_Gate"):
        return True
    if re.search(r"(?i)\bворот", name) and "воротник" not in name_l:
        return True
    # Лестницы (RaG BB)
    if classname.startswith(("RaG_BB_Stair", "RaG_BB_Ladder", "RaG_BB_StepLadder")):
        return True
    if "лестниц" in name_l or "stepladder" in name_l:
        return True
    # Тенты (рыболовные и т.п.) и окна RaG BB
    if "тент" in name_l.replace("ё", "е") or classname.startswith("FC_Fish_Tent"):
        return True
    if classname.startswith("RaG_BB_Window"):
        return True
    if name_norm in {"маленькое окно", "окно"} or name_norm.startswith("маленькое окно"):
        return True
    # Медсестра (creature), не платье
    if name.strip() == "Медсестра" or classname.startswith("Creature_Nurse"):
        return True
    # Могильный крест
    if "могильный крест" in name_l or "Gravecross" in classname or "GraveCross" in classname:
        return True
    # Пистолетные кейсы (без иконок)
    if "пистолетный кейс" in name_l or classname.startswith(("PC_Pistol_Case", "PC_Case")):
        return True
    # Площадка для укрытия
    if classname == "ShelterSite" or "площадка для укрытия" in name_l:
        return True
    # Поддоны (bl_pallet*)
    if classname.startswith("bl_pallet") or "поддон" in name_l:
        return True
    # Стена / столб (RaG BB)
    if classname.startswith(("RaG_BB_Wall", "RaG_BB_Pillar")):
        return True
    if name.strip() in {"Стена", "Столб"} or name_l in {"набор для стены", "набор для столба"}:
        return True

    # Пол (RaG BB), не «полевая»/«подсумок»
    if classname.startswith("RaG_BB_Floor") or name.strip() == "Пол" or name_l == "набор для пола":
        return True
    # Ракушки и рампа
    if "ракушк" in name_l or classname.startswith("FC_Fish_Other_Shell"):
        return True
    if classname.startswith("RaG_BB_Ramp") or name.strip() == "Рампа" or "набор для изготовления рампы" in name_l:
        return True
    # Сборщик дождя / свёрнутый календарь (без иконок)
    if (
        "сборщик дождя" in name_l
        or classname.startswith(("bl_rain_collector", "l_rain_collector"))
        or "свернутый календар" in name_l
        or classname.startswith("Custom_Calendar")
    ):
        return True
    # Спортивные сумки без иконок (TGK)
    if classname.startswith("TGK_Casual_Backpack"):
        return True
    if "спортивная сумка" in name_l and not has_usable_image(item):
        return True
    # Куртки без иконок (в т.ч. TGK тактические)
    if classname.startswith("TGK_RussianSolider_V3_TOP"):
        return True
    if "куртка" in name_l and not has_usable_image(item):
        return True
    # Тактические ремни без иконок (TGK)
    if classname.startswith("TGK_Casual_Belt"):
        return True
    if "тактический ремень" in name_l and not has_usable_image(item):
        return True
    # BRDK house (постройки/киты)
    if classname.startswith("BRDK_house") or "brdk house" in name_l:
        return True
    # Вагоны (поезд / Power Wagon)
    if "вагон" in name_l:
        return True
    if "Train_Wagon" in classname or classname.startswith("dodge_power_wagonrus"):
        return True
    if re.search(r"(?i)(^|_)wagon($|_)", classname) and "dragon" not in classname.lower():
        return True
    # EVG keycards / crates (без иконок)
    if classname.lower().startswith("evg_") or name_l.startswith("evg "):
        return True
    # Loftd без иконок (ghost/hijab и пр.)
    if classname.startswith("Loftd_") and not has_usable_image(item):
        return True

    # Целые машины из мира — показываем даже без иконки
    # (кроме резиновых лодок без картинки — плейсхолдер «Р»)
    if is_whole_vehicle(item, classname):
        if (
            name_l.strip() == "резиновая лодка" or classname.startswith("Boat_01_")
        ) and not classname.endswith("_Kit") and not has_usable_image(item):
            return True
        return False

    # Без картинки в книге не показываем (плейсхолдер «Б»)
    if not has_usable_image(item):
        return True

    # Детали авто — только если продаёт хоть кто-то
    if is_auto_item(item, classname) and not item_sold_by_trader(item):
        return True
    return False


def normalize_where_fields(catalog: dict[str, dict]) -> None:
    """Если в админ-данных нет места спавна — ставим «—»."""
    for item in catalog.values():
        where = str(item.get("where") or "").strip()
        if not where or where in {"-", "–", "—", "не встречается на карте", "не в экономике"}:
            item["where"] = "—"
            continue
        # нет ни лута, ни экономики, ни крафта, ни торговца — не выдумываем
        nominal = item.get("nominal")
        has_economy = nominal is not None and int(nominal) > 0
        has_loot = bool(item.get("loot"))
        has_craft = bool(item.get("craftable") or (item.get("recipe") and len(item["recipe"])))
        has_trader = bool(item.get("traders"))
        if not has_economy and not has_loot and not has_craft and not has_trader:
            item["where"] = "—"
        elif not has_economy and not has_loot and where.startswith("Ищется"):
            # usage без nominal — ложный след
            item["where"] = "—"


def mark_items_book_visibility(catalog: dict[str, dict]) -> dict[str, int]:
    stats = {"hidden": 0, "visible": 0, "auto": 0}
    for item in catalog.values():
        classname = str(item.get("classname") or item.get("id") or "")
        hide = should_hide_from_items_book(item)
        item["book"] = not hide
        if hide:
            stats["hidden"] += 1
            continue
        stats["visible"] += 1
        if is_whole_vehicle(item, classname) or sold_at_auto_trader(item) or is_auto_item(item, classname):
            # оружие из чужих категорий не переносим
            if normalize_category(item.get("category")) == "weapons":
                continue
            item["categoryLabel"] = "Авто"
            if normalize_category(item.get("category")) not in {"vehiclesparts", "vehicles"}:
                item["category"] = "vehiclesparts"
            stats["auto"] += 1
    # Повторно: «Прочее» без картинки — скрыть (на случай смены категории)
    for item in catalog.values():
        if not item.get("book"):
            continue
        if item.get("categoryLabel") == "Прочее" and not has_usable_image(item):
            item["book"] = False
            stats["hidden"] += 1
            stats["visible"] = max(0, stats["visible"] - 1)
    return stats


def hard_technical_ignore(classname: str) -> bool:
    if not classname:
        return True
    if "AdminDebug" in classname or "DebugTool" in classname:
        return True
    return any(classname.startswith(prefix) for prefix in _HARD_IGNORE_PREFIXES)


def soft_tech_flags(classname: str) -> list[str]:
    """Сомнительные техпризнаки: Base / ColorBase / AI — сами по себе не = ignore при user purpose."""
    flags: list[str] = []
    if not classname:
        return flags
    if classname.endswith("ColorBase"):
        flags.append("ColorBase")
    elif classname.endswith("_Base"):
        flags.append("Base")
    elif classname.endswith("Base") and len(classname) > 4 and classname[-5].islower():
        flags.append("Base")

    tokens = {t.lower() for t in _camel_tokens(classname)}
    tokens.update(p.lower() for p in classname.split("_") if p)
    hits = sorted(tokens & _SOFT_TECH_TOKENS)
    for hit in hits:
        flags.append(hit.upper() if hit == "ai" else hit)
    # unique order-preserving
    seen: set[str] = set()
    out: list[str] = []
    for flag in flags:
        if flag not in seen:
            seen.add(flag)
            out.append(flag)
    return out


def looks_like_trophy_or_collectible(classname: str, item: dict) -> bool:
    cn = classname or ""
    if re.search(r"(Trophy|Goldbar|GoldRing|painting|Paint)", cn, re.I):
        return True
    if re.search(r"(Head|Trophy)(_[fm])?$", cn, re.I):
        return True
    name = str(item.get("name") or "").lower()
    markers = ("трофей", "голова", "слиток", "картина", "кольцо", "коллекц")
    return any(marker in name for marker in markers)


def looks_like_user_classname(classname: str) -> str | None:
    """Эвристика classname, когда category=other (еда/одежда и т.п.)."""
    cn = classname or ""
    patterns = (
        (r"^(ANFood_|FC_Conserv_|Food|Meat|Can)", "food_classname"),
        (r"(Jacket|Pants|Boots|Gloves|Hat|Hoodie|Vest|Shirt|Bandana|Mask)", "clothes_classname"),
        (r"(Knife|Tool|Kit|Whetstone|Sewing|Hammer|Axe|Saw)", "tools_classname"),
        (r"^(Ammo_|Mag_|Magazine)", "ammo_classname"),
        (r"(Injector|Bandage|FirstAid|Morphine|Saline|Tetracycline|Pain)", "medicine_classname"),
    )
    for pattern, label in patterns:
        if re.search(pattern, cn, re.I):
            return label
    return None


def item_user_purpose(item: dict, reasons: list[str], classname: str) -> tuple[bool, str]:
    """Явное пользовательское назначение: крафт / торговцы / лут / категория / трофеи."""
    if item.get("traders") or "TraderPlusPriceConfig" in reasons:
        return True, "TraderPlus"
    if (
        item.get("craftable")
        or (item.get("recipe") and len(item["recipe"]))
        or "HP_Crafter.json" in reasons
        or "recipes" in reasons
    ):
        return True, "HP_Crafter_or_recipe"
    if item.get("loot") or "SearchForLoot.json" in reasons:
        return True, "loot"
    if any(r.startswith("Mod_ce/") and "spawnable" in r.lower() for r in reasons):
        return True, "spawnable_loot"

    category = normalize_category(item.get("category"))
    if category in _USER_ITEM_CATEGORIES:
        return True, f"category:{category}"

    if looks_like_trophy_or_collectible(classname, item):
        return True, "trophy_or_collectible"

    cn_hint = looks_like_user_classname(classname)
    if cn_hint:
        return True, cn_hint

    nominal = item.get("nominal")
    has_types = "types.xml" in reasons or any(
        r.startswith("Mod_ce/") and "spawnable" not in r.lower() for r in reasons
    )
    if has_types and nominal is not None and int(nominal) > 0:
        return True, "types_nominal_gt_0"

    return False, ""


def classify_missing_action(
    classname: str, item: dict, reasons: list[str]
) -> tuple[str, str | None]:
    """Возвращает (dump|review|ignore, review_reason|None)."""
    if hard_technical_ignore(classname):
        return "ignore", None

    soft = soft_tech_flags(classname)
    has_purpose, purpose = item_user_purpose(item, reasons, classname)

    # Base / ColorBase / AI + реальное назначение → review, не ignore.
    if soft and has_purpose:
        return "review", f"{purpose}; soft_tech:{','.join(soft)}"

    # Абстрактный/тех classname без назначения → ignore.
    if soft and not has_purpose:
        return "ignore", None

    if has_purpose:
        return "dump", None

    category = normalize_category(item.get("category"))
    if category in {"animals", "buildings"}:
        return "ignore", None

    # Нет сигналов пользователя — не гоняем в dumper.
    return "ignore", None


def add_ref(refs: dict[str, set[str]], classname: str | None, reason: str) -> None:
    if not classname:
        return
    refs.setdefault(classname, set()).add(reason)


def write_icon_report(catalog: dict[str, dict], refs: dict[str, set[str]]) -> dict:
    """Пишет data/icon_report.json и data/missing_icons.txt. Не меняет каталог."""
    DATA.mkdir(parents=True, exist_ok=True)
    report_items: list[dict] = []
    dump_list: list[str] = []
    counts = {"with_image": 0, "without_image": 0, "dump": 0, "review": 0, "ignore": 0}

    for item_id, item in sorted(catalog.items(), key=lambda kv: (kv[1].get("classname") or kv[0]).lower()):
        classname = item.get("classname") or item_id
        image = item.get("image") or ""
        image_source = classify_image_source(image)
        reasons = sorted(refs.get(classname, set()) | refs.get(item_id, set()))

        entry: dict = {
            "classname": classname,
            "name": item.get("name") or classname,
            "category": item.get("category") or "",
            "image": image,
            "imageSource": image_source,
        }

        if image_source != "missing":
            counts["with_image"] += 1
            entry["needed"] = False
            report_items.append(entry)
            continue

        counts["without_image"] += 1
        action, review_reason = classify_missing_action(classname, item, reasons)
        counts[action] += 1
        entry["needed"] = action == "dump"
        entry["status"] = action
        if review_reason:
            entry["review_reason"] = review_reason
        if reasons:
            entry["reasons"] = reasons
        report_items.append(entry)
        if action == "dump":
            dump_list.append(classname)

    dump_list = sorted(set(dump_list), key=str.lower)
    payload = {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "totals": {
            "items": len(catalog),
            "withImage": counts["with_image"],
            "withoutImage": counts["without_image"],
            "dump": counts["dump"],
            "review": counts["review"],
            "ignore": counts["ignore"],
        },
        "items": report_items,
    }
    report_path = DATA / "icon_report.json"
    missing_path = DATA / "missing_icons.txt"
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    missing_path.write_text("\n".join(dump_list) + ("\n" if dump_list else ""), encoding="utf-8")

    print()
    print("ICON REPORT")
    print()
    print(f"Всего предметов: {len(catalog)}")
    print(f"С изображением: {counts['with_image']}")
    print(f"Без изображения: {counts['without_image']}")
    print()
    print(f"Нужно выгрузить: {counts['dump']}")
    print(f"Требуют проверки: {counts['review']}")
    print(f"Игнорировано: {counts['ignore']}")
    print()
    print(f"wrote {report_path}")
    print(f"wrote {missing_path} ({len(dump_list)} classnames)")
    return payload["totals"]


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

    refs: dict[str, set[str]] = {}

    names = {}
    names.update(parse_stringtables())
    loot_names = parse_loot_names(source_names)
    names.update(loot_names)
    names.update(override_names)
    for classname in loot_names:
        add_ref(refs, classname, "Loot.json")

    hp_recipes, craft_meta, craft_categories = parse_hp_crafter(source_craft)
    loot_index = parse_search_for_loot(source_loot)
    for classname in loot_index:
        add_ref(refs, classname, "SearchForLoot.json")
    for result, parts in hp_recipes.items():
        add_ref(refs, result, "HP_Crafter.json")
        for part in parts:
            add_ref(refs, part.get("id"), "HP_Crafter.json")

    types_items = []
    if source_types.exists():
        types_items.extend(parse_types_xml(source_types))
        print(f"parsed {source_types.name}")
        for raw in types_items:
            add_ref(refs, raw.get("classname"), "types.xml")
    for path in iter_server_ce_files():
        if "spawnable" in path.name.lower():
            for row in parse_spawnable(path):
                classname = row.get("item")
                if not classname:
                    continue
                add_ref(refs, classname, f"Mod_ce/{path.name}")
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
        ce_items = parse_types_xml(path)
        types_items.extend(ce_items)
        for raw in ce_items:
            add_ref(refs, raw.get("classname"), f"Mod_ce/{path.name}")
        print(f"parsed Mod_ce/{path.name}")

    if not types_items:
        for path in iter_files(MISSION, ("*.xml",)):
            if "types" in path.name.lower() and "spawnable" not in path.name.lower():
                mission_items = parse_types_xml(path)
                types_items.extend(mission_items)
                for raw in mission_items:
                    add_ref(refs, raw.get("classname"), "types.xml")

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

    for item_id in override_items:
        add_ref(refs, item_id, "overrides/items.json")
        ov = override_items.get(item_id)
        if isinstance(ov, dict) and ov.get("classname"):
            add_ref(refs, ov["classname"], "overrides/items.json")
    for recipe_id, parts in recipes.items():
        if recipe_id in hp_recipes:
            continue
        add_ref(refs, recipe_id, "recipes")
        for part in parts:
            add_ref(refs, part.get("id"), "recipes")

    icons = copy_icons(classnames)
    splatoon = fetch_splatoon_classnames()
    splatoon_ci = {name.lower(): name for name in splatoon}
    catalog: dict[str, dict] = {}

    def apply_splatoon_image(item: dict, *candidates: str) -> None:
        if item.get("image"):
            return
        for candidate in candidates:
            matched = splatoon_lookup(candidate or "", splatoon, splatoon_ci)
            if matched:
                item["image"] = splatoon_thumb(matched)
                return

    for raw in types_items:
        item = build_item(raw, names, icons)
        apply_splatoon_image(item, raw["classname"])
        item["loot"] = loot_index.get(raw["classname"], [])
        if raw["classname"] in hp_recipes:
            item["recipe"] = hp_recipes[raw["classname"]]
            item["craftable"] = True
            item["rarity"] = "можно скрафтить"
            item["where"] = "Крафт на станке HP_Crafter."
        else:
            item["craftable"] = False
            item["recipe"] = []
            if item["loot"]:
                if (item.get("nominal") or 0) <= 0:
                    # SFL-точки при nominal=0 не считаем спавном на карте
                    item["where"] = "—"
                else:
                    item["where"] = where_from_loot(item)
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
            apply_splatoon_image(catalog[recipe_id], recipe_id)
            continue
        meta = craft_meta.get(recipe_id, {})
        image = find_icon(recipe_id, icons)
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
            "rarity": "можно скрафтить",
            "usage": [],
            "value": [],
            "loot": loot_index.get(recipe_id, []),
            "recipe": parts,
            "craftMeta": meta,
        }
        apply_splatoon_image(catalog[recipe_id], recipe_id)

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
        apply_splatoon_image(merged, merged.get("classname") or "", item_id)
        catalog[merged["id"]] = merged

    for item_id, item in catalog.items():
        apply_splatoon_image(item, item_id, item.get("classname") or "")

    prices = collect_prices()
    for row in prices:
        add_ref(refs, row.get("id"), "TraderPlusPriceConfig")
        item = catalog.get(row["id"])
        if item:
            row["item"] = item["name"]
            row["image"] = item.get("image") or ""
    attach_traders_to_items(catalog, prices)
    refine_unmapped_rarity(catalog)
    normalize_where_fields(catalog)
    book_stats = mark_items_book_visibility(catalog)
    print(
        f"книга предметов: видно {book_stats['visible']}, скрыто {book_stats['hidden']}, "
        f"в разделе «Авто» {book_stats.get('auto', 0)}"
    )

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
    icon_totals = write_icon_report(catalog, refs)
    status["iconReport"] = icon_totals
    (DATA / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
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
