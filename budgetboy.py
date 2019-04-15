import sys
from datetime import date
from datetime import datetime
from enum import Enum

## Search 'Rewrite' for whatever I was doing earlier
## Also, rewrite expense and the other classes to use dictionaries for fields; since I'm using
## them for saving/loading anyway, it's more concise.

## TODO Make sure save() backups the old file somewhere.
## TODO Get it to print a list of bills.
## TODO Get it to interpret commands, such as 'add' and 'rem'

class Program:
    
    self.separatorChar = '`'
    self.curDate

    header = [Terms.NAME, Terms.ID, Terms.AMOUNT, Terms.DDATE, Terms.TDATE, Terms.PERIOD, Terms.IMPORTANT]

    def __init__(self):
        dt = datetime.now()
        self.curDate = DueDate(dt.day, dt.month, dt.year)
        projectionDate = self.curDate += Time(months=4)
        budgetItems = []
        budgetPeriod = []

        arg = sys.argv
        datafilePath = "C:\\Users\\xpgra\\Home\\Scripts\\Data\\budgetboy_data"

    def run():
        
        ## Load from file
        try:
            file.open(datafilePath, 'x')
        except FileExistsError:
            pass
        
        f = file.open(datafilePath, 'r')
        
        ## Here's the part that does all the heavy lifting.
        ## I'm trying to get it to work, so I haven't added ~any~ safety bounds for the
        ## interpreter to work within (i.e. if the data doesn't match... oh well)
        line = True
        while line:
            line = f.readline()
            line = line[0:line.find('\n')]  ## Removes the annoying newline char
            
            ## Parse the loaded line and break it into discrete chunks
            data = []
            s = 0
            e = 0
            while s < len(line):
                e = line.find('`', s)
                if e == -1: e = len(line)
                data.append(line[s:e])
                s = e + 1
            line = f.readline()     ## Allows the grander while loop to continue
            
            ## Interpret the data
            ddate = None
            expense = None
            n = 3       ## Bandaid: If ddate is None, shift all other data entry indices by n much 4->1 5->2
            if data[0] != "--":
                ddate = DueDate(int(data[0]), int(data[1]), int(data[2]))
                ddate.duedate = int(data[3]) if data[3] != '--' else None
                n = 0
            expense = Expense(data[4-n], int(data[5-n]), ddate, Period[data[6-n]], True if data[7-n] == '1' else False)
            if data[8-n] != '--':
                tdate = DueDate(int(data[8-n]), int(data[9-n]), int(data[10-n]))
                expense.terminationDate = tdate
            
            budgetItems.append(expense)
            line = f.readline()
        
        f.close
        
        ## Iterate over list
        ##     Advance the period for all duedates until they are valid
        for item in budgetItems:
            while item.date < curDate:
                item.advancePeriod()
    
    ## Searchable: [Main() Rewrite]

    def save(self):
        ## Open the data file
        ## Also, I'm doing the try/except block because.. of paranoia, I think. Is it even necessary?
        try:
            f = open(program.datafile, 'x')
        except FileExistsError:
            pass
        f = open(program.datafile, 'w')

        ## Write all header fields into one line using the separator char.
        for h in program.header:
            f.write(h + program.separatorChar)
        f.write("\n")

        ## Write each budget item as a line, following the format of the header fields, using the separator char.
        for b in budgetItems:
            for key in program.header:
                f.write(b.fields[key] + program.separatorChar)
            f.write("\n")
        
        ## Close the data file
        f.close()

    def load(self):
        ## Open the datafile
        try:
            f = open(program.datafile, 'x')
        except FileExistsError:
            pass
        f = open(program.datafile, 'r')

        ## read first line, should be the DB header
        line = f.readline()

        ## verify its terms are.. correct?
        if line:
            for h in program.header:
                if not line.find(h):    # TODO I guess I should demand they also be the only fields... I dunno.
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
                e.fields[columnNames[i]] = line[n:line.find(program.separatorChar, n)]
                n = line.find(program.separatorChar, n) + len(program.separatorChar)
            
            # Reconfigure strings into integers ~if possible~
            # TODO This should probably be done ~in~ the Expense object.
            try:
                e.fields[Terms.AMOUNT] = int(e.fields[Terms.AMOUNT])
            except ValueError:
                pass
            
            # Verify the object, and add it to memory
            if e.validate():    # .hardValidate()
                program.budgetItems.append(e)
            else
                raise Exception("Data is corrupt; one of the read items did not validate correctly.")

            # TODO Add .hardValidate() to Expense objects; raise an error when data doesn't conform.
            # This method will confirm the right kind of data, the right number of fields, etc.
        
        # Finish
        f.close()
    
    ## Sort list
    def sort(self):
        if len(budgetItems) > 1:
            for i in range(1, len(budgetItems)):
                k = i
                j = i - 1
                while j > -1 and budgetItems[k].compare(budgetItems[j]) == -1:
                    tmp = budgetItems[j]
                    budgetItems[j] = budgetItems[k]
                    budgetItems[k] = tmp
                    j -= 1
                    k -= 1

class Expense:

    ## Rewrite
    # I think I'm done here... I need to finish writing Program, now.

    # For reference:
    # Fields: name, id, amount, ddate, tdate, payperiod, important

    ## Program will have to assign IDs to expense and income objects;
    ## each one needs to be unique, there's no way to verify that without access to the global list.
    # id, in case I forget, is calculated thusly:
    #     01 -- 99 (in order of creation), + 1 random digit.
    #     ex: 017 023 039 041
    # The extra digit helps prevent accidental reference, I pretend is the reason.
    # These id's are saved in the record, and become each item's "second name" for ease of use purposes.

    def __init__(self, fields={}}):
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
            int(self.fields[Terms.ID]) > 0 and
            int(self.fields[Terms.ID]) <= 999 and
            self.fields[Terms.AMOUNT] > 0 and
            Period.valid(self.fields[Terms.PERIOD]) and
            self.fields[Terms.DDATE].valid()):
            t2 = True

        return t1 and t2

    # Returns this expense's amount as a string in currency format
    def amountStr(self):
        return '-$' + str(self.fields[Terms.AMOUNT])

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
    
    # Returns true if the given var represents an instance of Expense (this class)
    def verifyOther(self, other):
        return isinstance(other, Expense)
    
    # Returns 1 if this object comes logically after the 'other' in ordering, -1 if before, 0 if indeterminate.
    def compare(self, other):
        if not verifyOther(other):
            raise TypeError("expected {} object, recieved {}".format(type(self), type(other)))
        val = self.fields[Terms.DDATE].compare(other.fields[Terms.DDATE])
        if val == 0: val = 1 if self.fields[Terms.AMOUNT] > other.fields[Terms.AMOUNT] else (-1 if self.fields[Terms.AMOUNT] < other.fields[Terms.AMOUNT] else o)
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

class Income(Expense):
    
    # Returns this income's amount as a string in currency format
    def string(self):
        return '+$' + str(self.fields[Terms.AMOUNT])
    
    # Verifies that the given object is an Income object
    def verifyOther(self, other):
        return isinstance(other, Income)
    
    # Returns a copy of this instance.
    def clone(self):
        i = Income()
        for term in Terms:
            i.fields[term] = self.fields[term]
        i.fields[Terms.DDATE] = self.fields[Terms.DDATE].clone()
        i.fields[Terms.TDATE] = self.fields[Terms.TDATE].clone()
        return i
    
class DueDate:

    def __init__(self, day, month, year, strictDate=True):
        self.day = day
        self.month = month
        self.year = year
        self.duedate = day if strictDate else None
        self.assertFormat()     ## I could throw an OutOfBoundsd Error, but... I dunno.
    
    def __eq__(self, o):
        if not isinstance(o, DueDate):
            raise TypeError("expected a DueDate object, recieved {}".format(type(o)))
        day = self.day if self.duedate == None else self.duedate
        oday = o.day if o.duedate == None else o.duedate
        return day == oday and self.month == o.month and self.year == o.year
        
    def __gt__(self, o):
        day = self.day if self.duedate == None else self.duedate
        oday = o.day if o.duedate == None else o.duedate
        b = self.year > o.year
        if not b: b = self.month > o.month
        if not b: b = day > oday
        return b
        
    def __ge__(self, o):
        return self.__eq__(o) or self.__gt__(o)
        
    def __lt__(self, o):
        day = self.day if self.duedate == None else self.duedate
        oday = o.day if o.duedate == None else o.duedate
        b = self.year < o.year
        if not b: b = self.month < o.month
        if not b: b = day < oday
        return b
    
    def __le__(self, o):
        return self.__eq__(o) or self.__lt__(o)
    
    def __add__(self, o):
        self.checkType(o)
        d = DueDate(self.day + o.day, self.month + o.month, self.year + o.year)
        d.assertFormat()
        return d
    
    def __iadd__(self, o):
        self.checkType(o)
        self.day += o.day
        self.month += o.month
        self.year += o.year
        self.assertFormat()
    
    def __sub__(self, o):
        self.checkType(o)
        d = DueDate(self.day - o.day, self.month - o.month, self.year - o.year)
        d.assertFormat()
        return d
    
    def __isub__(self, o):
        self.checkType(o)
        self.day -= o.day
        self.month -= o.month
        self.year -= o.year
        self.assertFormat()
    
    def compare(self, o):
        if not isinstance(o, DueDate):
            raise TypeError("expected a DueDate object, recieved {}".format(type(o)))
        return 1 if self > o else (-1 if self < o else 0)
    
    def clone(self):
        d = DueDate(self.day, self.month, self.year)
        d.duedate = self.duedate
        return d
    
    def checkType(self, o):
        if not isinstance(o, Time):
            raise TypeError("expected a Time object, recieved {}".format(type(o)))
    
    def assertFormat(self):
        ## Frontload all 'extra time' into the day field
        self.day += self.month // Month.maximum * 365
        self.month = (self.month % Month.maximum) + 1
    
        ## Filter time through the other fields if days are far too many
        while self.day > Month.length(self.month):
            self.day -= Month.length(self.month)
            self.month += 1
            if self.month > Month.maximum:
                self.month -= Month.maximum
                self.year += 1
        
        ## Filter time through the other fields if days are negative
        while self.day < Month.daysMin:
            self.day += Month.length(self.month)
            self.month -= 1
            if self.month < Month.minimum:
                self.month += Month.maximum
                self.year -= 1
                
        ## Duedate time objects only "need" to advance through their pay-periods, so if a strictly-defined
        ## pay-period exists, set this object's day to that time.
        if self.duedate: self.day = self.setWithinMonth(self.duedate)
    
    ## Allows me to project forward in time by relative due date
    def advancePeriod(self, period):
        d = self.clone()
        if period == Period.Weekly: d += Time(days=7)
        elif period == Period.BiWeekly: d += Time(days=14)
        elif period == Period.Monthly: d += Time(months=1)
        elif period == Period.Annually: d += Time(years=1)
        d.assertFormat()
        return d

    ## So that I can project backward, too, for whatever reason
    def recedePeriod(self, period):
        d = self.clone()
        if period == Period.Weekly: d -= Time(days=7)
        elif period == Period.BiWeekly: d -= Time(days=14)
        elif period == Period.Monthly: d -= Time(months=1)
        elif period == Period.Annually: d -= Time(years=1)
        d.assertFormat()
        return d
    
    def get(self, star=False):
        day = self.day if self.duedate == None else self.duedate
        string = "{0} {1:02}".format(Month.names(self.month), self.setWithinMonth(self.day))
        if star: string += '*'
        else: string += ' '
        return string
    
    def getFull(self, star=False):
        string = self.get() + ', ' + str(self.year)
        if star: string += '*'
        else: string += ' '
        return string
    
    ## The intent with this method is that monthly payments on 'missing' days for certain
    ## months (i.e. 31) will simply 'move' to the 30th or whenever for that month instead.
    def setWithinMonth(self, day)
        if day > Month.length(self.month):
            day = Month.length(self.month)
        return day
    
    def valid(self):
        b = False
        if (self.year > 0 and
            self.year < 10000 and
            self.month >= Month.minimum and
            self.month <= Month.maximum and
            self.day >= Month.daysMin and
            self.day <= Month.daysMax):
            b = True
        return b
        
class Time:
    
    def __init__(self, days=0, months=0, years=0)
        self.day = days
        self.month = months
        self.year = years
    
class Period(Enum):
    Singular = 1
    Weekly = 2
    BiWeekly = 3
    Monthly = 4
    Annually = 5

    # Return true
    def valid(n):
        if type(n) != int:
            raise Exception("Cannot validate parameter against enum values with {}".format(type(n)))
        return (within(n, 1, len(Period)))
    
class Month:
    maximum = 12
    minimum = 1
    daysMax = 31
    daysMin = 1
    names =   {0:'Nul', 1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
    lengths = {self.names[0]:0, self.names[1]:31, self.names[2]:28, self.names[3]:31, self.names[4]:30, self.names[5]:31,
               self.names[6]:30, self.names[7]:31, self.names[8]:31, self.names[9]:30, self.names[10]:31, self.names[11]:30,
               self.names[12]:31}
    
    def name(numeral):
        if numeral < 1 or numeral > maximum:
            raise OverflowError("Value given is out of bounds; recieved {}".format(numeral))
        return names[numeral]
        
    def length(numeral):
        if numeral < 1 or numeral > maximum:
            raise OverflowError("Value given is out of bounds; recieved {}".format(numeral))
        return length[names[numeral]]

class Terms:
    self.NAME = "Nm"
    self.ID = "ID"
    self.AMOUNT = "Amt"
    self.DDATE = "DD"
    self.TDATE = "TD"
    self.PERIOD = "P"
    self.IMPORTANT = "I"

# Returns true if n is in the interval min to max, inclusive
def within(n, min, max):
    return (n >= min and n <= max)

# Retruns true if n is in the interval min to max, exclusive
def between(n, min, max):
    return (n > min and n < max)

## Here's the epics:
program = Program()
program.run()
