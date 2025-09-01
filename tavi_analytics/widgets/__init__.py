"""
通用UI组件模块

提供可在多个模块间复用的UI组件。
"""

from .phase_selection_widget import PhaseSelectionWidget
from .compact_phase_toggle import CompactPhaseToggle
from .key_view_manager_widget import KeyViewManagerWidget, create_key_view_manager
from .section_card import SectionCard
from .valve_overlay_widget import ValveOverlayWidget, create_valve_overlay_widget

__all__ = [
    'PhaseSelectionWidget',
    'CompactPhaseToggle', 
    'KeyViewManagerWidget',
    'create_key_view_manager',
    'SectionCard',
    'ValveOverlayWidget',
    'create_valve_overlay_widget'
]
