#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id$

"""
Attribute class for GRAMPS
"""

__revision__ = "$Revision: 9101 $"

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from secondaryobj import SecondaryObject
from privacybase import PrivacyBase
from srcbase import SourceBase
from notebase import NoteBase
from attrtype import AttributeType

#-------------------------------------------------------------------------
#
# Attribute for Person/Family/MediaObject/MediaRef
#
#-------------------------------------------------------------------------
class Attribute(SecondaryObject, PrivacyBase, SourceBase, NoteBase):
    """Provides a simple key/value pair for describing properties. Used
    by the Person and Family objects to store descriptive information."""
    
    def __init__(self, source=None):
        """
        Creates a new Attribute object, copying from the source if provided.
        """
        PrivacyBase.__init__(self, source)
        SourceBase.__init__(self, source)
        NoteBase.__init__(self, source)
        
        if source:
            self.type = source.type
            self.value = source.value
        else:
            self.type = AttributeType()
            self.value = ""

    def serialize(self):
        """
        Converts the object to a serialized tuple of data
        """
        return (PrivacyBase.serialize(self),
                SourceBase.serialize(self),
                NoteBase.serialize(self),
                self.type.serialize(), self.value)

    def unserialize(self, data):
        """
        Converts a serialized tuple of data to an object
        """
        (privacy, source_list, note_list, the_type, self.value) = data
        PrivacyBase.unserialize(self, privacy)
        SourceBase.unserialize(self, source_list)
        NoteBase.unserialize(self, note_list)
        self.type.unserialize(the_type)
        return self

    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.value]

    def get_text_data_child_list(self):
        """
        Returns the list of child objects that may carry textual data.

        @return: Returns the list of child objects that may carry textual data.
        @rtype: list
        """
        return self.source_list

    def get_handle_referents(self):
        """
        Returns the list of child objects which may, directly or through
        their children, reference primary objects..
        
        @return: Returns the list of objects refereincing primary objects.
        @rtype: list
        """
        return self.source_list

    def get_referenced_handles(self):
        """
        Returns the list of (classname,handle) tuples for all directly
        referenced primary objects.
        
        @return: List of (classname,handle) tuples for referenced objects.
        @rtype: list
        """
        return self.get_referenced_note_handles()

    def set_type(self, val):
        """sets the type (or key) of the Attribute instance"""
        self.type.set(val)

    def get_type(self):
        """returns the type (or key) or the Attribute instance"""
        return self.type

    def set_value(self, val):
        """sets the value of the Attribute instance"""
        self.value = val

    def get_value(self):
        """returns the value of the Attribute instance"""
        return self.value
