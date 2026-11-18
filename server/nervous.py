"""Declare actual sensor transport actions into the capability graph."""


def install_nervous(runtime):
    runtime.add("nervous.stats", "Статус нервной шины", "mikoshi.nervous", [],
                 lambda a: runtime.bus.stats())
    runtime.add("nervous.read", "Читать нервные события", "mikoshi.nervous",
                 [], lambda a: runtime.bus.read(a.get("after", 0), a.get("limit", 100)))
    runtime.add("nervous.publish", "Послать сенсорное событие", "mikoshi.nervous",
                 [{"name": "source", "type": "text"},
                  {"name": "topic", "type": "text"},
                  {"name": "source_sequence", "type": "number"},
                  {"name": "at_ns", "type": "number"},
                  {"name": "clock_domain", "type": "text"},
                  {"name": "payload", "type": "json"}],
                 lambda a: runtime.bus.publish(a.get("source"), a.get("topic"),
                    a.get("source_sequence"), a.get("at_ns"), a.get("payload", {}),
                    a.get("clock_domain")))

