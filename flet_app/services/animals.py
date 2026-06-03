from __future__ import annotations

from pokedex_manager import _DEFAULT_ANIMALS, load_animals_db_dynamic


def get_animal_data(name: str) -> dict | None:
    animals_db = load_animals_db_dynamic()
    return animals_db.get(name) or _DEFAULT_ANIMALS.get(name)
