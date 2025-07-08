import time
import binascii

from pn532pi import Pn532, pn532
from pn532pi import Pn532I2c
from pn532pi import Pn532Spi
from pn532pi import Pn532Hsu

SPI = False
I2C = True
HSU = False

if SPI:
    PN532_SPI = Pn532Spi(Pn532Spi.SS0_GPIO8)
    nfc = Pn532(PN532_SPI)
# When the number after #elif set as 1, it will be switch to HSU Mode
elif HSU:
    PN532_HSU = Pn532Hsu(Pn532Hsu.RPI_MINI_UART)
    nfc = Pn532(PN532_HSU)

# When the number after #if & #elif set as 0, it will be switch to I2C Mode
elif I2C:
    PN532_I2C = Pn532I2c(1)
    nfc = Pn532(PN532_I2C)


def setup():
    nfc.begin()

    versiondata = nfc.getFirmwareVersion()
    if (not versiondata):
        print("Didn't find PN53x board")
        data = {
            "success": False,
            "error": "Didn't find PN53x board"
        }
        return data
        # raise RuntimeError("Didn't find PN53x board")  # halt

    #  Got ok data, print it out!

    print_output = ("Found chip PN5 {:#x} Firmware ver. {:d}.{:d}".format((versiondata >> 24) & 0xFF, (versiondata >> 16) & 0xFF,
                                                                (versiondata >> 8) & 0xFF))
    print(print_output)

    #  configure board to read RFID tags
    nfc.SAMConfig()

    data = {
        "success": True,
        "message": print_output
    }
    return data

# It will return a dictionary with success status, uid, uid length and type of card.
def iso14443a_identify():
    # Wait for an ISO14443A type cards (Mifare, etc.).  When one is found
    # 'uid' will be populated with the UID, and uidLength will indicate
    # if the uid is 4 bytes (Mifare Classic) or 7 bytes (Mifare Ultralight)
    success, uid = nfc.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS)

    if (success):
        print("Found a card!")
        print("UID Length: {:d}".format(len(uid)))
        print("UID Value: {}".format(binascii.hexlify(uid)))
        # Wait 1 second before continuing
        time.sleep(1)
        data = {
            "success": True,
            "uid": binascii.hexlify(uid).decode('utf-8'),
            "uid_length": len(uid),
            "type": ["Mifare Classic"] if len(uid) == 4 else ["NTAG21x", "Mifare DESFire", "Mifare Ultralight"]
        }
        return data
    else:
        # pn532 probably timed out waiting for a card
        print("Timed out waiting for a card")
        data = {
            "success": False,
            "error": "Timed out waiting for a card"
        }
        return data

def write_uid(new_uid_hex):
    print(f"Target UID: {new_uid_hex}")
    
    try:
        # Prepare new Block 0 data
        new_uid_bytes = binascii.unhexlify(new_uid_hex)
        
        # Read current Block 0 as template
        read_success, current_block0 = nfc.mifareclassic_ReadDataBlock(0)
        if not read_success:
            print("❌ Cannot read current Block 0")
            return {
                "success": False,
                "message": "Cannot read current Block 0"
            }
        
        # Build new Block 0 data
        new_block0 = bytearray(current_block0)
        new_block0[:4] = new_uid_bytes  # Replace first 4 bytes (UID)
        
        # Recalculate BCC (Block Check Character)
        bcc = new_uid_bytes[0] ^ new_uid_bytes[1] ^ new_uid_bytes[2] ^ new_uid_bytes[3]
        new_block0[4] = bcc
        
        print(f"📝 New Block 0: {binascii.hexlify(new_block0).decode().upper()}")
        
        # Attempt to write
        write_success = nfc.mifareclassic_WriteDataBlock(0, new_block0)
        
        if write_success:
            print("✅ Block 0 write successful!")
            return {
                "success": True,
                "message": "Block 0 write successful"
            }
        else:
            print("❌ Block 0 write failed!")
            return {
                "success": False,
                "message": "Block 0 write failed"
            }
            
    except Exception as e:
        print(f"❌ Error occurred during writing process: {e}")
        return {
            "success": False,
            "message": f"Error occurred during writing process: {str(e)}"
        }
