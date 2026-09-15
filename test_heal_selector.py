"""Unit tests for the self-healing proposal tool.

These are offline and fast - no browser, no network. The guard is the part that
matters most: it is what stops a healing agent from making a suite green by
making it test less, so it gets tested like any other safety-critical code.
"""

import pytest

from heal_selector import guard, identity_tokens, parse_selector, token_weights

pytestmark = pytest.mark.unit


ORIGINAL = '''
def check_images(page):
    expect(page.locator('//a[@aria-label="Next Item"]').first).to_be_visible()
    page.locator('//a[@aria-label="Next Item"]').click()
    expect(page.locator("//img[@alt='one']").first).to_have_text("one")
'''


def test_parse_selector_separates_values_from_attributes():
    intent = parse_selector('//a[@aria-label="Next Item"]')
    assert intent["value_tokens"] == ["next", "item"]
    assert intent["attributes"] == ["aria-label"]
    assert intent["tag"] == "a"


def test_rare_tokens_outweigh_common_ones():
    """The discriminating word should dominate the generic one."""
    elements = [
        {"id": None, "classes": ["sqs-lightbox-next"], "attrs": {}},
        *[{"id": None, "classes": ["header-nav-item"], "attrs": {}} for _ in range(20)],
    ]
    weights = token_weights(elements, {"value_tokens": ["next", "item"]})
    assert weights["next"] > weights["item"]


def test_identity_tokens_ignore_descendant_text():
    """A container is not the button just because a button sits inside it."""
    element = {"id": "wrap", "classes": ["outer"], "attrs": {}, "text": "Next Item"}
    assert "next" not in identity_tokens(element)


def test_guard_allows_a_locator_only_change():
    patched = ORIGINAL.replace('//a[@aria-label="Next Item"]', "a.sqs-lightbox-next")
    problems, before, after = guard(ORIGINAL, patched)
    assert problems == []
    assert before["expect"] == after["expect"] == 2


def test_guard_rejects_a_deleted_assertion():
    """The classic cheat: drop the step you cannot satisfy."""
    patched = "\n".join(
        line for line in ORIGINAL.splitlines() if "to_be_visible" not in line
    )
    problems, _, _ = guard(ORIGINAL, patched)
    assert problems, "guard must reject a patch that removes an assertion"
    assert any("expect" in p for p in problems)


def test_guard_rejects_a_weakened_assertion():
    """The subtler cheat: keep the call, assert something easier."""
    patched = ORIGINAL.replace("to_have_text", "to_be_attached")
    problems, _, _ = guard(ORIGINAL, patched)
    assert problems, "guard must reject swapping a strong assertion for a weaker one"
    assert any("to_have_text" in p for p in problems)


def test_guard_rejects_an_unparseable_patch():
    """A healing agent can emit broken Python. Reject it, do not crash."""
    problems, _, _ = guard(ORIGINAL, "def check_images(page:\n    expect(")
    assert problems, "guard must reject a patch that does not parse"
    assert any("does not parse" in p for p in problems)


def test_guard_allows_adding_assertions():
    patched = ORIGINAL + '    expect(page.locator("#x").first).to_be_visible()\n'
    problems, _, _ = guard(ORIGINAL, patched)
    assert problems == []
