import sys
from datetime import date
from datetime import datetime
from enum import Enum

## Search 'Rewrite' for whatever I was doing earlier
## Also, rewrite expense and the other classes to use dictionaries for fields; since I'm using
## them for saving/loading anyway, it's more concise.

class Program:
    
    separatorChar = '`'

    ## These constants are names for database columns. They're for saving/loading data.
    NAME = 'Nm'
    AMOUNT = 'Amt'
    DDATE = 'DD'
    TDATE = 'TD'
    PERIOD = 'P'
    IMPORTANT = 'I'

    header = [program.NAME, program.AMOUNT, program.DDATE, program.TDATE, program.PERIOD, program.IMPORTANT]

    def run():
        dt = datetime.now()
        curDate = DueDate(dt.day, dt.month, dt.year)
        projectionDate = curDate += Time(months=4)
        budgetItems = []
        bugetPeriod = []
        
        arg = sys.argv
        datafilePath = "C:\\Users\\xpgra\\Home\\Scripts\\Data\\budgetboy_data"
        
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
        
        ## Sort list
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
        
        ## Via user argumentative input, do something
        ## Show some kind of feedback on the thing
        
                ## This is the part where I am currently.
                ## My head is too.. sleepy to continue.
                ## I may need a nap.
                ## But! (fuck fuck fuck..) I have to call my Dad ~and~ I have to visit my friend.
                ## So... shit.
                
                ## Todo:
                ## Clean up the program class, jesus christ.
                ## That means:
                ##      Separate the different parts of run() into their own methods
                ##      Rewrite save and load so that they aren't... retarded.
                ##          Get expenses to save() themselves, maybe
                ##      Maybe confirm any of this works
        
        ## Save and exit
        f = file.open(datafilePath, 'w')
        
        e = '`' ## For 'escape char' which actually doesn't make sense, should be 'separator'
        for expense in budgetItems:
            ddate = expense.date
            tdate = expense.terminationDate
            s = ""
            if ddate == None:
                s += '--'
            else:
                s += str(ddate.day)
                s += e + str(ddate.month)
                s += e + str(ddate.year)
                if ddate.duedate == None:
                    s += e + '--'
                else:
                    s += e + str(s.duedate)
            s += e + expense.name
            s += e + str(expense.amount)
            s += e + expense.payperiod.name
            s += e + str(1 if expense.important else 0)
            if tdate == None:
                s += e + '--'
            else:
                s += e + str(tdate.day)
                s += e + str(tdate.month)
                s += e + str(tdate.year)
            
            f.write(s + '\n')
        
        f.close()
    
    ## Searchable: [Main() Rewrite]

    def save(self):
        saveLine = {}

        ## Open the data file
        ## Also, I'm doing the try/except block because.. of paranoia, I think. Is it even necessary?
        try:
            f = open(program.datafile, 'x')
        except FileExistsError:
            pass
        f = open(program.datafile, 'w')

        ## Write all header fields into one line using the separator char.
        for h in header:
            f.write(h + program.separatorChar)
        f.write("\n")

        ## Write each budget item as a line, following the format of the header fields, using the separator char.
        for b in budgetItems:
            ## TODO I won't do this until later, but if b used a dictionary for its fields itself, this block wouldn't be necessary. Probably.
            saveLine[program.NAME] = b.name
            saveLine[program.AMOUNT] = b.amount
            saveLine[program.DDATE] = str(b.date)
            saveLine[program.TDATE] = str(b.terminationDate)
            saveLine[program.PERIOD] = b.payperiod.name
            saveLine[program.IMPORTANT] = b.important

            for sl in saveLine:
                f.write(sl + program.separatorChar)
            f.write("\n")
        
        ## Close the data file
        f.close()

    def load(self):
        ## read first line, should be the DB header

        ## verify its terms are.. correct?

        ## Iterate over the proceeding lines, parsing them by the separator char
        ## (Also, remove the \n before iteration)

        ## read the values into a dict called loadedItem
        ## loadedItem[header[i]] = s.find(program.separatorChar, n)
        loadedItem = {}

        ## pull from this dict the relevant data via their keys
        ## name = loadedItem[program.NAME]

        ## insert all this dict data into a new expense object
        ## Expense(name, amount, date ...), or
        ## Expense(loadedItem[program.NAME], loadedItem[program.AMOUNT], ...)

class Expense:

    def __init__(self, name, amount, date=None, payperiod = Period.Monthly, important=False):
        self.name = name
        self.amount = amount
        self.date = date
        self.payperiod = payperiod
        self.terminationDate = None         ## When this item stops existing. For when I cancel a bill or get a promotion, etc.
        self.important = important          ## This flag essentially means "always show." Great for singular large-sum payments whose due date may or may not be looming over my head
        
    def string(self):
        return '-$' + str(self.amount)
        
    def amount(self):
        return -self.amount
    
    def advancePeriod(self):
        self.date = self.date.advanceTime(self.payperiod)
    
    def recedePeriod(self):
        self.date = self.date.recedeTime(self.payperiod)
    
    ## This will affect when the bill stops being inluded in the budget.
    ## If the bill has passed its expiration, it will remain in memory for rollback for 1 year
    def terminateOn(self, date):
        if not isinstance(date, DueDate):
            raise TypeError("expected a DueDate object, got {}".format(type(date)))
        b = False
        if date.valid():
            self.terminationDate = date
            b = True
        return b
        
    ## Returns True if this item has run its expiration date. ~On~ the expiration date is still valid.
    def expired(self):
        return self.date > self.terminationDate
    
    def verifyOther(self, other):
        return isinstance(other, Expense)
    
    def compare(self, other):
        if not verifyOther(other):
            raise TypeError("expected {} object, recieved {}".format(type(self), type(other)))
        val = self.date.compare(other.date)
        if val == 0: val = 1 if self.amount > other.amount else (-1 if self.amount < other.amount else o)
        if val == 0: val = 1 if self.name > other.name else (-1 if self.name < other.name else 0)
        return val
    
    def clone(self):
        e = Expense(self.name, self.amount, self.payperiod, self.date.clone(), self.important)
        e.terminationDate = self.terminationDate.clone()
        return e
    
    def valid(self):
        b = False
        if (self.name != "" and
            self.amount >= 0 and
            self.payperiod >= Constants.Budget and
            self.payperiod <= Constants.Annually and
            self.date.valid()) and 
            (self.terminationDate == None or
             self.terminationDate.valid())):
            b = True
        return b

class Income(Expense):
    
    def string(self):
        return '+$' + str(self.amount)
    
    def amount(self):
        return self.amount
    
    def verifyOther(self, other):
        return isinstance(other, Income)
    
    def clone(self):
        i = Income(self.name, self.amount, self.payperiod, self.date.clone(), self.important)
        i.terminationDate = self.terminationDate.clone()
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
    
class Month
    maximum = 12
    minimum = 1
    daysMax = 31
    daysMin = 1
    names =   ['Nul', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    lengths = [    0,    31,    28,    31,    30,    31,    30,    31,    31,    30,    31,    30,    31]
    
    def name(numeral):
        if numeral < 1 or numeral > maximum:
            raise OverflowError("Value given is out of bounds; recieved {}".format(numeral))
        return names[numeral]
        
    def length(numeral):
        if numeral < 1 or numeral > maximum:
            raise OverflowError("Value given is out of bounds; recieved {}".format(numeral))
        return length[numeral]

## Here's the epics:
program = Program()
program.run()
