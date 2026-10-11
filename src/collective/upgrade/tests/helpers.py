# -*- coding: utf-8 -*-
"""Helpers shared by the test modules."""


def transaction_notes(app):
    """Descriptions of the transactions committed in the test storage."""
    notes = []
    for record in app._p_jar.db().storage.iterator():
        description = record.description
        if isinstance(description, bytes):
            description = description.decode("utf-8")
        notes.append(description)
    return notes


def messages(log):
    """Messages of a zope.testing.loggingsupport handler."""
    return [record.getMessage() for record in log.records]
