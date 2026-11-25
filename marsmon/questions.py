"""Every question MarsMon asks about an image, in one place.

The hand-labelling page and the Jev requests both read these definitions, so a person
and the model answer the same question with the same criteria. `photo` is the name of
the image in the request state.

Rules for editing (see docs/CONCEPT.md):
- one judgment per question; describe each option or answer as a concrete situation;
- change wording only to make a definition clearer for a person, never to make one
  test image come out a certain way;
- bump VERSION on any change, so labels and answers record which wording they used.
"""

VERSION = "terrain-v2"  # v2: steep_slope means a hillside anywhere in view (25 Nov 2026)

TERRAIN = [
    {
        "id": "ground_visible",
        "kind": "noul",
        "text": "Does natural ground (soil, sand or rock) fill most of `photo`?",
        "true": "Most of the picture is the Martian surface near the rover.",
        "false": "Most of the picture is sky, the rover's own hardware, or deep shadow.",
    },
    {
        "id": "main_terrain",
        "kind": "choice",
        "text": "Which kind of ground covers most of `photo`?",
        "options": {
            "layered_outcrop": "Exposed rock stands out of the ground and shows stacked layers or bands, like steps or a cut cake.",
            "flat_bedrock": "Flat or gently tilted solid rock forms the surface, broken into slabs or plates.",
            "scattered_boulders": "Large rocks, each clearly bigger than the stones around it, are spread across the ground.",
            "loose_pebbles": "Soil covered with small loose stones and pebbles, with no large rocks or slabs.",
            "sand_ripples": "Sand or dust covers most of the ground, shaped into ripples, drifts or smooth patches.",
        },
    },
    {
        "id": "layering",
        "kind": "noul",
        "text": "Does rock in `photo` show parallel lines or bands?",
        "true": "Somewhere in the picture, a rock face or slab shows clear parallel lines or bands.",
        "false": "The rocks look solid or randomly broken, with no parallel lines or bands.",
    },
    {
        # v2: v1 asked whether "the ground in view" was steep, which left open whether that meant
        # the ground next to the rover or anything visible. v2 means anything visible, near or far.
        "id": "steep_slope",
        "kind": "noul",
        "text": "Does `photo` show a hillside, crater wall or steep bank?",
        "true": "A hillside, crater wall or steep bank fills a clear part of the picture, near or far.",
        "false": "All ground in view is flat or gently rolling.",
    },
]

# Questions answered only when ground_visible is yes; code applies the same rule to Jev's answers.
NEEDS_GROUND = {"main_terrain", "layering", "steep_slope"}


def allowed_answers(q: dict) -> set[str]:
    """Answers a person may give. 'unsure' is always allowed; Jev gives probabilities instead."""
    if q["kind"] == "noul":
        return {"yes", "no", "unsure"}
    return set(q["options"]) | {"unsure"}
