"""All route blueprints, collected for easy registration in the app factory."""

from . import pages, notes, groups, settings

ALL_BLUEPRINTS = [pages.bp, notes.bp, groups.bp, settings.bp]
