from dataclasses import dataclass
from pathlib import Path

from phs.inventory.config import HostConfig, load_host
from phs.inventory.config_renderer import TemplateRenderer
from phs.inventory.facts import Facts, OsFacts
from phs.inventory.recipe import Recipe, RecipeCollection, load_recipes


@dataclass
class Inventory:
    host: HostConfig
    recipes: dict[str, Recipe]


class InventoryLoader:
    def __init__(self, config_path: Path):
        self.config_path = config_path

    def load(self, hostname: str) -> Inventory:
        host_filename = self.config_path / "hosts" / f"{hostname}.yaml"
        if not host_filename.exists():
            raise FileNotFoundError(f"No such hostfile: {host_filename}")

        recipes_dir = self.config_path / "recipes"
        host_file = load_host(host_filename)
        recipe_collection = load_recipes(
            [p for p in recipes_dir.glob("*.yaml") if p.is_file()]
        )
        recipe_collection = recipe_collection.merge(
            RecipeCollection(recipes=host_file.recipes)
        )
        facts = Facts(os=OsFacts(id="arch", version="rolling"))

        renderer = TemplateRenderer()

        return Inventory(
            host=renderer.render_host(
                host_file.host,
                host=host_file.host,
                facts=facts,
            ),
            recipes={
                invocation.name: renderer.render_recipe(
                    recipe_collection.recipes[invocation.name],
                    invocation,
                    host=host_file.host,
                    facts=facts,
                )
                for invocation in host_file.host.recipes
            },
        )
