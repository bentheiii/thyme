from thyme.timeline import State


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
    prev = None
    for ev, val in events:
        if prev is not None:
            delta = ev.point - prev.point
            print(f"... {delta} later")
        if val is not None:
            v = f" ({val})"
        else:
            v = ""
        print(f"{ev.point}: {ev.description}{v}")
        prev = ev