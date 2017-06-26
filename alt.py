# Diego Celis
# In the pursuit of making this thing work.

# TODO:
# 1. developing or incorporating a text comparison tool, and
# 2. figuring out a way to easily allow a user to compare texts from any given year
#    to any other given year, also providing information about changes made.

import subprocess                   # Needed to clear the console window (and to use bash commands, not that they are needed).
import time                         # Needed to calculate the amount of time taken to run algorithms.
import httplib                      # Needed to catch IncompleteRead
from httplib import IncompleteRead  # Also needed to catch IncompleteRead
import urllib2                      # Needed to use URLError.
from urllib2 import URLError        # Needed to catch URLError.
import mechanize                    # Needed to use Browser.
from bs4 import BeautifulSoup       # Needed to read source code.


# TITLE 15 GOES TO LETTER E and has ADDITIONAL THING THAT USES "-1"! LIKE
# CHAPTER 2B-1


# Title 12 goes from chapters 1 to 54
# Title 15 goes from chapters 1 to 111

TITLE = 15

# Initializing all variables.
LAWS_URL_PRE_YR = 'http://uscode.house.gov/view.xhtml?hl=false&edition='
LAWS_URL_POST_YR = '&req=granuleid%3AUSC-prelim-title' + str(TITLE) + '-chapter'

EDGE_TAG = 'leader-work-head-left'


# NOTE THAT THE YEAR ONLY GOES UP TO 2015, and the YEARS all start at 1994. ALSO "prelim" represents current year.

CH_START = 1
CH_STOP = 111
YR_START = 1994
YR_STOP = 2015
MIN_SOUP_LEN = 4000 # Received this value from testing the files with zero bytes.

TIME_START = time.time()

CH_LETS = ['', 'A', 'B', 'C', 'D', 'E']
LET_SECTS = ['', '-1']

INVALID_URL_LENS = [3861, 3865, 3869, 3873] # Received these values from testing the files with invalid URL's.


def clear_console():
    subprocess.call('clear', shell = True)


def print_end():
    print '\nEntire process finished, taking ' + time.strftime('%H hours, %M minutes, and %S seconds.', time.gmtime(time.time() - TIME_START))


def process_data(variate_yr_rng, undesirables):
    for variate_ch in xrange(CH_STOP - CH_START + 1):

        for variate_let in CH_LETS:
            
            for variate_sect in LET_SECTS:

                for variate_yr in variate_yr_rng:
                    ch_timer = time.time() # Start timer.

                    laws_url = LAWS_URL_PRE_YR + variate_yr + LAWS_URL_POST_YR + \
                               str(CH_START + variate_ch) + variate_let + variate_sect
                    soup, retry, tries = make_soup(laws_url)

                    # Exits current iteration of inner loop.
                    #
                    # The reason why 'break' isn't used is because some years are
                    # missing from some chapters.
                    if not validate_soup(soup):
                        continue

                    result_name, source_name = make_names(variate_ch, variate_let, variate_yr, variate_sect)
                    
                    

                    with open(source_name, 'w') as source: # Write HTML onto a file.
                        source.write(str(soup))

                    top = [] # Contains all Text objects with section 'section-head'
                    top, n_objs, n_valid_tags, n_invalid_tags = make_top(soup, result_name, source_name, undesirables, variate_ch, variate_let, variate_yr, variate_sect)

                    # Anything after this line is after the source.in has been read and |top|
                    # has been constructed.

                    report(n_objs, retry, tries, ch_timer, variate_ch, variate_let, variate_yr, variate_sect, n_valid_tags, n_invalid_tags)


def print_top(top, result):
    n_objs = 0

    for obj in top:
        n_objs += 1
        result.write(obj.get_content() + '\n')

        if obj.has_data():
            result.write(obj.get_data() + '\n')

        result.write('\n')

        if obj.has_subsections():
            n_objs += print_top(obj.get_subsections(), result)

    return n_objs


def report(n_objs, retry, tries, ch_timer, variate_ch, variate_let, variate_yr, variate_sect, n_valid_tags, n_invalid_tags):
    status = get_status(n_objs, retry, tries)

    print '{0:5}{1:6}{2:9}{3:10}{4:10}{5}'.format(str(CH_START + variate_ch) + variate_let + variate_sect, \
          'CURR' if variate_yr == 'prelim' else variate_yr, str(n_objs), \
          str(round(n_valid_tags / float(n_valid_tags + n_invalid_tags) * 100, 4)) + '%', \
          str(round(time.time() - ch_timer, 4)), status)


def get_status(n_objs, retry, tries):
    status = None

    if n_objs > 0:
        if not retry:
            status = 'SUCCESSFUL'
        
        else:
            status = 'SUCCESSFUL RETRY #' + str(tries)

    else:
        status = 'FAILED'

    return status


def make_top(soup, result_name, source_name, undesirables, variate_ch, variate_let, variate_yr, variate_sect):
    write_source(soup, source_name)
    
    top = [] # Contains all Text objects with section 'section-head'

    n_valid_tags = n_invalid_tags = 0

    with open(result_name, 'w') as result:
        with open(source_name, 'r') as source:
            for line in source:
                repeat_needed = False

                while True:
                    tag_let_loc = line.find('"') + 1
                    potential_tag = line[tag_let_loc : line.find('"', tag_let_loc)]
                    
                    tag_contents = None

                    if potential_tag == EDGE_TAG: # Special case, another tag is at end of |line|
                        second_line_loc = line.rfind('<', 0, line.rfind('<'))
                        tag_contents = line[line.find('>') + 1 : second_line_loc]

                        line_2 = line[second_line_loc : ]
                        repeat_needed = True

                    else:
                        tag_contents = line[line.find('>') + 1 : line.rfind('</')]

                    tag_contents = remove_html(tag_contents)

                    if potential_tag in HIERARCHY:
                        hierarchy_lvl = HIERARCHY[potential_tag]

                        # If |potential_tag| is 'section-head', then create a new Text object.
                        if hierarchy_lvl == 0:
                            # From end of first tag to beginning of ending tag.
                            new = Text(potential_tag, tag_contents, None, [], None)
                            top.append(new) # |top| contains all 'section-head' Text objects.
                        
                        # If |prev_obj| has a hierarchy right above that of |potential_tag|...
                        elif hierarchy_lvl > HIERARCHY[prev_obj.get_section()]:
                            new = Text(potential_tag, tag_contents, prev_obj, [], None)
                            prev_obj.add_subsection(new)

                        elif hierarchy_lvl == HIERARCHY[prev_obj.get_section()]:
                            new = Text(potential_tag, tag_contents, prev_obj.get_parent(), [], None)
                            prev_obj.get_parent().add_subsection(new)
                        
                        # Implicit hierarchy_lvl < HIERARCHY[prev_obj.get_section()]
                        else:
                            # Plus one because you need an additional iteration to reach correct parent.
                            # The minus element is to correct for discrepancies in hierarchy (maybe there's
                            # a skip of a hierarchical level)

                            # difference = HIERARCHY[prev_obj.get_section()] - hierarchy_lvl + 1 - \
                            #              (HIERARCHY[prev_obj.get_section()] - HIERARCHY[prev_obj.get_parent().get_section()] - 1)
                            difference = HIERARCHY[prev_obj.get_parent().get_section()] - hierarchy_lvl + 2
                            prev_obj = get_nth_parent(prev_obj, difference)

                            new = Text(potential_tag, tag_contents, prev_obj, [], None)
                            prev_obj.add_subsection(new)

                        prev_obj = new

                        n_valid_tags += 1

                    elif potential_tag in DATA_TYPE:
                        if not prev_obj.has_data():
                            prev_obj.set_data(tag_contents)

                        else:
                            prev_obj.add_to_data(tag_contents)
                        
                        n_valid_tags += 1

                    else:
                        # Essentially, if no tag is found or anything then this ELSE runs.
                        # Keep note of how there is a delimiter that allows for ease of searching
                        # inserted before |potential_tag|.
                        undesirables.add(str(CH_START + variate_ch) + variate_let + variate_sect + ' ' + variate_yr + '::' + potential_tag)
                        n_invalid_tags += 1

                    if not repeat_needed:
                        break

                    else:
                        repeat_needed = False
                        line = line_2

        return top, print_top(top, result), n_valid_tags, n_invalid_tags


def get_nth_parent(prev_obj, difference):
    for i in xrange(difference):
        prev_obj = prev_obj.get_parent()

    return prev_obj


# Write HTML onto a file
def write_source(soup, source_name):
    with open(source_name, 'w') as source:
        source.write(str(soup))


def make_names(variate_ch, variate_let, variate_yr, variate_sect):
    result_name = 'results/ch' + str(CH_START + variate_ch) + variate_let + variate_sect + 'yr' + \
                  ('CURR' if variate_yr == 'prelim' else variate_yr) + '.out'

    source_name = 'sources/ch' + str(CH_START + variate_ch) + variate_let + variate_sect + 'yr' + \
                  ('CURR' if variate_yr == 'prelim' else variate_yr) + '.in'

    return result_name, source_name


def make_soup(laws_url):
    retry = False
    tries = 0
    soup = None
    
    # Retries if the first read doesn't work.
    while True:
        try:
            br = mechanize.Browser()
            br.set_handle_robots(False) # I promise I'm not a robot.
            br.open(laws_url)

            html = br.response().read()
            soup = BeautifulSoup(html, 'html.parser') # Collect HTML from site

            if validate_html(soup):
                break

            retry = True
            tries += 1
        
        except (urllib2.URLError, httplib.IncompleteRead) as error:
            # Successfully caught error!

            retry = True
            tries += 1

    return soup, retry, tries


def validate_html(soup):
    soup_len = len(str(soup))

    return soup_len > MIN_SOUP_LEN or soup_len in INVALID_URL_LENS


def validate_soup(soup):
    soup_len = len(str(soup))

    return not soup_len in INVALID_URL_LENS


# This represents the variate years. Have to be made separately
# because 'prelim' has to be included at the end.
def make_variate_yr_rng():
    variate_yr_rng = []

    for i in range(YR_STOP - YR_START + 1):
        variate_yr_rng.append(str(YR_START + i))

    # This is a special word used to reference the current year.
    variate_yr_rng.append('prelim')

    return variate_yr_rng





def print_beginning():
    print_intro()

    print 'Accessing title ' + str(TITLE) + ' chapters ' + str(CH_START) + ' to ' + str(CH_STOP) + '.'
    print 'Looking through years ' + str(YR_START) + ' to ' + str(YR_STOP) + '.\n'

    print_header()


def print_intro():
    print "Welcome to Diego's Indexer v3!"
    print "File processing is now starting.\n"


# This works as the header by which the program will show the files processed
def print_header():
    print '{0:5}{1:6}{2:9}{3:10}{4:10}{5}'.format('Ch.', 'Year', 'Objects', 'Usage', 'Time (s)', 'Status')


HIERARCHY = {'section-head'             : 0, \
             'subsection-head'          : 1, \
             'paragraph-head'           : 2, \
             'subparagraph-head'        : 3, \
             'clause-head'              : 4, \
             'subclause-head'           : 5, \
             'subsubclause-head'        : 6}

DATA_TYPE = ['statutory-body',                                               \
             'statutory-body-1em',                                           \
             'statutory-body-2em',                                           \
             'statutory-body-3em',                                           \
             'statutory-body-4em',                                           \
             'statutory-body-5em',                                           \
             'statutory-body-6em',                                           \
             'statutory-body-block',                                         \
             'statutory-body-block-1em',                                     \
             'statutory-body-block-2em',                                     \
             'statutory-body-flush2_hang3',                                  \
             'wide_left_side_0em-two-column-analysis-style-content-left',    \
             'leader-work-head-left',                                        \
             'three-column-analysis-style-content-left']

# Example for 'wide_left_side_0em-two-column-analysis-style-content-left' is chapter 16, year 2002
# Example for 'leader-work-head-left' is chapter 12, year 2001

# A Text object is a header. Its content is the header itself, and the data is the information
# which uses the header.
class Text:
    def __init__(self, section = None, content = None, parent = None,   \
                 subsections = [], data = None):
        self.__section = section
        self.__content = content
        self.__parent = parent
        self.__subsections = subsections
        self.__data = data

    def __repr__(self):
        return 'OBJ' + self.get_section()

    def get_section(self):
        return self.__section

    def get_content(self):
        return self.__content

    def get_parent(self):
        return self.__parent

    def get_subsections(self):
        return self.__subsections

    def add_subsection(self, subsection):
        self.__subsections.append(subsection)

    def has_subsections(self):
        if len(self.__subsections) > 0:
            return True
        return False
    
    # Currently not being used...
    def has_parent(self):
        if self.__parent != None:
            return True
        return False

    def get_data(self):
        return self.__data

    def set_data(self, data):
        self.__data = data

    def has_data(self):
        if self.__data != None:
            return True
        return False

    def add_to_data(self, moreData):
        self.__data += '\n' + moreData


# This method will recursively go through all the elements of the hierarchy and print them
def printAll(e):
    objects = 0
    for thing in e:
        objects += 1
        post.write(thing.get_content() + '\n')
        if thing.has_data():
            post.write(thing.get_data() + '\n')
        post.write('\n')
        if thing.has_subsections():
            objects += printAll(thing.get_subsections())
    return objects


# This method cleans the lines of code so that there is no residual HTML
def remove_html(line):
    case1 = '<div class="wide_left_side-two-column-analysis-style-content-right">'
    case2 = '<div class="leader-work-head-right">'
    case3 = '<div class="leader-work-head-left">'
    case4 = '<div class="leader-work-left">'
    case5 = '<div class="leader-work-right">'

    if line.find(case1) != -1:
        line = line[:line.find(case1)] + ' - ' + line[line.find(case1) + len(case1):]

    if line.find(case2) != -1: # Header (right side)
        line = line[:line.find(case2)] + '\t\t|\t\t' + line[line.find(case2) + len(case2):]

    if line.find(case3) != -1: # Header (right side)
        line = line[:line.find(case3)] + '\n' + line[line.find(case3) + len(case3):]

    if line.find(case4) != -1: # Left data thing, new line
        line = line[:line.find(case4)] + '\n' + line[line.find(case4) + len(case4):]

    if line.find(case5) != -1: # Right data thing, separated by delimiter
        line = line[:line.find(case5)] + ' | ' + line[line.find(case5) + len(case5):]

    if line.find("<") == -1 or line.find(">", line.find("<") + 1) == -1:
        return line

    newLine = line[0:line.find("<")] + line[line.find(">", line.find("<") + 1) + 1:]

    return remove_html(newLine)


# This can be used to print the tag of a single Text object with the right indentation
def print_hierarchy(element):
    indentation = HIERARCHY[element.get_section()]
    result = ''

    for x in xrange(indentation):
        result += '    '

    result += (element.get_section() + '\n')

    return result


# This goes through |undesirables| and compares each of its elements with all the
# elements in |all_tags|. If there is a match found, as in something in |all_tags|
# is a part of something in |undesirables|, then |undesirables|' element is written
# into undesirables_locs.out.
def record_locs(undesirables, all_tags):
    with open('undesirables_locs.out', 'w') as locs:
        for undesirable in undesirables:
            for tag in all_tags:
                if undesirable.find(tag) != -1:
                    locs.write(undesirable + '\n')
                    break


# und(esirable)
# This grabs everything in undesirables_locs.out, gets rid of the identifiers and
# delimiters, and puts the new files into undesirables.out. Essentially shows the
# set of undesirable tags.
def record_no_locs():
    with open('undesirables.out', 'w') as no_locs:
        with open('undesirables_locs.out', 'r') as locs:
            und_no_locs = set()

            for und in locs:
                und_no_locs.add(und[und.find('::') + 2 : ])

            for und in und_no_locs:
                no_locs.write(und + '\n')


# Potentially desirable undesirables.
def pdu(undesirables):
    print '\nSearching for potentially desirable undesirables...'

    all_tags = []

    for tag in DATA_TYPE:
        all_tags.append(tag)

    for tag in HIERARCHY:
        all_tags.append(tag)

    record_locs(undesirables, all_tags)
    record_no_locs()

    print 'Finished generating undesirable lists.'




""" Here is where all the work starts """


if __name__ == '__main__':
    clear_console()
    print_beginning()

    # This represents the tags that are of no interest.
    undesirables = set()

    variate_yr_rng = make_variate_yr_rng()

    process_data(variate_yr_rng, undesirables)

    print_end()

    pdu(undesirables)


"""with open('undesirablesWithCertainty.out', 'r') as source:
    undesirablesWithCertainty = set()
    for e in source:
        undesirablesWithCertainty.add(e)
    with open('filteredUndesirables.out', 'w') as post:
        with open('filteredUndesirablesWithLocations.out', 'w') as wLoc:
            withoutLocations = set()
            withLocations = set()
            for e in undesirables:
                if e.find('<!--', e.find('::') + 2) == -1 and e.find('substructure-location', e.find('::') + 2) == -1 and e.find('/view.xhtml;jsessionid=', e.find('::') + 2) == -1: # These are restrictions to filer the results.
                    withoutLocations.add(e[e.find('::') + 2:])
                    withLocations.add(e)
            for e in withoutLocations - undesirablesWithCertainty: # Elements in wL but not in uWC
                post.write(e + '\n')
            for e in withLocations:
                if e[e.find('::') + 2:] in withoutLocations - undesirablesWithCertainty:
                    wLoc.write(e + '\n')"""
"""
# This stuff below is for the sole purpose of trying to find similar matches to currently known tags.

# |interestingTags| contains both |HIERARCHY| and |DATA_TYPE|.
interestingTags = []
for e in DATA_TYPE:
    interestingTags.append(e)
for e in HIERARCHY:
    interestingTags.append(e)

# This goes through |undesirables| and compares each of its elements with all the elements in |interestingTags|.
# If there is a match found, as in something in |interestingTags| is a part of something in |undesirables|, then
# |undesirables|' element is written into undesirablesWithLocations.out.
with open('undesirablesWithLocations.out', 'w') as post:
    for e in undesirables:
        for thing in interestingTags:
            if e.find(thing) != -1:
                post.write(e + '\n')
                break

# This grabs everything in undesirablesWithLocations.out, gets rid of the identifiers and delimiters, and puts
# the new files into undesirables.out. Essentially shows the set of undesirable tags.
with open('undesirables.out', 'w') as post:
    with open('undesirablesWithLocations.out', 'r') as source:
        normalSet = set()
        for e in source:
            normalSet.add(e[e.find('::') + 2:])
        for e in normalSet:
            post.write(e + '\n')
"""

