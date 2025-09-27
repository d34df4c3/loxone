from Loxone.ApiClient import BasicAuth
from Loxone.Control.NfcCodeTouch import NfcCodeTouch, CodeType
import logging
import pytz
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

# Initialize the Loxone API client with basic authentication
client = BasicAuth(
    url="http://213.211.136.162:8080",
    user="DokosAPI",#"JulienAdmin",#
    password="6xC49dEw2Q=2TGe"#"jULIENroot0486" #
)

# Load the MiniServer configuration
from Loxone.MiniServer import MiniServerLoader
miniserver = MiniServerLoader(client).load()


nfc = miniserver.get_nfc_code_touch_by_name("Porte extérieure")
if nfc is None:
    logging.critical("NFC Code Touch with name 'Porte extérieure' not found.")
    exit(1)

nfc.impulse(1)

exit(1)

logging.info("Retrieving NFC codes...")
codes = nfc.codes()
for code in codes:
    logging.info(f"Code: {code}")

for code in codes:
    if code.name.startswith('Test-00'):
        logging.info(f"Deleting code: {code.name}")
        code.delete()

# Create a new NFC code
brussels_tz = pytz.timezone("Europe/Brussels")
code = (nfc.code_builder()
        .name("Test-UNTIL-2223")
        .code("2223")
        .type(CodeType.TIME_DEPENDENT)
        .time_from(brussels_tz.localize(datetime(2023, 10, 1, 11, 30, 00)))
        .time_to(brussels_tz.localize(datetime(2025, 6, 21, 14, 00, 00)))
        .set_output(1)
        .build())

if code.create():
    logging.info("Created NFC code successfully")
else:
    logging.error("Failed to create NFC code")

for code in nfc.codes():
    if code.name == "Test-UNTIL-2223":
        code.name = "Test-UNTIL-2223-UPDATED"
        code.type = CodeType.VALID_UNTIL
        code.time_to = brussels_tz.localize(datetime(2025, 6, 21, 15, 30, 00))
        code.update()
        logging.info(f"Updated code: {code}")