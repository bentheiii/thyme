import sys
sys.path.insert(0, ".")

from thyme.timeline import Event, State


foo = State()
qux = State()

Event(10, "Start something", foo.begin())
Event(13, "Begin something else", qux.begin())
Event(20, "Set value", foo << 42)
Event(22, "Set value of child", foo.bar << "hello")
Event(23, "Set value of sibling", qux << 3.14)
Event(25, "Set value again", foo << 100)
Event(30, "End something", foo.end())
Event(35, "End something else", qux.end())

def report_timeline(s: State):
    events = list(s._events)
    def collect_from_children(child: State):
        for ev, _ in child._events:
            val = s.at(ev.point)
            events.append((ev, val))
        for grandchild in child._children.values():
            collect_from_children(grandchild)
    for child in s._children.values():
        collect_from_children(child)
    events.sort(key=lambda x: x[0].point)
    for ev, val in events:
        print(f"{ev.point}: {ev.description} ({val})")

report_timeline(foo)