from dataclasses import dataclass
from pathlib import Path

from phs.execution.factory import ConnectionFactory
from phs.inventory.config import HostConfig, load_host
from phs.inventory.config_renderer import TemplateRenderer
from phs.inventory.facts import Facts, collect_facts
from phs.inventory.recipe import Recipe, RecipeCollection, load_recipes
from phs.settings import Settings


@dataclass
class Inventory:
    host: HostConfig
    recipes: dict[str, Recipe]
    facts: Facts


class InventoryLoader:
    def __init__(self, config_path: Path, settings: Settings):
        self.config_path = config_path
        self.settings = settings

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
        target = ConnectionFactory(host_file.host, self.settings).ssh()
        facts = collect_facts(target)

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
            facts=facts,
        )
