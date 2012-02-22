from zope import interface


class IUpgrader(interface.Interface):
    """Upgrade a context."""
