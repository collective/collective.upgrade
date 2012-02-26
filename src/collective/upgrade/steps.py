import logging

from Products.CMFCore.utils import getToolByName

logger = logging.getLogger('collective.upgrade')


def deleteCustomSkinObjs(context, *obj_ids):
    skins = getToolByName(context, 'portal_skins')
    del_ids = [obj_id for obj_id in obj_ids
               if obj_id in skins.custom]
    if not del_ids:
        return

    skins.custom.manage_delObjects(del_ids)
    logger.info(
        'Deleted custom skin objects from %r: %r'
        % (skins.custom, del_ids))
