"""
Save/load proiect — fisiere JSON (cf. arhitectura: NU SQL, fisiere portabile).

Format:
{
  "format_version": 1,
  "app": "Simulator circuite electrice",
  "components": [
    {"id": "R1", "type": "resistor", "x": 120.0, "y": 80.0, "params": {...}}
  ],
  "wires": [
    {"from": ["R1", "A"], "to": ["V1", "+"]}
  ]
}
"""

import json
from typing import Any, Dict


FORMAT_VERSION = 1


def project_to_dict(scene) -> Dict[str, Any]:
    """Serializeaza scena curenta intr-un dict JSON-safe."""
    from src.components.component_item import ComponentItem
    from src.components.wire import Wire

    components = []
    pin_map: Dict[int, tuple] = {}    # id(pin) -> (uid, pin_name) — pentru fire

    for it in scene.items():
        if isinstance(it, ComponentItem):
            comp_dict = {
                "id": it.uid,
                "type": it.data.get("type") or it.data.get("name"),
                "x": float(it.x()),
                "y": float(it.y()),
                "params": _serializable(it.properties),
            }
            components.append(comp_dict)
            for pin in it.pins:
                pin_map[id(pin)] = (it.uid, pin.node_name)

    wires = []
    for it in scene.items():
        if isinstance(it, Wire):
            k1 = pin_map.get(id(it.pin1))
            k2 = pin_map.get(id(it.pin2))
            if k1 and k2:
                wires.append({"from": list(k1), "to": list(k2)})

    return {
        "format_version": FORMAT_VERSION,
        "app": "Simulator circuite electrice",
        "components": components,
        "wires": wires,
    }


def dict_to_project(data: Dict[str, Any], scene) -> None:
    """Reconstruieste scena dintr-un dict produs de `project_to_dict`."""
    from src.components.component_factory import create_component
    from src.components.component_item import ComponentItem
    from src.components.wire import Wire

    # curata scena
    scene.clear()
    scene.wires = []
    ComponentItem.reset_id_counters()

    if data.get("format_version", 0) > FORMAT_VERSION:
        raise ValueError(f"Format necunoscut: v{data.get('format_version')}.")

    # creare componente
    comp_by_uid = {}
    for cdata in data.get("components", []):
        comp = create_component(cdata["type"], comp_id=cdata["id"])
        comp.setPos(float(cdata.get("x", 0)), float(cdata.get("y", 0)))
        # actualizeaza parametrii
        for k, v in (cdata.get("params") or {}).items():
            comp.set_property(k, v)
        comp.update_label()
        scene.addItem(comp)
        comp_by_uid[comp.uid] = comp
        # actualizeaza contoarul global dupa cel mai mare numar gasit
        digits = "".join(ch for ch in comp.uid if ch.isdigit())
        if digits:
            ComponentItem.bump_counter_to(comp.kind, int(digits))

    # creare fire
    for wdata in data.get("wires", []):
        f_uid, f_pin = wdata["from"]
        t_uid, t_pin = wdata["to"]
        cf = comp_by_uid.get(f_uid)
        ct = comp_by_uid.get(t_uid)
        if not cf or not ct:
            continue
        pin1 = next((p for p in cf.pins if p.node_name == f_pin), None)
        pin2 = next((p for p in ct.pins if p.node_name == t_pin), None)
        if pin1 and pin2:
            wire = Wire(pin1, pin2)
            scene.addItem(wire)
            scene.wires.append(wire)


def save_project(path: str, scene) -> None:
    data = project_to_dict(scene)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_project(path: str, scene) -> None:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    dict_to_project(data, scene)


def _serializable(d):
    """Asigura ca toate valorile sunt JSON-safe."""
    out = {}
    for k, v in d.items():
        if isinstance(v, (int, float, str, bool)) or v is None:
            out[k] = v
        else:
            out[k] = str(v)
    return out
