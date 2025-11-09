from __future__ import annotations
from abc import ABC, abstractmethod
from bisect import bisect
from collections.abc import Collection
from typing import Any
from weakref import ReferenceType, ref

from varname import varname

class Event[P: int]:
    def __init__(self, point: P, description: str, *extras: _Outcome[P, Any] | Subject[P, Any]) -> None:
        self.point = point
        self.description = description
        outcomes = []
        for extra in extras:
            if isinstance(extra, _Outcome):
                outcomes.append(extra)
                s = extra.pertains_to()
            else:
                s = extra
            outcomes.extend([_Pertains(s) for s in s.ancestors()])
        for outcome in outcomes:
            outcome.on_assign(self)


class _Outcome[P: int, T](ABC):
    def __init__(self, state: Subject[P, T]) -> None:
        self.state = state
    def pertains_to(self) -> Subject[P, T]:
        return self.state
    @abstractmethod
    def on_assign(self, point: P) -> None:
        pass

class _Set[P: int, T](_Outcome[P, T]):
    def __init__(self, state: Subject[P, T], value: T) -> None:
        super().__init__(state)
        self.value = value

    def on_assign(self, ev: Event[P]) -> None:
        self.state._set(ev, self.value)

class _Pertains[P, T](_Outcome[P, T]):
    def on_assign(self, ev: Event[P]) -> None:
        self.state._set_pertains(ev)

hollow_value = object()

class Subject[P: int, T]:
    def __init__(self, name: str = ..., *, parents: Collection[Subject[P, Any]] = (), default: T | None = None, **kwargs) -> None:
        if name is ...:
            name = varname().replace("_", " ").title()
        self._name = name

        self._parents: tuple[ReferenceType[Subject[P, Any]], ...] = tuple(ref(parent) for parent in parents)
        self._events: list[tuple[Event[P], T]] = []
        self._children: dict[str, Subject[P, Any]] = {}
        self._default = default

        for key, value in kwargs.items():
            self.make_child(key, value)
    
    def name(self) -> str:
        return self._name
    
    def at(self, point: P) -> T:
        idx = bisect(self._events, point, key=lambda x: x[0].point)
        while True:
            if idx == 0:
                return self._default
            v = self._events[idx-1][1]
            if v is hollow_value:
                idx -= 1
                continue
            return v
    
    def __lshift__(self, other: T) -> _Set[P, T]:
        return _Set(self, other)
    
    def begin(self, value: T = True) -> _Set[P, T]:
        return self << value
    
    def end(self, value: T = False) -> _Set[P, T]:
        return self << value
    
    def make_child(self, name: str, default: Any) -> Subject[P, Any]:
        child = Subject(name=f"{self.name()}.{name}", parents=[self], default=default)
        self._children[name] = child
        return child

    def __getattr__(self, name: str) -> Subject[P, Any]:
        if name not in self._children:
            self.make_child(name, None)
        return self._children[name]
    
    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            child = self.__getattr__(name)
            child._default = value
        
    def _set(self, ev: Event[P], value: T) -> None:
        # we expect events to be inserted in chronological order
        self._events.append((ev, value))
        self._events.sort(key=lambda x: x[0].point)

    def _set_pertains(self, ev: Event[P])->None:
        self._events.append((ev, hollow_value))

    def ancestors(self) -> Collection[Subject[P, Any]]:
        result = set()
        def collect(s: Subject[P, Any]):
            result.add(s)
            for parent_ref in s._parents:
                parent = parent_ref()
                if parent and parent not in result:
                    collect(parent)
        collect(self)
        return result