#!/usr/bin/env python3
"""Propose replacements for selectors that no longer match the live site.

This is the "self-healing" half of an AI-assisted test workflow, with the
dangerous half deliberately removed: it NEVER edits a test file. It inspects the
live page, works out which element a broken selector used to match, proposes a
more stable replacement, verifies that proposal actually resolves, and prints a
diff for a human to review.

Why proposal-only. A healing agent that can rewrite tests can make a failing
suite pass by asserting less - deleting the step it cannot satisfy, or loosening
an assertion until it holds. That is the exact failure mode this suite was built
to catch: three of its video tests once passed while verifying nothing at all. An
agent allowed to commit its own fixes can recreate that silently and at speed, so
every proposal here goes through review, and any patch that would reduce the
assertions in a file is rejected outright (see assertion_signature).

Usage:
    python heal_selector.py --url URL --selector 'BROKEN' [--open 'SELECTOR'] \
                            [--test-file PATH]

Example - the real breakage in this repo's history (commit b3cd861), where
Squarespace renamed the lightbox arrow's label from "Next Item" to "Next":

    python heal_selector.py \
        --url https://thecmt.org/auditorium-2 \
        --selector '//a[@aria-label="Next Item"]' \
        --open 'img[data-src*="CMT+HouseLeft"]'
"""

import argparse
import ast
import math
import difflib
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

# Page-level containers are never the control we are looking for, and their
# class lists are theme soup that matches almost any token by accident.
STRUCTURAL = {"html", "body", "head", "script", "style", "noscript", "meta", "link", "title"}
MAX_CLASSES = 15          # more than this is a theme container, not a widget
INTERACTIVE = {"a", "button", "input", "select", "textarea"}

# Tag names and selector keywords carry no intent on their own.
GENERIC = {
    "a", "div", "span", "img", "button", "input", "li", "ul", "p", "h1", "h2",
    "xpath", "css", "text", "contains", "first", "last", "and", "or", "not",
    "the", "class", "id", "href", "src",
}


def parse_selector(selector):
    """Split a selector into the parts that carry intent.

    Quoted values ("Next Item") say what the element *is*; attribute names
    (aria-label) only say where that was written down. They are weighted
    differently because an attribute rename is the common breakage, and the
    thing that broke is exactly what we should stop relying on.
    """
    values = re.findall(r"['\"]([^'\"]+)['\"]", selector)
    attributes = re.findall(r"@([\w-]+)", selector)
    attributes += re.findall(r"\[([\w-]+)[\]=]", selector)
    tag_match = re.search(r"(?:^|/|\(|\s)([a-z][a-z0-9]*)(?:[\[\.\#]|$)", selector)

    tokens = []
    for value in values:
        for word in re.split(r"[\s\-_]+", value):
            word = word.lower()
            if len(word) > 1 and word not in GENERIC:
                tokens.append(word)

    return {
        "value_tokens": list(dict.fromkeys(tokens)),
        "attributes": list(dict.fromkeys(attributes)),
        "tag": tag_match.group(1) if tag_match else None,
        "raw": selector,
    }


def describe_elements(page):
    """Snapshot every element on the page with the facts we score against."""
    return page.evaluate(
        """() => [...document.querySelectorAll('*')].map((el, i) => {
            const r = el.getBoundingClientRect();
            const attrs = {};
            for (const a of el.attributes) attrs[a.name] = a.value;
            return {
                index: i,
                tag: el.tagName.toLowerCase(),
                id: el.id || null,
                classes: (el.className && el.className.baseVal !== undefined
                          ? el.className.baseVal : el.className || '').toString().split(/\\s+/).filter(Boolean),
                attrs,
                text: (el.innerText || '').trim().slice(0, 80),
                width: Math.round(r.width), height: Math.round(r.height),
                visible: !!(r.width && r.height),
            };
        })"""
    )


def identity_tokens(element):
    """The words an element uses to describe itself.

    Deliberately excludes descendant text: a container is not the button just
    because a button sits inside it.
    """
    parts = [element["id"] or ""]
    parts += element["classes"]
    parts += [f"{k} {v}" for k, v in element["attrs"].items() if k != "class"]
    tokens = set()
    for part in parts:
        for word in re.split(r"[\s\-_/.:]+", str(part).lower()):
            if len(word) > 1:
                tokens.add(word)
    return tokens


def token_weights(elements, intent):
    """Weight each intent token by how rare it is on this page.

    Not all words in a selector carry equal signal. In //a[@aria-label="Next
    Item"] the word that identifies the control is "next"; "item" is generic UI
    vocabulary that also appears on every nav link. Weighting by inverse
    document frequency lets the rare, discriminating word decide - the same
    idea search engines use to stop common words dominating a query.
    """
    total = max(len(elements), 1)
    weights = {}
    for token in intent["value_tokens"]:
        seen = sum(1 for el in elements if token in identity_tokens(el))
        weights[token] = round(3 * math.log(total / (1 + seen)), 1)
    return weights


def score(element, intent, viewport_area, weights):
    """How likely is this element the one the broken selector meant?

    Controls are small, interactive, and name themselves. Page containers are
    large and accumulate unrelated class names, so they are filtered out before
    scoring rather than merely out-scored - a body tag carrying 200 theme
    classes will otherwise match any token by coincidence.
    """
    if element["tag"] in STRUCTURAL or len(element["classes"]) > MAX_CLASSES:
        return 0, []

    tokens = identity_tokens(element)
    points = 0
    matched = []
    for token in intent["value_tokens"]:
        if token in tokens:
            points += weights.get(token, 3)
            matched.append(token)
    if not matched:
        return 0, []

    if intent["tag"] and element["tag"] == intent["tag"]:
        points += 2
    if element["tag"] in INTERACTIVE or element["attrs"].get("role") == "button":
        points += 2
    if element["visible"]:
        points += 1
    # A control occupies a small part of the page; a wrapper does not.
    area = element["width"] * element["height"]
    if viewport_area and area > 0.4 * viewport_area:
        points -= 5
    return points, matched


def propose(element, intent):
    """Build candidate selectors for an element, most stable first.

    The attribute that broke goes last: if aria-label was renamed once, it is
    the least trustworthy thing to key on next time.
    """
    broken_attrs = set(intent["attributes"])
    candidates = []

    for cls in element["classes"]:
        if any(t in cls.lower() for t in intent["value_tokens"]):
            candidates.append(f"{element['tag']}.{cls}")
    for cls in element["classes"]:
        selector = f"{element['tag']}.{cls}"
        if selector not in candidates:
            candidates.append(selector)

    for name, value in element["attrs"].items():
        if name.startswith("data-") and name not in broken_attrs and value:
            candidates.append(f"{element['tag']}[{name}='{value}']")

    if element["id"]:
        candidates.append(f"#{element['id']}")

    for name in broken_attrs:
        if name in element["attrs"]:
            candidates.append(f"{element['tag']}[{name}='{element['attrs'][name]}']")

    return candidates


def assertion_signature(source):
    """Count what a test file asserts, so a patch cannot quietly assert less."""
    tree = ast.parse(source)
    expects = asserts = 0
    methods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            asserts += 1
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "expect":
                expects += 1
            elif isinstance(func, ast.Attribute) and func.attr.startswith(
                ("to_be", "to_have", "not_to", "to_contain")
            ):
                methods.append(func.attr)
    return {"expect": expects, "assert": asserts, "methods": sorted(methods)}


def guard(original, patched):
    """Reject a patch that reduces what the file checks."""
    before, after = assertion_signature(original), assertion_signature(patched)
    problems = []
    if after["expect"] < before["expect"]:
        problems.append(f"expect() calls dropped {before['expect']} -> {after['expect']}")
    if after["assert"] < before["assert"]:
        problems.append(f"assert statements dropped {before['assert']} -> {after['assert']}")
    lost = set(before["methods"]) - set(after["methods"])
    if lost:
        problems.append(f"assertion methods removed: {', '.join(sorted(lost))}")
    return problems, before, after


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True, help="Page the selector is used on")
    ap.add_argument("--selector", required=True, help="The selector that no longer matches")
    ap.add_argument("--open", dest="open_selector", help="Click this first (e.g. to open a lightbox)")
    ap.add_argument("--test-file", help="Show a diff of this file with the proposal applied")
    ap.add_argument("--browser", default="firefox", choices=["firefox", "chromium", "webkit"])
    ap.add_argument("--top", type=int, default=3, help="How many candidate elements to show")
    args = ap.parse_args()

    intent = parse_selector(args.selector)
    print(f"Broken selector : {args.selector}")
    print(f"Reading intent  : tag={intent['tag']} "
          f"values={intent['value_tokens']} attributes={intent['attributes']}\n")

    with sync_playwright() as pw:
        browser = getattr(pw, args.browser).launch(headless=True)
        page = browser.new_page()
        page.goto(args.url, wait_until="load")

        still_matches = page.locator(args.selector).count()
        if still_matches:
            print(f"NOTE: that selector still matches {still_matches} element(s). Nothing to heal.")
            browser.close()
            return 0

        if args.open_selector:
            page.locator(args.open_selector).first.click()
            page.wait_for_timeout(2500)
            print(f"Opened with     : {args.open_selector}\n")

        elements = describe_elements(page)
        vp = page.viewport_size or {"width": 1280, "height": 720}
        viewport_area = vp["width"] * vp["height"]
        weights = token_weights(elements, intent)
        print("Token weights   : " + ", ".join(f"{t}={w}" for t, w in weights.items())
              + "   (rarer on the page = more discriminating)\n")
        ranked = []
        for el in elements:
            points, matched = score(el, intent, viewport_area, weights)
            if points > 1:
                ranked.append((points, matched, el))
        ranked.sort(key=lambda r: -r[0])

        if not ranked:
            print("No candidate element found. The element may be gone entirely,")
            print("which is a real failure worth a human looking at, not a heal.")
            browser.close()
            return 1

        print(f"Candidates (top {args.top}):")
        for points, matched, el in ranked[: args.top]:
            shown = el["classes"][:3]
            cls = ("." + ".".join(shown)) if shown else ""
            more = f" (+{len(el['classes']) - len(shown)} more)" if len(el["classes"]) > len(shown) else ""
            print(f"  score {round(points, 1)}  <{el['tag']}{cls}>{more}  "
                  f"matched={matched}  {el['width']}x{el['height']}px")
        print()

        _, _, best = ranked[0]
        proposal = None
        for candidate in propose(best, intent):
            count = page.locator(candidate).count()
            if count == 1:
                proposal = candidate
                print(f"Proposed        : {candidate}")
                print(f"Verified        : resolves to exactly 1 element on the live page")
                break
            elif count > 1:
                print(f"  rejected {candidate!r} - matches {count} elements, not unique")

        browser.close()

    if not proposal:
        print("\nNo unique replacement found. Needs a human.")
        return 1

    if args.test_file:
        path = Path(args.test_file)
        original = path.read_text()
        if args.selector not in original:
            print(f"\nNOTE: {args.selector!r} does not appear in {path}; no diff to show.")
            return 0
        patched = original.replace(args.selector, proposal)

        problems, before, after = guard(original, patched)
        print(f"\nAssertion guard : {before['expect']} expect() / {before['assert']} assert "
              f"-> {after['expect']} expect() / {after['assert']} assert")
        if problems:
            print("REJECTED - this patch would weaken the tests:")
            for p in problems:
                print(f"  - {p}")
            return 1
        print("PASSED - the patch changes locators only, assertions untouched\n")

        print("".join(difflib.unified_diff(
            original.splitlines(keepends=True), patched.splitlines(keepends=True),
            fromfile=f"a/{path.name}", tofile=f"b/{path.name}", n=2,
        )))
        print("Not applied. Review the diff and apply it yourself if it is right.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
