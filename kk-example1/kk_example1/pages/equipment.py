"""The equipment table page."""

from ..templates import template
from ..backend.equipment_state import EquipmentState
from ..views.equipment import main_table

import reflex as rx


@template(route="/equipment", title="Site Equipment", on_load=EquipmentState.load_entries)
def equipmentTable() -> rx.Component:
    """The table of all equipment.

    Returns:
        The UI for the table page.
    """
    return rx.vstack(
        rx.heading("Equipment", size="5"),
        main_table(),
        spacing="8",
        width="100%",
    )
