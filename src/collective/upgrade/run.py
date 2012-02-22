import os
import sys
import logging
import pdb

from zodbupdate import main


if __name__ == '__main__':
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    stdout_handler = root.handlers[0]
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.addFilter(main.duplicate_filter)
    root.addHandler(logging.FileHandler(
        os.path.join('var', 'log', 'upgrade.log'), mode='w'))
    upgrader = Upgrader(makerequest(app))
    try:
        upgrader()
    except:
        upgrader.logger.exception('Exception running the upgrades.')
        pdb.post_mortem(sys.exc_info()[2])
        raise
