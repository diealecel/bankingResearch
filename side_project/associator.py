import re

FILE_LOC = 'specimen.txt'
REGEX = r'^ (Section )?\d*\. '
REGEX_2 = r'^ (Section )?\d*\. .*\(.*\)'

if __name__ == '__main__':
    with open(FILE_LOC, 'r') as src:
        valid = re.compile(REGEX)
        valid_2 = re.compile(REGEX_2)
        all_lines = []
        str_buffer = ''

        for line in src:
            if valid.match(line):
                if valid_2.match(str_buffer):
                    all_lines.append(str_buffer.lstrip()) # gets rid of first space

                str_buffer = line.rstrip() # get rid of newline, etc (including weird char)
            else:
                str_buffer += line.rstrip() #uses extra space as space I'd originally insert, so you should change it to make the additional space more explicit (actually put it in yourself)
        if valid_2.match(str_buffer): # just in case last one is actually a thing we want (there wouldn't be another thing after it to add it, so we're doing it here to catch it. there's definitely a more elegant way to approach this but this works for now)
            all_lines.append(str_buffer.lstrip())

        dictionary = {}

        for thing in all_lines:
            end_tag = thing[thing.rfind(' (') + 1 : thing.rfind(')') + 1]
            dictionary[thing] = end_tag

        for thing in dictionary:
            print dictionary[thing]

        print len(dictionary)
