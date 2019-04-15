import sys
import random
from datetime import date
from datetime import datetime
from enum import Enum

## Search 'Rewrite' for whatever I was doing earlier
## Also, rewrite expense and the other classes to use dictionaries for fields; since I'm using
## them for saving/loading anyway, it's more concise.

## TODO Get it to print a list of bills.
## TODO Get it to interpret commands, such as 'add' and 'rem'

class Program:
    
    separatorChar = '`'
    IDs = []

    curDate = None
    projectionDate = None
    budgetItems = []
    budgetPeriod = []       # I have no idea what this was supposed to be for

    arg = sys.argv
    datafilePath = "C:\\Users\\xpgra\\Home\\Scripts\\Data\\budgetboy_data"      # Can I use relative path?

    def __init__(self):
        dt = datetime.now()
        self.curDate = DueDate(dt.day, dt.month, dt.year)
        self.projectionDate = self.curDate + Time(months=4)
        
    def run(self):
        self.load()         # Loads all the data that there is
        self.update()       # Updates the list of data with the current date
        self.sort()         # Sorts the list of data by relevance (soonest and largest due)
        self.userInput()    # Interprets user arguments, does something
        self.clean()        # Cleans the list of data of invalid or broken entries, warning the user
        self.save()         # Saves the final list of data to a file, backing up the old one

    # Saves the list of bills and income in a handy-dandy file
    def save(self):
        self.backup()

        ## Open the data file
        f = open(self.datafilePath, 'w')

        ## Write all header fields into one line using the separator char.
        for term in Terms:
            f.write(term + program.separatorChar)
        f.write("\n")

        ## Write each budget item as a line, following the format of the header fields, using the separator char.
        for b in self.budgetItems:
            for term in Terms:
                f.write(b.fields[term] + program.separatorChar)
            f.write("\n")
        
        ## Close the data file
        f.close()

    # Backs up the "old" datafile before saving a new one.
    def backup(self):
        ## Open 'from' file and 'to' file
        r = open(self.datafilePath, 'r')
        w = open(self.datafilePath + "_bk", 'w')

        ## Back 'em up
        for line in r.readlines():
            w.write(line)

        ## Close
        r.close()   # (Close)
        w.close()   # close the file

    def load(self):
        ## Open the datafile
        try:
            f = open(self.datafilePath, 'r')
        except FileNotFoundError:
            return      # Nothing to read here

        ## read first line, should be the DB header
        line = f.readline()

        ## verify its terms are.. correct?
        if line:
            for term in Terms:
                if not line.find(str(term)):    # TODO I guess I should demand they also be the only fields... I dunno.
                    raise Exception("File appears to be corrupt: file content does not match expected format.")
        
        ## Break the header line into discrete pieces
        n = 0
        columnNames = []
        while n < len(line):
            columnNames.append(line[n:line.find(program.separatorChar, n)])
            n = line.find(program.separatorChar, n) + len(program.separatorChar)

        ## Iterate over the proceeding lines, parsing them by the separator char
        ## (Also, remove the \n before iteration)
        while line:
            line = f.readline()
            line = line[0:line.find('\n')]
            e = Expense()
            
            ## Add each piece of data to the dictionary key associated.
            n = 0
            for i in range(0, len(columnNames)):
                term = Terms.fromString(columnNames[i])
                e.fields[term] = line[n:line.find(self.separatorChar, n)]
                n = line.find(self.separatorChar, n) + len(self.separatorChar)
            
            # Reconfigure strings into their prospective types
            try:
                # AMOUNT
                e.fields[Terms.AMOUNT] = int(e.fields[Terms.AMOUNT])

                # DDATE
                dd = DueDate()
                dd.fromString(e.fields[Terms.DDATE])
                e.fields[Terms.DDATE] = dd

                # TDATE, which may be 'None' anyway
                if e.fields[Terms.TDATE] != 'None':
                    td = DueDate()
                    td.fromString(e.fields[Terms.TDATE])
                else:
                    td = None
                e.fields[Terms.TDATE] = td

                # PERIOD and IMPORTANT
                e.fields[Terms.PERIOD] = Period.fromString(e.fields[Terms.PERIOD])
                e.fields[Terms.IMPORTANT] = (e.fields[Terms.IMPORTANT] == "True")
            except ValueError:
                pass    # TODO This should never happen, but it would be cool if I passed this object to
                        # a list of misfits, and then displayed that list of troublemakers to the user.
            
            # Verify the object, and add it to memory
            if e.valid():
                self.IDs.append(e.fields[Terms.ID])
                program.budgetItems.append(e)
            else:
                raise Exception("Data is corrupt; one of the read items did not validate correctly.")
                # TODO Same as the above: pass it to a list, present the list of troublemakers
        
        # Finish
        f.close()

    ## Cleans the list of expenses of invalid or broken entries. Notifies the user by printing everything
    # known about these items in-line.
    def clean(self):
        toRemove = []       # List of all budgetItem elements to delete (by index)
        silentRemove = []   # The same, but without report; reason for deletion is innocuous.

        # Iterate through the entire list of budget items
        for i in range(0, len(self.budgetItems)):
            item = self.budgetItems[i]

            # If they self-report as invalid, report to the user and mark for deletion
            if item.validate() == False:
                s = "Deleted >> "
                for term in Terms:
                    s = s + str(item.fields[term]) + " : "
                s = s[0:len(s)-2]
                print(s)
                toRemove.append(i)

            # If the item has not been relevant for longer than 1 year, delete silently.
            if (item.fields[Terms.TDATE] != None and
                item.fields[Terms.TDATE] < (self.curDate - Time(years=1))):
                silentRemove.append(i)

        # Report to the user how many items were deleted, and delete them.
        if len(toRemove) > 0:
            print("Removed {} broken budget items.".format(len(toRemove)))
            print()
            for i in toRemove:
                self.budgetItems.pop(i)
        
        # Silently delete old listings
        for i in range(0, len(silentRemove)):
            self.budgetItems.pop(i)

    ## Sorts the list by their duedate (soonest), then amount (biggest), then name.
    ## Well, the .compare() method does.
    def sort(self):
        if len(self.budgetItems) > 1:
            for i in range(1, len(self.budgetItems)):
                k = i
                j = i - 1
                while j > -1 and self.budgetItems[k].compare(self.budgetItems[j]) == -1:
                    tmp = self.budgetItems[j]
                    self.budgetItems[j] = self.budgetItems[k]
                    self.budgetItems[k] = tmp
                    j -= 1
                    k -= 1
    
    ## Update due dates to their next occurrence from the present
    def update(self):
        for item in self.budgetItems:
            while (item.fields[Terms.PERIOD] != Period.Singular and
                   item.fields[Terms.DDATE] < self.curDate):
                item.fields[Terms.DDATE].advancePeriod(item.fields[Terms.PERIOD])

    ## Interprets the user's arguments to the program as actionable.. actions.
    def userInput(self):
        pass
        # TODO bby wrk on ths
        # I am going to bed.
        # This thing is finally almost done for real now.
        # The last thing to do (and I really think the logic is fine--no errors) is to
        # actually write down ways the program will collect user input and data,
        # and display its internal list.
        # Almost a big step unto itself.
        # It may take me some hours.
        # I hope not too many.
        # The basic 'listadd' , 'listdisplay' functionality ought to be easy enough.

    ## Generates a new ID for a new income/expense object.
    def newID(self):
        if len(self.IDs) < 999:
            done = False
            while not done:
                newID = random.randint(1,1000)
                done = True
                for ID in self.IDs:
                    if int(ID) == newID:
                        done = False
                        break
            return "{:03d}".format(newID)
        else:
            raise Exception("There are no available IDs to give out; update code to allow 4 digits?")

class Expense:

    def __init__(self, fields={}):
        self.fields = fields
        
    # Returns true if all required fields are filled in and with correct data.
    def valid(self):
        t1 = False
        t2 = False

        # TDATE isn't critical, so if it's invalid, just get rid of it.
        if (type(self.fields[Terms.TDATE]) != DueDate or
            self.fields[Terms.TDATE].valid() == False):
            self.fields[Terms.TDATE] == None

        # Confirm all fields are the correct type.
        if (type(self.fields[Terms.NAME]) == str and
            type(self.fields[Terms.ID]) == str and
            type(self.fields[Terms.AMOUNT]) == int and
            type(self.fields[Terms.PERIOD]) == Period and
            type(self.fields[Terms.DDATE]) == DueDate and
            type(self.fields[Terms.IMPORTANT]) == bool):
            t1 = True

        # Confirm all fields have legal values.
        if (self.fields[Terms.NAME] != "" and
            between(int(self.fields[Terms.ID]), 0, 1000) and
            self.fields[Terms.AMOUNT] > 0 and
            Period.valid(self.fields[Terms.PERIOD]) and
            self.fields[Terms.DDATE].valid()):
            t2 = True

        return t1 and t2

    # Returns a formatted line considered this expense object's 'formal display'
    def display(self):
        s = "" + self.fields[Terms.DDATE].get(self.lastPayment())
        s = s + ' {:50}'.format(self.fields[Terms.NAME]) + (' **' if self.fields[Terms.IMPORTANT] else '   ')
        s = s + (' ' * 4) + "{:>8}".format(self.amountStr())

    # Returns this expense's amount as a string in currency format
    def amountStr(self):
        sign = '-' if self.fields[Terms.AMOUNT] < 0 else '+'
        return sign + '$' + str(abs(self.fields[Terms.AMOUNT]))

    # Returns this expense's amount as an int
    def amount(self):
        return self.fields[Terms.AMOUNT]
    
    # Rolls the due-date forward by one payperiod.
    # 'budgetboy -p [name|id]' or 'budgetboy -rf [name|id]' do this as well, if the bill has been payed.
    def rollForward(self):
        self.fields[Terms.DDATE] = self.fields[Terms.DDATE].advancePeriod(self.fields[Terms.PERIOD])
    
    # Rolls the due-date backward by one payperiod.
    # This function does not take into account real bill history, it only projects backward in time.
    def rollBack(self):
        self.fields[Terms.DDATE] = self.fields[Terms.DDATE].recedePeriod(self.fields[Terms.PERIOD])
    
    # This schedules the cancellation of a bill. If cancelled on its due-date, the bill is considered valid through the next payperiod.
    # If the bill has passed its expiration, it will remain in the record for 1 year before being removed.
    def terminateOn(self, date):
        if not isinstance(date, DueDate):
            raise TypeError("expected a DueDate object, got {}".format(type(date)))
        b = False
        if date.valid():
            self.fields[Terms.TDATE] = date
            b = True
        return b
    
    # Used to revive a terminated bill that still exists in the record.
    # Records are cleared of an expense 1 year after their termination date.
    def revive(self):
        self.fields[Terms.TDATE] = None
        while (self.fields[Terms.DDATE] < program.curDate):
            self.rollForward()

    # Returns True if this item has run its expiration date. The expiration date is the last date the bill is still valid.
    def expired(self):
        return self.fields[Terms.DDATE] > self.fields[Terms.TDATE]

    # Returns true if this is the last occurrence of this payment, meaning the next period interval lies
    # beyond the termination date.
    def lastPayment(self):
        d = self.fields[Terms.DDATE].clone()
        return d.advancePeriod() > self.fields[Terms.TDATE]
    
    # Returns true if the given var represents an instance of Expense (this class)
    def verifyOther(self, other):
        return isinstance(other, Expense)
    
    # Returns 1 if this object comes logically after the 'other' in ordering, -1 if before, 0 if indeterminate.
    def compare(self, other):
        if not self.verifyOther(other):
            raise TypeError("expected {} object, recieved {}".format(type(self), type(other)))
        val = self.fields[Terms.DDATE].compare(other.fields[Terms.DDATE])
        if val == 0: val = 1 if self.fields[Terms.AMOUNT] > other.fields[Terms.AMOUNT] else (-1 if self.fields[Terms.AMOUNT] < other.fields[Terms.AMOUNT] else 0)
        if val == 0: val = 1 if self.fields[Terms.NAME] > other.fields[Terms.NAME] else (-1 if self.fields[Terms.NAME] < other.fields[Terms.NAME] else 0)
        return val
    
    # Returns a copy of this instance.
    def clone(self):
        e = Expense()
        for term in Terms:
            e.fields[term] = self.fields[term]
        e.fields[Terms.DDATE] = self.fields[Terms.DDATE].clone()
        e.fields[Terms.TDATE] = self.fields[Terms.TDATE].clone()
        return e
    
class DueDate:

    def __init__(self, day=1, month=1, year=1):
        self.day = day
        self.month = month
        self.year = year
        self.assertValidity()
    
    def __str__(self):
        return "{:02d}-{:02d}-{}".format(self.day, self.month, self.year)
    
    def __eq__(self, o):
        if not isinstance(o, DueDate):
            raise TypeError("expected a DueDate object, recieved {}".format(type(o)))
        day = self.effectiveDate()
        oday = o.effectiveDate()
        return day == oday and self.month == o.month and self.year == o.year
        
    def __gt__(self, o):
        day = self.effectiveDate()
        oday = o.effectiveDate()
        b = self.year > o.year
        if not b: b = self.month > o.month
        if not b: b = day > oday
        return b
        
    def __ge__(self, o):
        return self.__eq__(o) or self.__gt__(o)
        
    def __lt__(self, o):
        day = self.effectiveDate()
        oday = o.effectiveDate()
        b = self.year < o.year
        if not b: b = self.month < o.month
        if not b: b = day < oday
        return b
    
    def __le__(self, o):
        return self.__eq__(o) or self.__lt__(o)
    
    def __add__(self, o):
        d = self.clone()
        d.addTime(o)
        return d
    
    def __iadd__(self, o):
        self.addTime(o)
    
    def __sub__(self, o):
        d = self.clone()
        d.addTime(o)
        return d
    
    def __isub__(self, o):
        self.addTime(o)
    
    def compare(self, o):
        if not isinstance(o, DueDate):
            raise TypeError("expected a DueDate object, recieved {}".format(type(o)))
        return 1 if self > o else (-1 if self < o else 0)
    
    def clone(self):
        d = DueDate(self.day, self.month, self.year)
        return d

    def fromString(self, s):
        # expects 'xx-xx-xxxx'
        ls = s.split('-')

        if len(ls) != 3:
            raise Exception("Cannot read date from string: str = " + s)

        self.day = int(ls[0])
        self.month = int(ls[1])
        self.year = int(ls[2])

        self.assertValidity()

    def checkType(self, o):
        if not isinstance(o, Time):
            raise TypeError("expected a Time object, recieved {}".format(type(o)))
    
    def addTime(self, time):
        self.checkType(time)

        # Resolve months and years first.
        self.year += time.years
        self.month += time.months

        # Overflow months-out-of-range into years
        while self.month < Month.minimum:
            self.month += Month.maximum
            self.year -= 1
        while self.month > Month.maximum:
            self.month -= Month.maximum
            self.year += 1
        
        # If days are being added/subtracted, then throw out the idealized date.
        if time.days != 0:
            self.day = self.effectiveDate() # Calc from a real point in time in the resulting month
            self.day += time.days

            # Overflow days-out-of-range into months into years
            while self.day < Month.daysMin:
                self.month -= 1
                if self.month < Month.minimum:
                    self.month = Month.maximum
                    self.year -= 1
                self.day += Month.length(self.month)
            while self.day > Month.length(self.month):
                self.day -= Month.length(self.month)
                self.month += 1
                if self.month > Month.maximum:
                    self.month = Month.minimum
                    self.year += 1
        
        # Enforce a minimum date; no A.C./B.C. here.
        if self.year < 1:
            self.year = 1
            self.month = 1
            self.day = 1

    ## Throws an exception if, for whatever reason, this date object is illegitimate
    def assertValidity(self):
        if not self.valid():
            raise Exception("Date object is malconfigured: {}".format(self))
    
    ## Allows me to project forward in time by relative due date
    def advancePeriod(self, period):
        d = self.clone()
        if period == Period.Weekly: d += Time(days=7)
        elif period == Period.BiWeekly: d += Time(days=14)
        elif period == Period.Monthly: d += Time(months=1)
        elif period == Period.Annually: d += Time(years=1)
        return d

    ## So that I can project backward, too, for whatever reason
    def recedePeriod(self, period):
        d = self.clone()
        if period == Period.Weekly: d -= Time(days=7)
        elif period == Period.BiWeekly: d -= Time(days=14)
        elif period == Period.Monthly: d -= Time(months=1)
        elif period == Period.Annually: d -= Time(years=1)
        return d
    
    def get(self, star=False):
        string = "{0} {1:02d}".format(Month.name(self.month), self.effectiveDate())
        if star: string += '*'
        else: string += ' '
        return string
    
    def getFull(self, star=False):
        string = self.get() + ', ' + str(self.year)
        if star: string += '*'
        else: string += ' '
        return string
    
    # Returns a date limited by the current month length, but maintaining the current month
    def effectiveDate(self):
        return min(self.day, Month.length(self.month))

    def valid(self):
        b = False
        if (between(self.year, 0, 10000) and
            within(self.month, Month.minimum, Month.maximum) and
            within(self.day, Month.daysMin, Month.daysMax)):
            b = True
        return b
        
class Time:
    
    def __init__(self, days=0, months=0, years=0):
        self.day = days
        self.month = months
        self.year = years
    
class Period(Enum):
    Singular = 1
    Weekly = 2
    BiWeekly = 3
    Monthly = 4
    Annually = 5

    # Return true if the given n can be associated with any legitimate value of Period
    # I'll be honest, though, no idea when I used this.
    @staticmethod
    def valid(n):
        if type(n) != int:
            raise Exception("Cannot validate parameter against enum values with {}".format(type(n)))
        return (within(n, 1, len(Period)))
    
    # Return an Enum value equal to its name as a string
    @staticmethod
    def fromString(s):
        for p in Period:
            if str(p) == s:
                return p
        return None
    
class Month:
    maximum = 12
    minimum = 1
    daysMax = 31
    daysMin = 1
    names =   {0:'Nul', 1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
    lengths = {names[0]:0, names[1]:31, names[2]:28, names[3]:31, names[4]:30, names[5]:31,
               names[6]:30, names[7]:31, names[8]:31, names[9]:30, names[10]:31, names[11]:30,
               names[12]:31}
    
    @classmethod
    def name(cls, numeral):
        if numeral < 1 or numeral > cls.maximum:
            raise OverflowError("Value given is out of bounds; recieved {}".format(numeral))
        return cls.names[numeral]
        
    @classmethod
    def length(cls, numeral):
        if numeral < 1 or numeral > cls.maximum:
            raise OverflowError("Value given is out of bounds; recieved {}".format(numeral))
        return cls.lengths[cls.names[numeral]]

class Terms(Enum):
    NAME = 0
    ID = 1
    AMOUNT = 2
    DDATE = 3
    TDATE = 4
    PERIOD = 5
    IMPORTANT = 6

    # Return an Enum value equal to its own name as a string
    @staticmethod
    def fromString(s):
        for term in Terms:
            if str(term) == s:
                return term
        return None

# Returns true if n is in the interval min to max, inclusive
def within(n, min, max):
    return (n >= min and n <= max)

# Retruns true if n is in the interval min to max, exclusive
def between(n, min, max):
    return (n > min and n < max)

## Here's the epics:
program = Program()
program.run()
