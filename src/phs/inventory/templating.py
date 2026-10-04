from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from jinja2 import StrictUndefined
from jinja2.nativetypes import NativeEnvironment
from pydantic import BaseModel

from phs.inventory.config import HostConfig
from phs.inventory.facts import Facts
from phs.inventory.recipe import Recipe, RecipeInvocation


class TemplateError(ValueError):
    pass


class TemplateRenderer:
    def __init__(self) -> None:
        self.environment = NativeEnvironment(
            undefined=StrictUndefined,
            autoescape=False,
        )

    def render(
        self,
        value: Any,
        *,
        host: Any,
        facts: Any,
        recipe: Any = None,
    ) -> Any:
        context = _RenderContext(
            renderer=self,
            values={
                "host": host,
                "facts": facts,
                "recipe": recipe or {},
            },
        )

        return context.render(value)

    def render_model(
        self,
        model: BaseModel,
        *,
        host: Any,
        facts: Any,
        recipe: Any = None,
    ) -> BaseModel:
        return self.render(
            model,
            host=host,
            facts=facts,
            recipe=recipe,
        )


class _RenderContext:
    def __init__(
        self,
        *,
        renderer: TemplateRenderer,
        values: dict[str, Any],
        resolving: tuple[str, ...] = (),
    ) -> None:
        self.renderer = renderer
        self.values = values
        self.resolving = resolving

    def template_context(self) -> dict[str, Any]:
        return {
            name: _TemplateValue(
                context=self,
                value=value,
                path=name,
            )
            for name, value in self.values.items()
        }

    def render(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.render_string(value)

        if isinstance(value, BaseModel):
            data = {key: self.render(item) for key, item in value.model_dump().items()}

            return value.__class__.model_validate(data)

        if isinstance(value, list):
            return [self.render(item) for item in value]

        if isinstance(value, dict):
            return {key: self.render(item) for key, item in value.items()}

        return value

    def render_string(self, value: str) -> Any:
        try:
            template = self.renderer.environment.from_string(value)
            return template.render(self.template_context())
        except Exception as exc:
            raise TemplateError(f"Failed to render template {value!r}") from exc

    def resolve(
        self,
        value: Any,
        path: str,
    ) -> Any:
        if path in self.resolving:
            chain = " -> ".join((*self.resolving, path))
            raise TemplateError(f"Circular template reference: {chain}")

        context = _RenderContext(
            renderer=self.renderer,
            values=self.values,
            resolving=(*self.resolving, path),
        )

        return context.render(value)


class _TemplateValue:
    def __init__(
        self,
        *,
        context: _RenderContext,
        value: Any,
        path: str,
    ) -> None:
        self.context = context
        self.value = value
        self.path = path

    def __getattr__(self, name: str) -> Any:
        if isinstance(self.value, BaseModel):
            value = getattr(self.value, name)

        elif isinstance(self.value, Mapping):
            try:
                value = self.value[name]
            except KeyError:
                raise AttributeError(name) from None

        else:
            raise AttributeError(name)

        return self.context.resolve(
            value,
            f"{self.path}.{name}",
        )

    def __getitem__(self, name: str) -> Any:
        return self.__getattr__(name)


def render_recipe(
    recipe: Recipe,
    invocation: RecipeInvocation,
    renderer: TemplateRenderer,
    *,
    host: HostConfig,
    facts: Facts,
) -> Recipe:
    variables = recipe.variables(invocation.variables)

    rendered_vars = renderer.render(
        variables,
        host=host,
        facts=facts,
        recipe=variables,
    )

    rendered_tasks = renderer.render(
        recipe.tasks,
        host=host,
        facts=facts,
        recipe=rendered_vars,
    )

    return recipe.model_copy(
        update={
            "vars": rendered_vars,
            "tasks": rendered_tasks,
        }
    )
