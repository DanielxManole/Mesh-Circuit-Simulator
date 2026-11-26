"""
Fabrica de componente. Singurul loc unde se citeste catalogul si se construiesc
ComponentItem — restul codului foloseste doar `create_component(type, id?)`.
"""

from .components_catalog import COMPONENTS
from .component_item import ComponentItem


def create_component(component_type, comp_id=None):
    if component_type not in COMPONENTS:
        raise ValueError(f"Componenta necunoscuta: {component_type}")
    data = COMPONENTS[component_type]
    # pastram cheia originala pentru save/load
    data_with_key = dict(data)
    data_with_key["type"] = component_type
    return ComponentItem(data_with_key, comp_id=comp_id)
