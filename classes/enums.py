from enum import Enum

class quality_enum (Enum):
    BAD = 0x00
    CFGERROR= 0x04
    STALE = 0x40
    OUTOFRANGEMIN = 0x41
    OUTOFRANGEMAX = 0x42
    FROZEN = 0x43
    OK = 0xc0
    LOCALOVERRIDE = 0xD8

    