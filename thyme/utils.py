from thyme.timeline import Subject


def report_timeline(s: Subject):
    events = set()
    def collect_from_children(child: Subject):
        for ev, _ in child._events:
            events.add(ev)
        for grandchild in child._children.values():
            collect_from_children(grandchild)
    collect_from_children(s)
    events = sorted(events, key=lambda x: x.point)
    prev = None
    for ev in events:
        val = s.at(ev.point)
        if prev is not None:
            delta = ev.point - prev.point
            print(f"... {delta} later")
        if val is not None:
            v = f" ({val})"
        else:
            v = ""
        print(f"{ev.point}: {ev.description}{v}")
        prev = ev