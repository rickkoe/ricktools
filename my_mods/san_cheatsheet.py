brocade_cheatsheet = [
    '\n####################################################################',
    '#                        BROCADE CHEATSHEET                        #',
    '####################################################################',
    '### SHOW EFFECTIVE ZONE CONFIG NAME',
    '  cfgshow | grep -A 1 Effective',
    '### SHOW PENDING ZONING CHANGES THAT HAVE NOT BEEN SAVED TO FABRIC',
    '  cfgshow --transdiffsonly',
    '### SHOW ZONING WITH "*" ON MEMBERS THAT ARE NOT LOGGED INTO THE FABRIC',
    '  zoneshow --validate',
]

cisco_cheatsheet = [ 
    '\n####################################################################',
    '#                         CISCO CHEATSHEET                         #',
    '####################################################################',
    '### SHOW ZONING WITH "*" ON MEMBERS THAT ARE LOGGED INTO THE FABRIC',
    '  show zoneset active',
    '### SHOW ALL LOGGED-IN WWPNS AND ASSOCIATED DEVICE-ALIASES',
    '  show flogi database',
]