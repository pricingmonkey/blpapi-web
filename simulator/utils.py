import re, random

def randomFieldValue(field, security = "RXH7 COMDTY"):
    if field == "FUT_CTD_CPN":
        return "1.000"
    elif field == "FUT_CTD_MTY":
        return "08/15/2025"
    elif field == "FUT_CTD_FREQ":
        return "A"
    elif field == "FUT_DLV_DT_LAST":
        return "12/12/2016"
    elif field == "FUT_CNVS_FACTOR":
        return ".669312"
    elif len(security) < 12:
        return str(99 + (0.05 * random.random()))
    else:
        return str(0.14 + (0.05 * random.random()))

def merge_dicts(d1, d2):
    out = d1.copy()
    out.update(d2)
    return out

def isValidSecurity(security):
    strikeMatch = re.search(" (\d*\.?\d*) Comdty", security)
    strike = None
    if strikeMatch:
        strike = float(strikeMatch.group(1))
    if security.endswith("ERR"):
        return False
    elif strike and (strike < 50 or strike > 200):
        return False
    else:
        return True

