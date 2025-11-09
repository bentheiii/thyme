from __future__ import annotations
from abc import ABC, abstractmethod
from bisect import bisect
from typing import Any
from weakref import ReferenceType, ref

class Event[P: int]:
    def __init__(self, point: P, description: str, *extras: _Outcome[P, Any] | State[P, Any]) -> None:
        self.point = point
        self.description = description
        self.pertains_to = []
        outcomes = []
        for extra in extras:
            if isinstance(extra, _Outcome):
                outcomes.append(extra)
                s = extra.pertains_to()
            else:
                s = extra
            while s:
                self.pertains_to.append(s)
                s = s._parent() if s._parent else None
        for outcome in outcomes:
            outcome.on_assign(self)


class _Outcome[P: int, T](ABC):
    def __init__(self, state: State[P, T]) -> None:
        self.state = state
    def pertains_to(self) -> State[P, T]:
        return self.state
    @abstractmethod
    def on_assign(self, point: P) -> None:
        pass

class _Set[P: int, T](_Outcome[P, T]):
    def __init__(self, state: State[P, T], value: T) -> None:
        super().__init__(state)
        self.value = value

    def on_assign(self, ev: Event[P]) -> None:
        self.state._set(ev, self.value)

class _Begin[P, T](_Outcome[P, T]):
    def on_assign(self, ev: Event[P]) -> None:
        self.state._begin(ev)
        self.state._set(ev, None)

class _End[P, T](_Outcome[P, T]):
    def on_assign(self, ev: Event[P]) -> None:
        self.state._end(ev)
        self.state._set(ev, None)

class State[P: int, T]:
    def __init__(self, parent: State[P, Any] | None = None) -> None:
        self._parent: ReferenceType[State[P, Any]] | None = ref(parent) if parent else None
        self._boundaries: tuple[Event[P] | None, Event[P] | None] | None = None
        self._events: list[tuple[Event[P], T]] = []
        self._children: dict[str, State[P, Any]] = {}

    def boundaries(self) -> tuple[P | None, P | None]:
        if self._boundaries is None:
            if self._parent:
                return self._parent.boundaries()
            return (None, None)
        return self._boundaries
    
    def at(self, point: P) -> T:
        idx = bisect(self._events, point, key=lambda x: x[0].point)
        if idx == 0:
            return None
        return self._events[idx-1][1]
    
    def __lshift__(self, other: T) -> _Set[P, T]:
        return _Set(self, other)
    
    def begin(self) -> _Begin[P, T]:
        return _Begin(self)
    
    def end(self) -> _End[P, T]:
        return _End(self)

    def __getattr__(self, name: str) -> State[P, Any]:
        if name not in self._children:
            self._children[name] = State(self)
        return self._children[name]
        
    def _set(self, ev: Event[P], value: T) -> None:
        # we expect events to be inserted in chronological order
        self._events.append((ev, value))
        self._events.sort(key=lambda x: x[0].point)

    def _begin(self, ev: Event[P]) -> None:
        end = self._boundaries[1] if self._boundaries else None
        self._boundaries = (ev, end)

    def _end(self, ev: Event[P]) -> None:
        start = self._boundaries[0] if self._boundaries else None
        self._boundaries = (start, ev)