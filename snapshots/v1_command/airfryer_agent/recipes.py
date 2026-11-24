"""Dish profiles for the air fryer simulator."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Recipe:
    name: str
    label: str
    preheat_temp_c: int
    preheat_min: float
    cook_temp_c: int
    cook_min: float
    # Minutes of cooking before the turn/shake stop. None = no turn step.
    turn_after_min: float | None
    load: str
    notes: str = ""


RECIPES: dict[str, Recipe] = {
    "french_fries": Recipe(
        name="french_fries",
        label="French Fries",
        preheat_temp_c=200,
        preheat_min=3,
        cook_temp_c=200,
        cook_min=15,
        turn_after_min=8,
        load="fries basket",
        notes="Shake basket well at the turn stop.",
    ),
    "chicken_wings": Recipe(
        name="chicken_wings",
        label="Chicken Wings",
        preheat_temp_c=200,
        preheat_min=3,
        cook_temp_c=190,
        cook_min=20,
        turn_after_min=10,
        load="chicken wings",
        notes="Flip each wing at the turn stop.",
    ),
    "salmon_fillet": Recipe(
        name="salmon_fillet",
        label="Salmon Fillet",
        preheat_temp_c=180,
        preheat_min=2,
        cook_temp_c=180,
        cook_min=8,
        turn_after_min=None,
        load="salmon fillets",
        notes="No turn needed; fish stays skin-side down.",
    ),
    "veggie_mix": Recipe(
        name="veggie_mix",
        label="Veggie Mix",
        preheat_temp_c=190,
        preheat_min=2,
        cook_temp_c=190,
        cook_min=10,
        turn_after_min=5,
        load="mixed vegetables",
        notes="Toss vegetables at the turn stop.",
    ),
    "frozen_nuggets": Recipe(
        name="frozen_nuggets",
        label="Frozen Nuggets",
        preheat_temp_c=200,
        preheat_min=3,
        cook_temp_c=200,
        cook_min=12,
        turn_after_min=6,
        load="frozen nuggets",
        notes="Flip nuggets at the turn stop.",
    ),
}


def get_recipe(name: str) -> Recipe:
    key = name.strip().lower()
    if key not in RECIPES:
        valid = ", ".join(sorted(RECIPES))
        raise KeyError(f"unknown dish {name!r}; choose one of: {valid}")
    return RECIPES[key]


def list_recipes() -> list[Recipe]:
    return [RECIPES[k] for k in sorted(RECIPES)]
