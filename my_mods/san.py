import re

def wwpn_colonizer(wwpn, notation=':'):
    notation_set = set([':', '-', ' ', ''])
    if notation not in notation_set:
        notation = ':'
    # Remove colons if they exist
    wwpn = wwpn.replace(':', '')
    # Remove spaces if they exist
    wwpn = wwpn.replace(' ', '')
    # Remove dashes if they exist
    wwpn = wwpn.replace('-', '')
    # Determine if the wwpn is the correct length and has valid characters
    if len(wwpn) == 16 and re.match('[0-9a-fA-F]{16}', str(wwpn)):
        if notation == '':
            wwpn_converted = wwpn
        else:
            wwpn_converted = notation.join(re.findall('..', wwpn))
    else:
        # Return Error Message if the length and/or characaters are invalid
        print(f'Error in {__name__}.wwpn_colonizer(). Invalid WWPN Format.  {len(wwpn)}')
        exit()
    return wwpn_converted

    """Check if given value exists in list of dictionaries """
    for elem in dict_list:
        if value in elem.values():
            return True
    return False