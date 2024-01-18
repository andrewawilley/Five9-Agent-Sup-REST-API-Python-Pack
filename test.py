import logging

from test_classes import *

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)		
		
a = SC()
TC.parentlevel = 99
logging.debug(f"A parent: {a.parentlevel}")

