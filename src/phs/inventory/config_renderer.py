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

    def _render(
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

    def render_host(
        self,
        model: HostConfig,
        *,
        host: HostConfig,
        facts: Facts,
    ) -> HostConfig:
        return self._render(
            model,
            host=host,
            facts=facts,
        )

    def render_recipe(
        self,
        recipe: Recipe,
        invocation: RecipeInvocation,
        *,
        host: HostConfig,
        facts: Facts,
    ) -> Recipe:
        variables = recipe.variables(invocation.variables)

        rendered_vars = self._render(
            variables,
            host=host,
            facts=facts,
            recipe=variables,
        )

        rendered_tasks = self._render(
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
            data = {
                field_name: self.render(field_value)
                for field_name, field_value in value.__dict__.items()
            }

            return value.model_copy(update=data)

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
            raise TypeError(name)

        return self.context.resolve(
            value,
            f"{self.path}.{name}",
        )

    def __getitem__(self, name: str) -> Any:
        return self.__getattr__(name)
