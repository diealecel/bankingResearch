# Diego Celis
# In the pursuit of making this thing work.

# TODO:
# 1. developing or incorporating a text comparison tool, and
# 2. figuring out a way to easily allow a user to compare texts from any given year
#    to any other given year, also providing information about changes made.

# The problem with this script seems to be that the files outputted have some small discrepancies.
# Most of them have to do with the type of symbols used. Common "differences" are those of normal
# quotes and smart quotes. There are also certain characters that don't translate well for some reason
# for this script that have no issues with the chapter-by-chapter approach. An example is the single
# quotation being represented as "&amp;apos;" instead of just "'". I believe that this issue
# may be caused by one of two reasons (or maybe even both!):
#     1. there is a difference in the unicode used in the sources (not my problem, but the coder's), or
#     2. for some reason fullSorter.py cannot correctly represent certain characters (but keep in mind that
#        it is using the same stuff as sorter.py, which represented them just fine, it seems).
# For the time being I'll go ahead and use sorter.py instead of this script, fullSorter.py.

import subprocess                   # Needed to clear the console window (and to use bash commands, not that they are needed).
import time                         # Needed to calculate the amount of time taken to run algorithms.
import httplib                      # Needed to catch IncompleteRead
from httplib import IncompleteRead  # Also needed to catch IncompleteRead
import urllib2                      # Needed to use URLError.
from urllib2 import URLError        # Needed to catch URLError.
import mechanize                    # Needed to use Browser.
from mechanize import Browser       # Needed to access websites.
from bs4 import BeautifulSoup       # Needed to read source code.

hierarchy = {'section-head':0,      \
             'subsection-head':1,   \
             'paragraph-head':2,    \
             'subparagraph-head':3, \
             'clause-head':4,       \
             'subclause-head':5,    \
             'subsubclause-head':6}

dataType = ['statutory-body',                                               \
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
        return 'OBJ' + self.getSection()

    def getSection(self):
        return self.__section

    def getContent(self):
        return self.__content

    def getParent(self):
        return self.__parent

    def getSubsections(self):
        return self.__subsections

    def addSubsection(self, subsection):
        self.__subsections.append(subsection)

    def hasSubsections(self):
        if len(self.__subsections) > 0:
            return True
        return False

    def hasParent(self):
        if self.__parent != None:
            return True
        return False

    def getData(self):
        return self.__data

    def setData(self, data):
        self.__data = data

    def hasData(self):
        if self.__data != None:
            return True
        return False

    def addToData(self, moreData):
        self.__data += '\n' + moreData

# This method will recursively go through all the elements of the hierarchy and print them
def printAll(e):
    objects = 0
    for thing in e:
        objects += 1
        post.write(thing.getContent() + '\n')
        if thing.hasData():
            post.write(thing.getData() + '\n')
        post.write('\n')
        if thing.hasSubsections():
            objects += printAll(thing.getSubsections())
    return objects

# This method cleans the lines of code so that there is no residual HTML
def cleanLineFromHTML(line):
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
    return cleanLineFromHTML(newLine)

# This can be used to print the tag of a single Text object with the right indentation
def printHierarchy(element):
    indentation = hierarchy[element.getSection()]
    result = ''
    for x in xrange(indentation):
        result += '    '
    result += (element.getSection() + '\n')
    return result

""" Here is where all the work starts """

# NOTE THAT THE YEAR ONLY GOES UP TO 2015, and the YEARS all start at 1994. ALSO "prelim" represents current year.

STARTING_YEAR = 1994
ENDING_YEAR = 2015
MINIMUM_LENGTH_OF_SOUP = 4000 # Received this value from testing the files with zero bytes.
STARTING_TIME = time.time()

EXCEPTIONS_FOR_LETTERS = [3861, 3865, 3869, 3873] # Received these values from testing the files with invalid URL's.

nothing = subprocess.call('clear', shell = True) # Clears the console window.
print "Welcome to Diego's Indexer v2f!\nFile processing is now starting.\n"

# This works as the header by which the program will show the files processed
print '{0:6}{1:9}{2:10}{3:10}{4}'.format('Year', 'Objects', 'Usage', 'Time (s)', 'Status')

# This represents the tags that are of no interest.
undesirables = set()

# This represents the variate years. Have to be made separately because 'prelim' has to be included.
variateYearRange = []
for x in range(ENDING_YEAR - STARTING_YEAR + 1):
    variateYearRange.append(str(STARTING_YEAR + x))
variateYearRange.append('prelim') # This is a special word used to reference the current year.

for variateYear in variateYearRange: # This creates [0, 1, ..., 20, 'prelim']
    # This represents the current time at which the process was initiated.
    timeStart = time.time()

    bankLawsSite = "http://uscode.house.gov/view.xhtml?hl=false&edition=" + variateYear + "&req=granuleid%3AUSC-prelim-title12"

    triedRetry = False
    retryNumber = 0

    # Retries if the first read doesn't work.
    while True:
        try:
            br = Browser()
            br.set_handle_robots(False) # I promise I'm not a robot.
            br.open(bankLawsSite)
            html = br.response().read()
            soup = BeautifulSoup(html, 'html.parser') # Collect HTML from site.
            if len(str(soup)) > MINIMUM_LENGTH_OF_SOUP or len(str(soup)) in EXCEPTIONS_FOR_LETTERS:
                break
            triedRetry = True
            retryNumber += 1
        except (urllib2.URLError, httplib.IncompleteRead) as error:
            # print "WOOPS! Successfully caught URLError."
            triedRetry = True
            retryNumber += 1

    # This represents the path to which the file will be saved.
    specimenName = 'fullResults/yr' + ('CURR' if variateYear == 'prelim' else variateYear) + '.out'
    sourceName = 'fullSources/yr' + ('CURR' if variateYear == 'prelim' else variateYear) + '.in'

    with open(sourceName, 'w') as source: # Write HTML onto a file.
        source.write(str(soup))

    # Contains all Text objects with section 'section-head'
    top = []

    validTag = 0
    invalidTag = 0
    # raise NameError('Hello!')

    with open(specimenName, 'w') as post:
        with open(sourceName, 'r') as source:
            for line in source:
                while True:
                    # Line below looks for the HTML tags. For example, consider the following:
                    # <h4 class="subsection-head">
                    #            ^^^^^^^^^^^^^^^
                    # This is what is being read from |source| and written into |post|.
                    # Of course, there are several cases in which what is written into |post| is not an HTML tag.
                    # The line below finds the first thing to be within quotes of the line.

                    potentialTag = line[line.find('"') + 1:line.find('"', line.find('"') + 1)]
                    if potentialTag == 'leader-work-head-left': # Special case, another tag is at end of line
                        contentWithinTags = line[line.find('>') + 1:line.rfind('<', 0, line.rfind('<'))]
                        lineTwo = line[line.rfind('<', 0, line.rfind('<')):]
                        neededRepeat = True
                    else:
                        contentWithinTags = line[line.find('>') + 1:line.rfind('</')]
                        neededRepeat = False

                    contentWithinTags = cleanLineFromHTML(contentWithinTags)
                    if potentialTag in hierarchy:
                        # post.write('prevElement is ' + str(prevElement) + '\n')
                        if potentialTag == 'section-head': # If |potentialTag| is 'section-head', then create a new Text object.
                            new = Text('section-head', contentWithinTags, None, [], None) # From end of first tag to beginning of ending tag.
                            top.append(new) # |top| contains all 'section-head' Text objects.
                        # If |prevElement| has a hierarchy right above that of |potentialTag|...
                        elif hierarchy[potentialTag] > hierarchy[prevElement.getSection()]:
                            new = Text(potentialTag, contentWithinTags, prevElement, [], None)
                            prevElement.addSubsection(new)
                        elif hierarchy[potentialTag] == hierarchy[prevElement.getSection()]:
                            new = Text(potentialTag, contentWithinTags, prevElement.getParent(), [], None)
                            prevElement.getParent().addSubsection(new)
                        else: # Implicit hierarchy[potentialTag] < hierarchy[prevElement.getSection()]
                            difference = hierarchy[prevElement.getSection()] - hierarchy[potentialTag] + 1 - (hierarchy[prevElement.getSection()] - hierarchy[prevElement.getParent().getSection()] - 1) # Plus one because you need an additional iteration to reach correct parent. # The minus element is to correct for discrepancies in hierarchy (maybe there's a skip of a hierarchical level)
                            for x in xrange(difference):
                                prevElement = prevElement.getParent()
                            new = Text(potentialTag, contentWithinTags, prevElement, [], None)
                            prevElement.addSubsection(new)
                        prevElement = new

                        validTag += 1
                    # This implements data into the objects.
                    elif potentialTag in dataType:
                        try:
                            prevElement
                        except NameError:
                            invalidTag += 1
                        else:
                            if not prevElement.hasData():
                                prevElement.setData(contentWithinTags)
                            else:
                                prevElement.addToData(contentWithinTags)
                            validTag += 1
                    else:
                        # Essentially, if no tag is found or anything then this "else" runs.
                        # Keep note of how there is a delimiter that allows for ease of searching inserted before |potentialTag|.
                        undesirables.add(variateYear + '::' + potentialTag)
                        invalidTag += 1
                    if not neededRepeat:
                        break
                    else:
                        neededRepeat = False
                        line = lineTwo

        # Anything after this line is after the source.in has already been read and |top| has been constructed.
        numberOfObjects = printAll(top)

        # Determine the status of the process.
        if numberOfObjects > 0 and not triedRetry:
            status = 'SUCCESSFUL'
        elif numberOfObjects > 0 and triedRetry:
            status = 'SUCCESSFUL RETRY #' + str(retryNumber)
        else:
            status = 'FAILED'
        print '{0:6}{1:9}{2:10}{3:10}{4}'.format('CURR' if variateYear == 'prelim' else variateYear, str(numberOfObjects), str(round(validTag / float(validTag + invalidTag) * 100, 4)) + '%', str(round(time.time() - timeStart, 4)), status)

print '\nEntire process finished, taking ' + str(time.time() - STARTING_TIME) + ' seconds.'

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

# This stuff below is for the sole purpose of trying to find similar matches to currently known tags.

# |interestingTags| contains both |hierarchy| and |dataType|.
interestingTags = []
for e in dataType:
    interestingTags.append(e)
for e in hierarchy:
    interestingTags.append(e)

# This goes through |undesirables| and compares each of its elements with all the elements in |interestingTags|.
# If there is a match found, as in something in |interestingTags| is a part of something in |undesirables|, then
# |undesirables|' element is written into undesirablesWithLocations.out.
with open('fullUndesirablesWithLocations.out', 'w') as post:
    for e in undesirables:
        for thing in interestingTags:
            if e.find(thing) != -1:
                post.write(e + '\n')
                break

# This grabs everything in undesirablesWithLocations.out, gets rid of the identifiers and delimiters, and puts
# the new files into undesirables.out. Essentially shows the set of undesirable tags.
with open('fullUndesirables.out', 'w') as post:
    with open('fullUndesirablesWithLocations.out', 'r') as source:
        normalSet = set()
        for e in source:
            normalSet.add(e[e.find('::') + 2:])
        for e in normalSet:
            post.write(e + '\n')
