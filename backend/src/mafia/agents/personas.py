"""Persona pool: 50 fixed characters drawn at game start."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from importlib.resources import files


@dataclass(frozen=True)
class Persona:
    id: int
    name: str
    job: str
    personality: str
    style: str


@dataclass
class PersonaPool:
    all_personas: list[Persona]

    def draw(self, n: int, rng: random.Random) -> list[Persona]:
        if n > len(self.all_personas):
            raise ValueError(f"requested {n} personas but only {len(self.all_personas)} available")
        return rng.sample(self.all_personas, n)


def load_personas() -> PersonaPool:
    """Load the bundled personas.json from the package."""
    data_path = files("mafia.agents").joinpath("personas.json")
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    personas = [Persona(**item) for item in raw]
    return PersonaPool(all_personas=personas)
