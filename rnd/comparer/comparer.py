import os
import sys

BASE_FOLDER = 'new'
COMP_FOLDER = 'old'

if __name__ == '__main__':
    for filename in os.listdir(BASE_FOLDER):
        base_file = os.path.join(BASE_FOLDER, filename)
        comp_file = os.path.join(COMP_FOLDER, filename)

        with open(base_file, 'r') as base:
            with open(comp_file, 'r') as comp:
                base_lines = comp_lines = []

                for base_line in base:
                    base_lines.append(base_line)

                for comp_line in comp:
                    comp_lines.append(comp_line)

                for i in xrange(len(base_lines)):
                    if base_lines[i] != comp_lines[i]:
                        sys.exit('Found a difference!')

    print 'Found no conflicts.'
