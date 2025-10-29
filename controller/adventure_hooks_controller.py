import random
from typing import Optional, List, Dict, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem

from model.sectors_db import SectorDB
from model.planets_db import PlanetDB
from model.adventure_hooks_db import AdventureHooksDB
from utils.adventure_generator import AdventureGenerator, generate_adventure_story
from utils.map_renderer import parse_uwp, ATMOSPHERE_CLASSES
from view.adventure_hooks_view import AdventureHooksView


class AdventureHooksController:
    def __init__(self, db_instance):
        self.db = db_instance
        self.view: Optional[AdventureHooksView] = None
        self.sector_db = SectorDB(db_instance)
        self.planet_db = PlanetDB(db_instance)
        self.generator = AdventureGenerator()
        self.hooks_db = AdventureHooksDB(db_instance)
        self.current_hook_id: Optional[int] = None
        self.last_outline: Optional[List[Tuple[str, object]]] = None
        self.last_world_info: Optional[Dict[str, object]] = None

    def show_view(self, display_widget):
        view = self._ensure_view()

        if hasattr(display_widget, "setWidget"):
            display_widget.setWidget(view)
        elif hasattr(display_widget, "layout"):
            display_widget.setLayout(view.layout())
        else:
            display_widget.setText("Adventure hook view requires a widget container.")

    def get_view(self) -> AdventureHooksView:
        return self._ensure_view()

    def _ensure_view(self) -> AdventureHooksView:
        if not self.view:
            self.view = AdventureHooksView()
            self._populate_sectors()
            self.view.sector_combo.currentIndexChanged.connect(self._on_sector_changed)
            self.view.system_combo.currentIndexChanged.connect(self._on_system_changed)
            self.view.generate_button.clicked.connect(self._generate_hook)
            self.view.enhance_button.clicked.connect(self._enhance_with_chatgpt)
            self.view.save_button.clicked.connect(self._save_hook)
            self.view.delete_button.clicked.connect(self._delete_hook)
            self.view.saved_hooks_list.itemSelectionChanged.connect(self._on_saved_hook_selected)
            self._refresh_saved_hooks()
            self.view.delete_button.setEnabled(False)
        return self.view

    # ------------------------------------------------------------------
    # Population helpers
    # ------------------------------------------------------------------

    def _populate_sectors(self) -> None:
        records = self.sector_db.list_sector_records()
        combo = self.view.sector_combo
        combo.blockSignals(True)
        for sector_id, name, abbr in records:
            label = f"{name} ({abbr})" if abbr else name
            combo.addItem(label, userData={"id": sector_id, "name": name, "abbr": abbr})
        combo.blockSignals(False)

    def _on_sector_changed(self) -> None:
        combo = self.view.sector_combo
        sector_info = combo.currentData()
        sector_id = sector_info.get("id") if isinstance(sector_info, dict) else None
        sector_name = sector_info.get("name") if isinstance(sector_info, dict) else None
        system_combo = self.view.system_combo
        system_combo.blockSignals(True)
        system_combo.clear()
        system_combo.addItem("Any System", userData=None)

        planet_combo = self.view.planet_combo
        planet_combo.blockSignals(True)
        planet_combo.clear()
        planet_combo.addItem("Any World", userData=None)

        if sector_id is not None:
            planets = self.planet_db.db.read_records("planets", {"sector_id": sector_id})
            columns = self.planet_db.db.get_table_columns("planets")
            name_idx = columns.index("name") if "name" in columns else 0
            hex_idx = columns.index("hex") if "hex" in columns else None
            planet_id_idx = columns.index("planet_id") if "planet_id" in columns else None

            seen_hex = set()
            for row in planets:
                system_hex_val = str(row[hex_idx]) if hex_idx is not None and row[hex_idx] else None
                if system_hex_val and system_hex_val not in seen_hex:
                    system_combo.addItem(system_hex_val, userData={"hex": system_hex_val, "sector_id": sector_id})
                    seen_hex.add(system_hex_val)
                planet_name = str(row[name_idx])
                planet_id_val = row[planet_id_idx] if planet_id_idx is not None else None
                planet_combo.addItem(
                    planet_name,
                    userData={
                        "name": planet_name,
                        "hex": system_hex_val,
                        "sector_id": sector_id,
                        "planet_id": planet_id_val,
                    },
                )

        system_combo.blockSignals(False)
        planet_combo.blockSignals(False)

    def _on_system_changed(self) -> None:
        sector_info = self.view.sector_combo.currentData()
        sector_id = sector_info.get("id") if isinstance(sector_info, dict) else None
        sector_name = sector_info.get("name") if isinstance(sector_info, dict) else None
        system_info = self.view.system_combo.currentData()
        system_hex = system_info.get("hex") if isinstance(system_info, dict) else system_info
        planet_combo = self.view.planet_combo
        planet_combo.blockSignals(True)
        planet_combo.clear()
        planet_combo.addItem("Any World", userData=None)

        if sector_id is not None and system_hex:
            planets = self.planet_db.db.read_records("planets", {"sector_id": sector_id, "hex": system_hex})
            columns = self.planet_db.db.get_table_columns("planets")
            name_idx = columns.index("name") if "name" in columns else 0
            planet_id_idx = columns.index("planet_id") if "planet_id" in columns else None
            for row in planets:
                planet_name = str(row[name_idx])
                planet_id_val = row[planet_id_idx] if planet_id_idx is not None else None
                planet_combo.addItem(
                    planet_name,
                    userData={
                        "name": planet_name,
                        "hex": system_hex,
                        "sector_id": sector_id,
                        "planet_id": planet_id_val,
                    },
                )
        elif sector_id is not None:
            planets = self.planet_db.db.read_records("planets", {"sector_id": sector_id})
            columns = self.planet_db.db.get_table_columns("planets")
            name_idx = columns.index("name") if "name" in columns else 0
            hex_idx = columns.index("hex") if "hex" in columns else None
            planet_id_idx = columns.index("planet_id") if "planet_id" in columns else None
            for row in planets:
                planet_name = str(row[name_idx])
                system_hex_val = str(row[hex_idx]) if hex_idx is not None and row[hex_idx] else None
                planet_id_val = row[planet_id_idx] if planet_id_idx is not None else None
                planet_combo.addItem(
                    planet_name,
                    userData={
                        "name": planet_name,
                        "hex": system_hex_val,
                        "sector_id": sector_id,
                        "planet_id": planet_id_val,
                    },
                )

        planet_combo.blockSignals(False)

    # ------------------------------------------------------------------
    # Adventure generation
    # ------------------------------------------------------------------

    def _generate_hook(self) -> None:
        rng = random.Random()
        outline = self.generator.generate(rng)

        context_lines, world_info = self._build_context()
        title, text = generate_adventure_story(outline, world_info=world_info, context_lines=context_lines, rng=rng)
        self.current_hook_id = None
        self.view.saved_hooks_list.clearSelection()
        self.view.delete_button.setEnabled(False)
        self.view.title_edit.setText(title)
        self.view.output.setPlainText(text)
        self.last_outline = outline
        self.last_world_info = world_info

    def _build_context(self) -> Tuple[Optional[List[str]], Dict[str, object]]:
        context: List[str] = []
        world_info: Dict[str, object] = {}

        sector_data = self.view.sector_combo.currentData()
        sector_id = None
        sector_name = None
        if isinstance(sector_data, dict):
            sector_id = sector_data.get("id")
            sector_name = sector_data.get("name")
        elif sector_data:
            sector_name = sector_data

        system_data = self.view.system_combo.currentData()
        system_hex = None
        if isinstance(system_data, dict):
            system_hex = system_data.get("hex")
        elif system_data:
            system_hex = system_data

        planet_data = self.view.planet_combo.currentData()

        if sector_name:
            context.append(f"Sector: {sector_name}")
            world_info["sector_name"] = sector_name
        if system_hex:
            context.append(f"System Hex: {system_hex}")
            world_info["system_hex"] = system_hex

        planet_summary: Dict[str, object] = {}
        if isinstance(planet_data, dict):
            planet_name = planet_data.get("name")
            planet_hex = planet_data.get("hex")
            planet_sector_id = planet_data.get("sector_id", sector_id)
            planet_id = planet_data.get("planet_id")
            if planet_name:
                context.append(f"Planet: {planet_name}")
                planet_summary["name"] = planet_name
            if planet_hex:
                context.append(f"Planet Hex: {planet_hex}")
                planet_summary["hex"] = planet_hex
            planet_details = None
            if planet_id:
                planet_details = self.planet_db.get_planet_by_id(planet_id)
            if not planet_details and planet_name:
                planet_details = self.planet_db.get_planet_details(planet_name, planet_sector_id)
            if planet_details:
                uwp = planet_details.get("UWP") or planet_details.get("uwp")
                planet_summary["details"] = planet_details
                planet_summary["uwp"] = uwp
                planet_summary["planet_id"] = planet_details.get("planet_id")
                if uwp:
                    try:
                        parsed = parse_uwp(str(uwp))
                        planet_summary["parsed_uwp"] = parsed
                        atmo = ATMOSPHERE_CLASSES.get(parsed["atmosphere"], "Unknown atmosphere")
                        context.append(f"UWP: {uwp} ({atmo})")
                    except ValueError:
                        context.append(f"UWP: {uwp}")
            world_info["planet"] = planet_summary

        if sector_id is not None:
            world_info["sector_id"] = sector_id

        return (context if context else None), world_info

    def _enhance_with_chatgpt(self) -> None:
        if not self.last_outline:
            self.view.output.append("\n[Generate an adventure before enhancing with ChatGPT.]")
            return

        try:
            from utils.openai_client import ChatGPTAdventureWriter, OpenAIConfigurationError
        except ImportError:
            self.view.output.append("\n[ChatGPT integration is unavailable. Install the 'openai' package to enable this feature.]")
            return

        try:
            writer = ChatGPTAdventureWriter()
        except OpenAIConfigurationError as exc:
            self.view.output.append(f"\n[{exc}]")
            return
        except Exception as exc:  # pragma: no cover - unexpected runtime failure
            self.view.output.append(f"\n[Failed to initialise ChatGPT client: {exc}]")
            return

        try:
            title, enhanced_text = writer.enhance(
                self.last_outline,
                self.last_world_info,
                self.view.output.toPlainText(),
            )
        except Exception as exc:
            self.view.output.append(f"\n[ChatGPT request failed: {exc}]")
            return

        if title:
            self.view.title_edit.setText(title)
        self.view.output.setPlainText(enhanced_text)
    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save_hook(self) -> None:
        title = self.view.title_edit.text().strip() or "Untitled Adventure"
        description = self.view.output.toPlainText().strip()
        planet_data = self.view.planet_combo.currentData()
        planet_id = None
        if isinstance(planet_data, dict):
            planet_id = planet_data.get("planet_id")

        if not description:
            self.view.output.append("\n[Please generate or enter an adventure before saving.]")
            return

        try:
            if self.current_hook_id is None:
                self.current_hook_id = self.hooks_db.create_hook(title, description, planet_id)
            else:
                self.hooks_db.update_hook(self.current_hook_id, title, description, planet_id)
            self._refresh_saved_hooks(select_id=self.current_hook_id)
        except RuntimeError as exc:
            self.view.output.append(f"\n[Error saving adventure: {exc}]")

    def _delete_hook(self) -> None:
        if self.current_hook_id is None:
            return
        try:
            self.hooks_db.delete_hook(self.current_hook_id)
        except RuntimeError as exc:
            self.view.output.append(f"\n[Error deleting adventure: {exc}]")
            return

        self.current_hook_id = None
        self.view.title_edit.clear()
        self.view.output.clear()
        self.view.saved_hooks_list.clearSelection()
        self.view.delete_button.setEnabled(False)
        self._refresh_saved_hooks()

    def _refresh_saved_hooks(self, select_id: Optional[int] = None) -> None:
        hooks = self.hooks_db.list_hooks()
        list_widget = self.view.saved_hooks_list
        list_widget.blockSignals(True)
        list_widget.clear()
        matched_item = None
        for hook in hooks:
            label = hook["title"] or "Untitled Adventure"
            if hook.get("planet_id"):
                label = f"{label} (Planet {hook['planet_id']})"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, hook)
            list_widget.addItem(item)
            if select_id and hook.get("hook_id") == select_id:
                matched_item = item
        list_widget.blockSignals(False)
        if matched_item:
            list_widget.setCurrentItem(matched_item)
        else:
            self.view.delete_button.setEnabled(False)

    def _on_saved_hook_selected(self) -> None:
        items = self.view.saved_hooks_list.selectedItems()
        if not items:
            self.current_hook_id = None
            self.view.delete_button.setEnabled(False)
            return

        item = items[0]
        hook = item.data(Qt.ItemDataRole.UserRole)
        if not hook:
            return

        self.current_hook_id = hook.get("hook_id")
        self.view.delete_button.setEnabled(True)
        self.view.title_edit.setText(hook.get("title") or "Untitled Adventure")
        self.view.output.setPlainText(hook.get("description") or "")

        planet_id = hook.get("planet_id")
        if planet_id:
            planet = self.planet_db.get_planet_by_id(planet_id)
            if planet:
                sector_id = planet.get("sector_id")
                system_hex = planet.get("hex")
                planet_name = planet.get("name")
                self._set_sector_selection(sector_id)
                self._set_system_selection(sector_id, system_hex)
                self._set_planet_selection(planet_id, planet_name, system_hex, sector_id)
        else:
            self.view.sector_combo.setCurrentIndex(0)
            self.view.system_combo.setCurrentIndex(0)
            self.view.planet_combo.setCurrentIndex(0)

    def _set_sector_selection(self, target_sector_id: Optional[int]) -> None:
        combo = self.view.sector_combo
        if target_sector_id is None:
            combo.setCurrentIndex(0)
            return
        for idx in range(combo.count()):
            data = combo.itemData(idx)
            if isinstance(data, dict) and data.get("id") == target_sector_id:
                combo.setCurrentIndex(idx)
                return

    def _set_system_selection(self, sector_id: Optional[int], target_hex: Optional[str]) -> None:
        if target_hex is None:
            self.view.system_combo.setCurrentIndex(0)
            return
        combo = self.view.system_combo
        for idx in range(combo.count()):
            data = combo.itemData(idx)
            if isinstance(data, dict) and data.get("hex") == target_hex:
                combo.setCurrentIndex(idx)
                return

    def _set_planet_selection(self, planet_id: Optional[int], planet_name: Optional[str], system_hex: Optional[str], sector_id: Optional[int]) -> None:
        combo = self.view.planet_combo
        if planet_id is None:
            combo.setCurrentIndex(0)
            return
        for idx in range(combo.count()):
            data = combo.itemData(idx)
            if isinstance(data, dict) and data.get("planet_id") == planet_id:
                combo.setCurrentIndex(idx)
                return
