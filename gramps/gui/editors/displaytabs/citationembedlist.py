#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2011       Tim G L Lyons
# Copyright (C) 2025       Alois Poettker
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

# -------------------------------------------------------------------------
#
# Python classes
#
# -------------------------------------------------------------------------
import logging

# -------------------------------------------------------------------------
#
# GTK/Gnome modules
#
# -------------------------------------------------------------------------
from gi.repository import Gtk
from gi.repository import GLib

# -------------------------------------------------------------------------
#
# Gramps classes
#
# -------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale

from gramps.gen.db import DbTxn
from gramps.gen.errors import WindowActiveError
from gramps.gen.lib import Citation, Source
from ...dbguielement import DbGUIElement
from ...selectors import SelectorFactory
from .citationrefmodel import CitationRefModel
from .embeddedlist import EmbeddedList, TEXT_COL, MARKUP_COL, ICON_COL
from ...ddtargets import DdTargets

LOG = logging.getLogger(".citation")
_ = glocale.translation.gettext


# -------------------------------------------------------------------------
#
# CitationEmbedList
#
# -------------------------------------------------------------------------
class CitationEmbedList(EmbeddedList, DbGUIElement):
    """
    Citation List display tab for edit dialogs.

    Derives from the EmbeddedList class.
    """

    _HANDLE_COL = 10  # Column number from CitationRefModel
    _DND_TYPE = DdTargets.CITATION_LINK
    _DND_EXTRA = DdTargets.SOURCE_LINK

    _MSG = {
        "add": _("Create and add a new citation and new source"),
        "del": _("Remove the existing citation"),
        "edit": _("Edit the selected citation"),
        "share": _("Add an existing citation or source"),
        "clone" : _("Clone an existing citation"),
        "merge" : _("Merge two existing citations"),
        "up": _("Move the selected citation upwards"),
        "down": _("Move the selected citation downwards"),
    }

    # index = column in model. Value =
    #   (name, sortcol in model, width, markup/text, weigth_col)
    _column_names = [
        (_("Title"), 0, 350, TEXT_COL, -1, None),
        (_("Author"), 1, 200, TEXT_COL, -1, None),
        (_("Date"), 8, 180, MARKUP_COL, -1, None),
        (_("Publisher"), 3, 200, TEXT_COL, -1, None),
        (_("Confidence"), 9, 120, MARKUP_COL, -1, None),
        (_("Page"), 5, 100, TEXT_COL, -1, None),
        (_("ID"), 6, 80, TEXT_COL, -1, None),
        (_("Private"), 7, 30, ICON_COL, -1, "gramps-lock"),
        (_("Sorted date"), 8, 80, TEXT_COL, -1, None),
        (_("Sorted confidence"), 9, 120, TEXT_COL, -1, None),
    ]

    def __init__(self, dbstate, uistate, track, data, config_key, callertitle=None):
        self.data = data
        self.callertitle = callertitle
        EmbeddedList.__init__(
            self,
            dbstate,
            uistate,
            track,
            _("_Source Citations"),
            CitationRefModel,
            config_key,
            share_button=True,
            clone_button=True,
            merge_button=True,
            move_buttons=True,
        )
        DbGUIElement.__init__(self, dbstate.db)
        self.callman.register_handles({"citation": self.data})

        # Gtk mode to allow multiple selection of list entries
        self.selection.set_mode(Gtk.SelectionMode.MULTIPLE)

    def _selection_changed(self, obj=None):
        """
        Callback method called after user selection of a row
        overwrites method in buttontab.py
        """
        if self.dirty_selection:
            return

        # picks the actual selected rows
        self.selected_list = []   # Selection list (eg. multiselection)
        (model, pathlist) = self.selection.get_selected_rows()
        for path in pathlist:
            iter = model.get_iter(path)
            if iter is not None:
                value = model.get_value(iter, self._HANDLE_COL)   # (Index, Citation)
                self.selected_list.append(value)   # Citation handle

        # manage the sensitivity of several buttons to avoid warning messages
        if self.selected_list:
            btn = len(self.selected_list) == 1
            self.edit_btn.set_sensitive(btn)
            self.clone_btn.set_sensitive(btn)
            self.del_btn.set_sensitive(btn)

            btn = len(self.selected_list) == 2
            self.merge_btn.set_sensitive(btn)

    def _connect_db_signals(self):
        """
        Implement base class DbGUIElement method
        """
        # citation: citation-rebuild closes the editors, so no need to connect to it
        self.callman.register_callbacks(
            {
                "citation-delete": self.citation_delete,
                "citation-update": self.citation_update,
                # "citation-clone": self.citation_clone,
                # "citation-merge": self.citation_merge,
            }
        )
        self.callman.connect_all(keys=["citation"])

    def get_icon_name(self):
        """
        Return the stock-id icon name associated with the display tab
        """
        return "gramps-source"

    def get_data(self):
        """
        Return the data associated with display tab
        """
        return self.data

    def column_order(self):
        """
        Return the column order of the columns in the display tab.
        """
        return ((1, 7), (1, 0), (1, 1), (1, 5), (1, 2), (1, 3), (1, 6), (1, 4))

    def add_button_clicked(self, obj):
        """
        Create a new Citation instance and call the EditCitation editor with
        the new citation.

        Called when the Add button is clicked.
        If the window already exists (WindowActiveError), we ignore it.
        This prevents the dialog from coming up twice on the same object.
        """
        try:
            from .. import EditCitation

            EditCitation(
                self.dbstate,
                self.uistate,
                self.track,
                Citation(),
                Source(),
                self.object_added,
                self.callertitle,
            )
        except WindowActiveError:
            pass

    def object_added(self, value):
        """
        Called to update the screen when a new citation is added
        """
        data = self.get_data()
        data.append(value)
        self.callman.register_handles({"citation": [value]})
        self.changed = True
        self.rebuild()
        GLib.idle_add(self.tree.scroll_to_cell, len(data) - 1)

    def share_button_clicked(self, obj):
        SelectCitation = SelectorFactory("Citation")

        sel = SelectCitation(self.dbstate, self.uistate, self.track)
        objct = sel.run()
        LOG.debug("selected object: %s" % objct)
        # the object returned should either be a Source or a Citation
        if objct:
            if isinstance(objct, Source):
                try:
                    from .. import EditCitation

                    EditCitation(
                        self.dbstate,
                        self.uistate,
                        self.track,
                        Citation(),
                        objct,
                        callback=self.object_added,
                        callertitle=self.callertitle,
                    )
                except WindowActiveError:
                    from ...dialog import WarningDialog

                    WarningDialog(
                        _("Cannot share this reference"),
                        self.__blocked_text(),
                        parent=self.uistate.window,
                    )
            elif isinstance(objct, Citation):
                try:
                    from .. import EditCitation

                    EditCitation(
                        self.dbstate,
                        self.uistate,
                        self.track,
                        objct,
                        callback=self.object_added,
                        callertitle=self.callertitle,
                    )
                except WindowActiveError:
                    from ...dialog import WarningDialog

                    WarningDialog(
                        _("Cannot share this reference"),
                        self.__blocked_text(),
                        parent=self.uistate.window,
                    )
            else:
                raise ValueError("selection must be either source or citation")

    def __blocked_text(self):
        """
        Return the common text used when citation cannot be edited
        """
        return _(
            "This citation cannot be created at this time. "
            "Either the associated Source object is already being "
            "edited, or another citation associated with the same "
            "source is being edited.\n\nTo edit this "
            "citation, you need to close the object."
        )

    def edit_button_clicked(self, obj):
        """
        Get the selected Citation instance and call the EditCitation editor
        with the citation.

        Called when the Edit button is clicked.
        If the window already exists (WindowActiveError), we ignore it.
        This prevents the dialog from coming up twice on the same object.
        """
        handle = self.get_selected()
        if handle:
            citation = self.dbstate.db.get_citation_from_handle(handle)
            try:
                from .. import EditCitation

                EditCitation(
                    self.dbstate,
                    self.uistate,
                    self.track,
                    citation,
                    callertitle=self.callertitle,
                )
            except WindowActiveError:
                pass


    def clone_button_clicked(self, obj):
        # Method  called with the Clone button is clicked.

        source_ref = self.get_selected()
        if source_ref:
            source_citation = self.dbstate.db.get_citation_from_handle(source_ref)

            try:
                citation = Citation(source=source_citation)
                citation.set_gramps_id(self.dbstate.db.find_next_citation_gramps_id())
                citation.set_handle(None)
                source_handle = citation.get_reference_handle()
                source = self.dbstate.db.get_source_from_handle(source_handle)
                """
                self.changed = True
                with DbTxn(_("Clone Citation (%s)") % citation.gramps_id,
                           self.dbstate.db) as trans:
                    self.dbstate.db.add_citation(citation, trans)
                """
                self.action = 'Citation-Clone'
                from .. import EditCitation
                EditCitation(
                    self.dbstate,
                    self.uistate,
                    self.track,
                    citation,
                    source,
                    self.object_added,
                    self.callertitle,
                )
            except WindowActiveError:
                pass

    def merge_button_clicked(self, obj):
        # Method called with the Merge button is clicked.

        # double check for properly work; see eventembedlist/_selection_changed
        if len(self.selected_list) != 2:
            return

        # Checks if event are not equal
        if self.selected_list[0] == self.selected_list[1]:
            from ...dialog import WarningDialog
            WarningDialog(
                _("Cannot merge this references"),
                _("This is one event, but with different roles."),
                parent=self.uistate.window, )
            return

        self.changed = True
        self.action = 'Citation-Merge'
        from ...merge import MergeCitation
        MergeCitation(self.dbstate, self.uistate, self.track, \
                      self.selected_list[0], self.selected_list[1])

    def citation_delete(self, del_citation_handle_list):
        """
        Outside of this tab citation objects have been deleted. Check if tab
        and object must be changed.
        Note: delete of object will cause reference on database to be removed,
            so this method need not do this
        """
        rebuild = False
        for handle in del_citation_handle_list:
            while self.data.count(handle) > 0:
                self.data.remove(handle)
                rebuild = True
        if rebuild:
            self.rebuild()

    def citation_update(self, upd_citation_handle_list):
        """
        Outside of this tab citation objects have been updated. Check if tab
        and object must be updated.
        """
        for handle in upd_citation_handle_list:
            if handle in self.data:
                self.rebuild()
                break

    def _handle_drag(self, row, handle):
        """
        A CITATION_LINK has been dragged
        """
        if handle:
            objct = self.dbstate.db.get_citation_from_handle(handle)
            if isinstance(objct, Citation):
                try:
                    from .. import EditCitation

                    EditCitation(
                        self.dbstate,
                        self.uistate,
                        self.track,
                        objct,
                        callback=self.object_added,
                        callertitle=self.callertitle,
                    )
                except WindowActiveError:
                    from ...dialog import WarningDialog

                    WarningDialog(
                        _("Cannot share this reference"),
                        self.__blocked_text(),
                        parent=self.uistate.window,
                    )
            else:
                raise ValueError("selection must be either source or citation")

    def handle_extra_type(self, objtype, handle):
        """
        A SOURCE_LINK object has been dragged
        """
        if handle:
            objct = self.dbstate.db.get_source_from_handle(handle)
            if isinstance(objct, Source):
                try:
                    from .. import EditCitation

                    EditCitation(
                        self.dbstate,
                        self.uistate,
                        self.track,
                        Citation(),
                        objct,
                        callback=self.object_added,
                        callertitle=self.callertitle,
                    )
                except WindowActiveError:
                    from ...dialog import WarningDialog

                    WarningDialog(
                        _("Cannot share this reference"),
                        self.__blocked_text(),
                        parent=self.uistate.window,
                    )
            else:
                raise ValueError("selection must be either source or citation")
