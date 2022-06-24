"""
Provides methods for performing dynamic dispatch for actions on base type to one of its
subtypes.

Example:

```python
@register_base_type
class Base:
    @classmethod
    def __dispatch_key__(cls):
        return cls.__name__.lower()

@register_type
class Foo(Base):
    ...

key = get_dispatch_key(Foo)  # 'foo'
lookup_type(Base, key) # Foo
```
"""
from typing import Any, Dict, Optional, Type, TypeVar

T = TypeVar("T", bound=Type)

_TYPE_REGISTRIES: Dict[Type, Dict[str, Type]] = {}


def get_registry_for_type(cls: T) -> Optional[Dict[str, T]]:
    """
    Get the first matching registry for a class or any of its base classes.

    If not found, `None` is returned.
    """
    return next(
        filter(
            lambda registry: registry is not None,
            (_TYPE_REGISTRIES.get(cls) for cls in cls.mro()),
        ),
        None,
    )


def get_dispatch_key(
    cls_or_instance: Any, allow_missing: bool = False
) -> Optional[str]:
    """
    Retrieve the unique dispatch key for a class type or instance.

    This key is defined at the `__dispatch_key__` attribute. If it is a callable, it
    will be resolved.

    If `allow_missing` is `False`, an exception will be raised if the attribute is not
    defined or the key is null. If `True`, `None` will be returned in these cases.
    """
    dispatch_key = getattr(cls_or_instance, "__dispatch_key__", None)

    type_name = (
        cls_or_instance.__name__
        if isinstance(cls_or_instance, type)
        else type(cls_or_instance).__name__
    )

    if dispatch_key is None:
        if allow_missing:
            return None
        raise ValueError(
            f"Type {type_name!r} does not define a value for "
            "'__dispatch_key__' which is required for registry lookup."
        )

    if callable(dispatch_key):
        dispatch_key = dispatch_key()

    if allow_missing and dispatch_key is None:
        return None

    if not isinstance(dispatch_key, str):
        raise TypeError(
            f"Type {type_name!r} has a '__dispatch_key__' of type "
            f"{type(dispatch_key).__name__} but a type of 'str' is required."
        )

    return dispatch_key


def register_base_type(cls: T) -> T:
    """
    Register a base type allowing child types to be registered for dispatch with
    `register_type`.

    The base class may or may not define a `__dispatch_key__` to allow lookups of the
    base type.
    """
    registry = _TYPE_REGISTRIES.setdefault(cls, {})
    base_key = get_dispatch_key(cls, allow_missing=True)
    if base_key is not None:
        registry[base_key] = cls
    return cls


def register_type(cls: T) -> T:
    """
    Register a type for lookup with dispatch.

    The type or one of its parents must define a unique `__dispatch_key__`.

    One of the classes base types must be registered using `register_base_type`.
    """
    # Lookup the registry for this type
    registry = get_registry_for_type(cls)

    # Check if a base type is registered
    if registry is None:
        raise ValueError(
            f"No registry found for type {cls.__name__!r} with " f"bases {cls.mro()!r}."
        )

    # Add to the registry
    registry[get_dispatch_key(cls)] = cls

    return cls


def lookup_type(cls: T, dispatch_key: str) -> T:
    """
    Look up a dispatch key in the type registry for the given class.
    """
    # Get the first matching registry for the class or one of its bases
    registry = get_registry_for_type(cls)

    # Look up this type in the registry
    subcls = registry.get(dispatch_key)

    if subcls is None:
        raise KeyError(f"No class found in registry for dispatch key {dispatch_key!r}.")

    return subcls
