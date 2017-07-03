import re

with open('filtered.out', 'w') as fil:
    with open('pdu.out', 'r') as pdu:
        for line in pdu:
            if line.find('location') == -1 and not re.match(r'^\s*$', line) and line[:4] != '<!--' and line[:7] != '<title>':
                fil.write(line)
