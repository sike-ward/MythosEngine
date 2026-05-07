import re
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QInputDialog,
    QMenu,
    QVBoxLayout,
)

from Ward_DND_AI.gui.browse.view_browse import (
    MetadataEditorDialog,
    VersionHistoryDialog,
)
from Ward_DND_AI.utils.crash_handler import catch_and_report_crashes
from Ward_DND_AI.utils.utils import (
    make_title_case_filename,
    read_note_metadata,
    write_note_metadata,
)

# --- Helper for timestamp formatting ---


def _format_time(ts):
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

    except Exception:
        return str(ts)


STAR_FILE = "starred.json"


class BrowseController:
    def __init__(self, view, ctx, status_var=None):
        self.v = view

        self.ctx = ctx
        self.ai = ctx.ai

        self.storage = ctx.storage

        self.config = ctx.config

        self.status_var = status_var or self.v.status_label

        self.original_content = ""

        self.v.controller = self

        self.v.notes_tree.controller = self

        self.move_undo_stack = []

        self.starred_notes = self.load_starred()  # <-- move up here!

        self._bind_events()

        self.load_folders()

        self.load_tags()

        self.load_tree()

        self.starred_notes = self.load_starred()

    def _bind_events(self):
        self.v.folder_menu.currentTextChanged.connect(catch_and_report_crashes(self.on_folder_changed))

        self.v.tag_filter.textChanged.connect(catch_and_report_crashes(self.on_tag_changed))

        self.v.import_btn.clicked.connect(catch_and_report_crashes(self.import_notes))

        self.v.export_btn.clicked.connect(catch_and_report_crashes(self.export_notes))

        self.v.delete_btn.clicked.connect(catch_and_report_crashes(self.delete_notes))

        self.v.tag_btn.clicked.connect(catch_and_report_crashes(self.tag_notes))

        self.v.move_btn.clicked.connect(catch_and_report_crashes(self.move_notes))

        self.v.edit_btn.clicked.connect(catch_and_report_crashes(self.enable_edit))

        self.v.save_btn.clicked.connect(catch_and_report_crashes(self.save_note))

        self.v.cancel_btn.clicked.connect(catch_and_report_crashes(self.cancel_edit))

        self.v.summarize_btn.clicked.connect(catch_and_report_crashes(self.open_summarize_dialog))

        self.v.notes_tree.itemClicked.connect(catch_and_report_crashes(self._on_note_item_clicked))

        self.v.notes_tree.itemDoubleClicked.connect(catch_and_report_crashes(self._on_note_item_double_clicked))

        self.v.show_source_btn.clicked.connect(catch_and_report_crashes(self.toggle_source_view))

        self.v.multi_select_cb.toggled.connect(catch_and_report_crashes(self.on_multi_select_toggled))

        self.v.notes_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.v.notes_tree.customContextMenuRequested.connect(catch_and_report_crashes(self.show_notes_context_menu))

        self.v.undo_move_btn.clicked.connect(catch_and_report_crashes(self.undo_last_move))

        self.v.star_btn.clicked.connect(catch_and_report_crashes(self.toggle_star_selected_note))

        self.v.history_btn.clicked.connect(catch_and_report_crashes(self.open_history_dialog))

        self.v.links_btn.clicked.connect(catch_and_report_crashes(self.open_links_dialog))

        self.v.metadata_btn.clicked.connect(catch_and_report_crashes(self.open_metadata_dialog))

        self.v.fav_filter_cb.toggled.connect(catch_and_report_crashes(self.load_tree))

        self.v.search_btn.clicked.connect(catch_and_report_crashes(self.search_notes))

        self.v.search_input.returnPressed.connect(catch_and_report_crashes(self.search_notes))

        self.v.clear_search_btn.clicked.connect(catch_and_report_crashes(self.load_tree))

        self.v.create_btn.clicked.connect(catch_and_report_crashes(self.new_note_from_template))

    # --- Folder, Tag, and Tree Operations ---

    def load_folders(self):
        folders = self.storage.list_folders()

        self.v.clear_folders()

        self.v.add_folders([""] + sorted(folders))

    def load_tags(self):
        tags = set()

        wikilink_pattern = re.compile(r"\[\[([^\[\]]+)\]\]")

        for note in self.storage.list_notes():
            content = self.storage.read_note(note)

            tags.update(wikilink_pattern.findall(content))

        tag_list = sorted(tags)

        self.v.tag_filter.clear()

        if hasattr(self.v, "update_tag_completer"):
            self.v.update_tag_completer(tag_list)

    def load_tree(self, *args, **kwargs):
        folders = list(self.storage.list_folders())

        notes = list(self.storage.list_notes())

        self.v.set_tree_data(
            folders,
            notes,
            self.v.get_current_folder(),
            self.v.tag_filter.text(),
            self.v.multi_select_cb.isChecked(),
        )

        if hasattr(self.v, "update_search_completer"):
            self.v.update_search_completer(self.storage.list_notes())

    def on_folder_changed(self, *_):
        self.load_tree()

    def on_tag_changed(self, *_):
        self.load_tree()

    # --- Note selection helpers (checkboxes/multi-select) ---

    def get_selected_note_name(self):
        return self.v.get_selected_note_name()

    def get_batch_selected_notes(self):
        items = self.v.notes_tree.selectedItems()

        return [item.note_path for item in items if hasattr(item, "note_path")]

    # --- Note context menu ---

    def show_notes_context_menu(self, pos):
        item = self.v.notes_tree.itemAt(pos)

        menu = QMenu(self.v.notes_tree)

        # Only show note actions if this is a note (has note_path)

        if item and hasattr(item, "note_path"):
            note = item.note_path

            open_label = self.get_open_in_label()

            menu.addAction(open_label, lambda: self.open_in_vault_for(note))

            menu.addAction("Export Note…", lambda: self.export_specific(note))

            menu.addAction("Delete Note", lambda: self.delete_specific(note))

            menu.addAction("Summarize Note", lambda: self.summarize_note(note))

            menu.addAction("Switch View (Preview/Edit)", lambda: self.toggle_note_view_for(note))  # <-- add this line!

            menu.addSeparator()

        menu.addAction("New Note", self.new_note)

        menu.addAction("Import Notes…", self.import_notes)

        menu.addAction("Tag Notes…", self.tag_notes)

        menu.addAction("Move Notes…", self.move_notes)

        menu.exec(self.v.notes_tree.viewport().mapToGlobal(pos))

        # --- Note actions ---

    def load_starred(self):
        try:
            return self.storage.read_starred()
        except Exception:
            return set()

    def save_starred(self, stars):
        try:
            self.storage.write_starred(stars)
        except Exception as e:
            print(f"Failed to save stars: {e}")

    def is_note_starred(self, note_path):
        return note_path in self.starred_notes

    def toggle_star_selected_note(self, *args, **kwargs):
        sel = self.get_selected_note_name()

        if not sel:
            self.v.show_status("No note selected to star.")

            return

        if sel in self.starred_notes:
            self.starred_notes.remove(sel)

            self.v.show_status(f"Unstarred: {sel}")

        else:
            self.starred_notes.add(sel)

            self.v.show_status(f"Starred: {sel}")

        self.save_starred(self.starred_notes)

        self.load_tree()

    def preview_note(self, note_path):
        content = ""

        if note_path:
            try:
                content = self.storage.read_note(note_path)

            except Exception as e:
                content = f"[ERROR: {e}]"

        self.original_content = content

        self.v.show_markdown_preview(note_path, content)

        # Metadata info

        if note_path:
            try:
                self.v.show_metadata(note_path)

            except Exception as e:
                self.v.metadata_label.setText(f"<b>File:</b> {note_path}<br>(metadata unavailable: {e})")

        else:
            self.v.show_metadata("")

    def open_note_by_path(self, rel_path: str):
        """Open a note directly by its vault-relative path (used by Dashboard)."""

        try:
            content = self.storage.read_note(rel_path)

            self.v.open_note_tab(rel_path, content, editable=False)

            self.preview_note(rel_path)

        except Exception as e:
            self.status_var.setText(f"Could not open note: {e}")

    def _on_note_item_clicked(self, item, column):
        if hasattr(item, "note_path"):
            # Only open a tab if NO tab is open (single select)

            if self.v.preview_tabs.count() == 0:
                note = item.note_path

                content = self.storage.read_note(note)

                self.v.open_note_tab(note, content, editable=False)

                self.preview_note(note)  # <-- only call here!

        else:
            self.v.show_metadata("")

    def _on_note_item_double_clicked(self, item, column):
        if hasattr(item, "note_path"):
            note = item.note_path

            content = self.storage.read_note(note)

            self.v.open_note_tab(note, content, editable=False)

            self.preview_note(note)  # Always show meta when opening a tab

    def enable_edit(self, *args, **kwargs):
        tab = self.v.preview_tabs.currentWidget()

        if tab and hasattr(tab, "note_name"):
            note = tab.note_name

            md = self.storage.read_note(note)

            index = self.v.preview_tabs.currentIndex()

            # Remove the preview tab (if present) before adding the split editor

            self.v.preview_tabs.removeTab(index)

            self.v.show_markdown_editor(note, md)

            self.v.enable_buttons(save=True, cancel=True, edit=False)

            self.v.show_status("Editing…")

            self.v.show_source_btn.setVisible(False)

    def cancel_edit(self, *args, **kwargs):
        editor = self.v.preview_tabs.currentWidget()

        if editor and hasattr(editor, "note_name"):
            note = editor.note_name

            md = self.storage.read_note(note)

            # Remove current tab and replace with preview

            index = self.v.preview_tabs.currentIndex()

            self.v.preview_tabs.removeTab(index)

            self.v.show_markdown_preview(note, md)

            self.v.enable_buttons(save=False, cancel=False, edit=True)

            self.v.show_status("Edit canceled.")

    def save_note(self, *args, **kwargs):
        editor = self.v.preview_tabs.currentWidget()

        if not editor or not hasattr(editor, "note_name"):
            self.v.show_status("No note open to save.")

            return

        note = editor.note_name

        # Support SplitNoteEditor and plain QTextEdit

        if hasattr(editor, "toPlainText"):
            md = editor.toPlainText()

        elif hasattr(editor, "editor") and hasattr(editor.editor, "toPlainText"):
            md = editor.editor.toPlainText()

        else:
            md = ""

        try:
            self._backup_note_version(note)

            self.storage.write_note(note, md)

            # Always close the current tab (editor) and open new preview tab

            idx = self.v.preview_tabs.currentIndex()

            self.v.preview_tabs.removeTab(idx)

            # Open new preview tab for this note

            self.v.show_markdown_preview(note, md)

            self.v.enable_buttons(save=False, cancel=False, edit=True)

            self.v.show_status(f"Saved: {note}")

        except Exception as e:
            self.v.show_error("Save failed", str(e))

            self.v.show_status("Save error.")

    def new_note(self, *args, **kwargs):
        folder, ok = self.v.ask_user_folder("Select Folder", "Save to folder:")

        if not ok:
            return

        name, ok = self.v.ask_user_filename("File Name", "Enter file name (no .md):")

        if not ok or not name.strip():
            self.v.show_warning("Invalid name", "Please enter a valid file name.")

            return

        filename = make_title_case_filename(name.strip())

        rel = f"{folder}/{filename}.md" if folder else f"{filename}.md"

        if self.storage.exists(rel):
            self.v.show_warning("Exists", "Note already exists.")

            return

        self.storage.write_note(
            rel,
            "# " + filename + "\n\n## Notes\n\n- \n\n## Tags\n\n- \n\n## Links\n\n- \n",
        )

        self.load_tree()

        self.v.show_status(f"Created note: {rel}")

    def import_notes(self, *args, **kwargs):
        files = self.v.ask_user_files("Import Notes", "Markdown (*.md);;All Files (*)")

        if not files:
            return

        target = self.v.get_current_folder().strip()

        count = 0

        for path in files:
            name = Path(path).name

            rel = f"{target}/{name}" if target else name

            if self.storage.exists(rel):
                continue

            content = Path(path).read_text(encoding="utf-8")

            meta, body = read_note_metadata(content)

            meta, body = read_note_metadata(content)

            if not meta:  # No YAML at top
                content = write_note_metadata({}, body)

            self.storage.write_note(rel, content)

            count += 1

    def export_notes(self, *args, **kwargs):
        to_export = self.get_batch_selected_notes()

        if not to_export:
            sel = self.get_selected_note_name()

            if sel:
                to_export = [sel]

        if not to_export:
            self.v.show_status("No note(s) selected to export.")

            return

        folder = QFileDialog.getExistingDirectory(self.v, "Export to Folder")

        if not folder:
            return

        errors = []

        for note in to_export:
            try:
                content = self.storage.read_note(note)

                dest = str(Path(folder) / Path(note).name)

                Path(dest).write_text(content, encoding="utf-8")

            except Exception as e:
                errors.append(f"{note}: {e}")

        if errors:
            self.v.show_error("Export errors", "\n".join(errors))

        else:
            self.v.show_status(f"Exported {len(to_export)} note(s) to {folder}")

    def delete_notes(self, *args, **kwargs):
        to_delete = self.get_batch_selected_notes()

        if not to_delete:
            sel = self.get_selected_note_name()

            if sel:
                to_delete = [sel]

        if not to_delete:
            self.v.show_status("No note(s) selected to delete.")

            return

        if not self.v.ask_user_confirm("Delete Notes", f"Delete {len(to_delete)} note(s)?"):
            return

        errors = []

        for note in to_delete:
            try:
                note_content = self.storage.read_note(note)

                self.storage.delete_note(note)

                self.move_undo_stack.append(("delete_note", note, note_content))

            except Exception as e:
                errors.append(f"{note}: {e}")

        if errors:
            self.v.show_error("Delete errors", "\n".join(errors))

        else:
            self.v.show_status(f"Deleted {len(to_delete)} note(s).")

        self.load_tree()

    def tag_notes(self, *args, **kwargs):
        to_tag = self.get_batch_selected_notes()

        if not to_tag:
            sel = self.get_selected_note_name()

            if sel:
                to_tag = [sel]

        if not to_tag:
            self.v.show_status("No note(s) selected to tag.")

            return

        tags, ok = QInputDialog.getText(self.v, "Add Tags", "Enter tags (comma-separated):")

        if not ok or not tags.strip():
            return

        failures = []

        for note in to_tag:
            try:
                old_content = self.storage.read_note(note)

                new_content = old_content + "\n\n" + " ".join(f"[[{t.strip()}]]" for t in tags.split(","))

                self.storage.write_note(note, new_content)

                self.move_undo_stack.append(("tag_note", note, old_content))

            except Exception as e:
                failures.append(f"{note}: {e}")

        if failures:
            self.v.show_error("Tagging errors", "\n".join(failures))

        else:
            self.v.show_status(f"Tagged {len(to_tag)} note(s).")

        self.load_tree()

    def move_notes(self, *args, **kwargs):
        to_move = self.get_batch_selected_notes()

        if not to_move:
            sel = self.get_selected_note_name()

            if sel:
                to_move = [sel]

        if not to_move:
            self.v.show_status("No note(s) selected to move.")

            return

        target_folder, ok = QInputDialog.getText(self.v, "Move Notes", "Enter target folder:")

        if not ok or not target_folder.strip():
            return

        failures = []

        for note in to_move:
            try:
                content = self.storage.read_note(note)

                dest = f"{target_folder}/{Path(note).name}"

                self.storage.write_note(dest, content)

                self.storage.delete_note(note)

                self.move_undo_stack.append(("note", dest, note))

            except Exception as e:
                failures.append(f"{note}: {e}")

        if failures:
            self.v.show_error("Move errors", "\n".join(failures))

        else:
            self.v.show_status(f"Moved {len(to_move)} note(s) to {target_folder}")

        self.load_tree()

    def open_in_vault_for(self, note_name):
        backend = type(self.storage).__name__.replace("Storage", "").lower()

        if backend == "obsidian":
            vault = Path(self.config.VAULT_PATH).name

            file_enc = note_name.replace("/", "%2F")

            self.v.open_obsidian_link(vault, file_enc)

        else:
            # Fallback: open the note file in the user's default editor

            full_path = str(self.storage.vault_path / note_name)

            self.v.open_external_path(full_path)

    def export_specific(self, note_name):
        folder = QFileDialog.getExistingDirectory(self.v, "Export Note")

        if not folder:
            return

        content = self.storage.read_note(note_name)

        dest = str(Path(folder) / Path(note_name).name)

        Path(dest).write_text(content, encoding="utf-8")

        self.v.show_status(f"Exported {note_name} to {folder}")

    def delete_specific(self, note_name):
        if not self.v.ask_user_confirm("Delete Note", f"Delete '{note_name}'?"):
            return

        self.storage.delete_note(note_name)

        self.load_tree()

        self.v.show_status(f"Deleted {note_name}")

    def summarize_note(self, note_name):
        content = self.storage.read_note(note_name)

        summary = self.ai.summarize(content)

        self.v.show_summary_dialog(note_name, summary)

    def open_summarize_dialog(self, *args, **kwargs):
        from Ward_DND_AI.gui.browse.summarize.controller_summarize import (
            SummarizeController,
        )
        from Ward_DND_AI.gui.browse.summarize.view_summarize import SummarizeView

        dlg = QDialog(self.v)

        dlg.setWindowTitle("Summarize Notes")

        dlg.resize(600, 400)

        view = SummarizeView(dlg, self.config)

        SummarizeController(view, self.ai, self.storage, self.config, status_var=self.v.status_label)

        layout = QVBoxLayout(dlg)

        layout.addWidget(view)

        dlg.exec()

    def on_multi_select_toggled(self, enabled):
        self.v.toggle_multi_select(enabled)

        self.load_tree()

    def toggle_source_view(self, *args, **kwargs):
        btn = self.v.show_source_btn

        tab = self.v.preview_tabs.currentWidget()

        if not tab or not hasattr(tab, "note_name"):
            return

        name = tab.note_name

        if btn.text() == "Show Markdown Source":
            md = getattr(tab, "_markdown_content", None) or self.storage.read_note(name)

            self.v.show_markdown_editor(name, md)

            btn.setText("Show Rendered Preview")

        else:
            if hasattr(tab, "toPlainText"):
                md = tab.toPlainText()

            else:
                md = getattr(tab, "_markdown_content", None) or self.storage.read_note(name)

            import markdown2

            html = markdown2.markdown(md)

            self.v.show_html_editor(name, html)

            cur = self.v.preview_tabs.currentWidget()

            cur._markdown_content = md

            btn.setText("Show Markdown Source")

    def preview_note_metadata_only(self, note_path):
        # Metadata info only (no preview!)

        if note_path:
            try:
                self.v.show_metadata(note_path)

            except Exception as e:
                self.v.metadata_label.setText(f"<b>File:</b> {note_path}<br>(metadata unavailable: {e})")

        else:
            self.v.show_metadata("")

    def undo_last_move(self, *args, **kwargs):
        if not self.move_undo_stack:
            self.v.show_status("No actions to undo.")

            return

        typ, src, dest = self.move_undo_stack.pop()

        try:
            if typ == "note":
                self.storage.move_note(src, dest)

                self.v.show_status(f"Undo: moved note back to {dest}")

                self.v.rename_tab_by_note(src, dest)

            elif typ == "folder":
                self.storage.move_folder(src, dest)

                self.v.show_status(f"Undo: moved folder back to {dest}")

            elif typ == "delete_note":
                self.storage.write_note(src, dest)

                self.v.show_status(f"Undo: restored deleted note {src}")

            elif typ == "tag_note":
                self.storage.write_note(src, dest)

                self.v.show_status(f"Undo: reverted tags on note {src}")

            self.load_tree()

        except Exception as e:
            self.v.show_error("Undo failed", str(e))

    def get_open_in_label(self):
        backend = type(self.storage).__name__.replace("Storage", "").capitalize()

        if backend == "Obsidian":
            return "Open in Obsidian"

        else:
            return "Open in Vault"

    def search_notes(self, *args, **kwargs):
        query = self.v.search_input.text().strip()

        mode = self.v.search_type.currentText().lower()

        if not query:
            self.v.show_status("Enter a search term.")

            return

        if mode == "title":
            results = [n for n in self.storage.list_notes() if query.lower() in Path(n).name.lower()]

        elif mode == "tag":
            results = []

            for n in self.storage.list_notes():
                content = self.storage.read_note(n)

                # Find all tags and check if query is a substring

                tags = [
                    word.lstrip("#").strip("[]")
                    for word in content.split()
                    if word.startswith("#") or word.startswith("[[")
                ]

                if any(query.lower() in tag.lower() for tag in tags):
                    results.append(n)

        elif mode == "within":
            results = self.storage.search_notes(query, top_k=100)

        else:
            results = []

        if not results:
            self.v.show_status("No matching notes found.")

            self.v.set_tree_data([], [], "", "", False)

        else:
            self.v.set_tree_data([], results, "", "", False)

            self.v.show_status(f"Found {len(results)} note(s) matching search.")

    def new_note_from_template(self, *args, **kwargs):
        template_key = self.v.template_dropdown.currentText()

        template = self.v.templates_dict.get(template_key, {})

        content = template.get("content", "")

        # Editor dialog before saving

        from PyQt6.QtWidgets import (
            QDialog,
            QLabel,
            QLineEdit,
            QPushButton,
            QTextEdit,
            QVBoxLayout,
        )

        dlg = QDialog(self.v)

        dlg.setWindowTitle(f"New Note - {template_key}")

        layout = QVBoxLayout(dlg)

        name_label = QLabel("Enter note name (no extension):")

        name_input = QLineEdit()

        editor = QTextEdit()

        editor.setPlainText(content)

        save_btn = QPushButton("Save")

        cancel_btn = QPushButton("Cancel")

        layout.addWidget(name_label)

        layout.addWidget(name_input)

        layout.addWidget(editor)

        layout.addWidget(save_btn)

        layout.addWidget(cancel_btn)

    def _backup_note_version(self, note_path):
        """Delegate backup to storage layer."""
        if self.storage.exists(note_path):
            self.storage.backup_note(note_path)

    def open_history_dialog(self, *args, **kwargs):
        note = self.get_selected_note_name()

        if not note:
            self.v.show_status("Select a note to view history.")

            return

        version_names = self.storage.list_note_versions(note)

        if not version_names:
            self.v.show_status("No versions saved for this note.")

            return

        versions = []

        for fname in sorted(version_names, reverse=True):
            tstr = fname.split(".")[-2] if "." in fname else "?"
            fpath = str(self.storage.vault_path / ".versions" / Path(note).parent / fname)
            versions.append((fpath, tstr))

        if not versions:
            self.v.show_status("No versions saved for this note.")

            return

        dlg = VersionHistoryDialog(self.v, versions, note, self._restore_note_version)

        if dlg.exec() and dlg.selected_file:
            self._restore_note_version(note, dlg.selected_file)

    def _restore_note_version(self, note, version_file):
        with open(version_file, encoding="utf-8") as f:
            text = f.read()

        self.storage.write_note(note, text)

        self.load_tree()

        self.v.show_status(f"Restored version: {Path(version_file).name}")

    def _backup_note_version(self, note_path):
        """Delegate backup to storage layer."""
        if self.storage.exists(note_path):
            self.storage.backup_note(note_path)

    def get_full_metadata(self, note_name):
        meta = {
            "File Name": Path(note_name).name,
            "Path": note_name,
            "Full Path": str(self.storage.vault_path / note_name),
        }
        try:
            stat_meta = self.storage.get_note_metadata(note_name)
            meta["Date Created"] = stat_meta.get("created", "N/A")[:16].replace("T", " ")
            meta["Date Modified"] = stat_meta.get("modified", "N/A")[:16].replace("T", " ")
        except Exception:
            meta["Date Created"] = meta["Date Modified"] = "N/A"

        # Content stats

        try:
            content = self.storage.read_note(note_name)

            meta["Word Count"] = str(len(content.split()))

            meta["Character Count"] = str(len(content))

            tags = set(re.findall(r"(?:\[\[|\#)([A-Za-z0-9_\- ]+)(?:\]\])?", content))

            meta["Tags"] = ", ".join(sorted(tags)) if tags else "None"

        except Exception:
            meta["Word Count"] = meta["Character Count"] = meta["Tags"] = "N/A"

        # Optional: Backlinks (notes that mention this note)

        backlinks = []

        for n in self.storage.list_notes():
            if n == note_name:
                continue

            try:
                other_content = self.storage.read_note(n)

                if Path(note_name).stem in other_content:
                    backlinks.append(n)

            except Exception:
                pass

        meta["Backlink Count"] = str(len(backlinks))

        meta["Backlinks"] = ", ".join(backlinks) if backlinks else "None"

        return meta

    def toggle_note_view_for(self, note_name):
        tab = None

        for i in range(self.v.preview_tabs.count()):
            widget = self.v.preview_tabs.widget(i)

            if hasattr(widget, "note_name") and widget.note_name == note_name:
                tab = widget

                tab_index = i

                break

        if not tab:
            self.v.show_status("No open tab for that note.")

            return

        # Remove current tab and re-add as opposite mode

        if hasattr(tab, "editor"):  # If editing, switch to preview
            md = tab.toPlainText()

            self.v.preview_tabs.removeTab(tab_index)

            self.v.show_markdown_preview(note_name, md)

            self.v.enable_buttons(save=False, cancel=False, edit=True)

            self.v.show_status("Switched to preview.")

        else:  # If preview, switch to edit
            md = self.storage.read_note(note_name)

            self.v.preview_tabs.removeTab(tab_index)

            self.v.show_markdown_editor(note_name, md)

            self.v.enable_buttons(save=True, cancel=True, edit=False)

            self.v.show_status("Switched to edit mode.")

    def _star_path(self):
        # Deprecated — use storage.read_starred() / write_starred()
        return str(self.storage.vault_path / STAR_FILE)

    def open_links_dialog(self, *args, **kwargs):
        note = self.get_selected_note_name()

        if not note:
            self.v.show_status("Select a note to view links.")

            return

        # --- Forward links: all [[...]] in this note

        content = self.storage.read_note(note)

        fw_links = set(re.findall(r"\[\[([^\[\]]+)\]\]", content))

        # --- Backlinks: any other note that links to this note

        note_base = Path(note).stem

        backlinks = set()

        for n in self.storage.list_notes():
            if n == note:
                continue

            c = self.storage.read_note(n)

            if re.search(rf"\[\[\s*{re.escape(note_base)}\s*\]\]", c):
                backlinks.add(n)

        # --- Dialog

        from Ward_DND_AI.gui.browse.view_browse import NoteLinksDialog

        def open_note_callback(link_name):
            # Try to resolve link to note path

            link_path = None

            for n in self.storage.list_notes():
                if Path(n).stem.lower() == link_name.lower():
                    link_path = n

                    break

            if link_path:
                content = self.storage.read_note(link_path)

                self.v.open_note_tab(link_path, content, editable=False)

                self.v.show_metadata(link_path)

            else:
                self.v.show_status(f"Could not resolve: {link_name}")

        dlg = NoteLinksDialog(self.v, note, fw_links, backlinks, open_note_callback)

        dlg.exec()

    def open_metadata_dialog(self, *args, **kwargs):
        note = self.get_selected_note_name()

        if not note:
            self.v.show_status("Select a note to edit metadata.")

            return

        meta = self.storage.get_note_metadata(note)

        dlg = MetadataEditorDialog(self.v, meta)

        if dlg.exec():
            new_meta = dlg.get_metadata()

            self.storage.update_note_metadata(note, new_meta)

            self.v.show_status("Metadata updated.")

            # Optionally update the metadata preview label

            self.v.show_metadata(note)
