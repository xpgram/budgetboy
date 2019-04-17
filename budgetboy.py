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

# Globals
argv = sys.argv

class Program:

    def __init__(self):
        dt = datetime.now()
        self.curDate = DueDate(dt.day, dt.month, dt.year)
        self.projectionDate = self.curDate + Time(months=4)     # Projection date... 4 months I think is a dev-test

        self.separatorChar = '`'
        self.IDs = []
        self.budgetItems = []

        # TODO Make this a relative path
        # Relative to the script's source location, anyway
        self.datafilePath = "C:\\Users\\XPGram\\Home\\Scripts\\Data\\budgetboy_data"
        
    def run(self):
        print()             # First spacer, separates the shell command line from the output
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
            f.write(str(term) + program.separatorChar)
        f.write("\n")

        ## Write each budget item as a line, following the format of the header fields, using the separator char.
        for b in self.budgetItems:
            for term in Terms:
                f.write(str(b.fields[term]) + program.separatorChar)
            f.write("\n")
        
        ## Close the data file
        f.close()

    # Backs up the "old" datafile before saving a new one.
    def backup(self):
        ## Open 'from' file and 'to' file
        try:
            r = open(self.datafilePath, 'r')
        except FileNotFoundError:
            return      # Nothing to do here
        
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
        if not line:
            return      # No point in loading an empty file
        
        ## verify its terms are.. correct?
        for term in Terms:
            if line.find(str(term)) == -1:  # TODO I guess I should demand they also be the only fields... I dunno.
                raise Exception("File appears to be corrupt: file content does not match expected format.")
        
        ## Break the header line into discrete pieces
        n = 0
        columnNames = []
        line = line[0:line.find('\n')]
        while n < len(line):
            columnNames.append(line[n:line.find(self.separatorChar, n)])
            n = line.find(self.separatorChar, n) + len(self.separatorChar)
        
        ## Iterate over the proceeding lines, parsing them by the separator char
        ## (Also, remove the \n before iteration)
        line = f.readline()
        while line:
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
                print(">> " + e.fields[Terms.DDATE] + " : " + e.fields[Terms.NAME] + " : " + e.fields[Terms.AMOUNT])
                raise Exception("This object did not read correctly from memory. Check datafile for corruption?")
                    # TODO This should never happen, but it would be cool if I passed this object to
                    # a list of misfits, and then displayed that list of troublemakers to the user,
                    # which is ~kind of~ what I'm doing here, I suppose.
            
            # Verify the object, and add it to memory
            if e.valid():
                self.IDs.append(e.fields[Terms.ID])
                program.budgetItems.append(e)
            else:
                print(">> " + e.displayStr())
                raise Exception("Data is corrupt; this item did not validate correctly.")

            # Continue dat while loop
            line = f.readline()

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
            if item.valid() == False:
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
            for r in toRemove:
                self.budgetItems.pop(r)
        
        # Silently delete old listings
        for r in silentRemove:
            self.budgetItems.pop(r)

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
            if item.fields[Terms.PERIOD] != Period.Singular:
                while item.fields[Terms.DDATE] < self.curDate:
                    item.rollForward()

    ## Interprets the user's arguments to the program as actionable.. actions.
    def userInput(self):
        # TODO bby wrk on ths

        # I have updated the features!
        # As far as I can tell, this baby is fully up and running with no side effects!
        #
        # That is, except for no projection features.
        # I am not willing to work on that ~right now~, partly because I spent ~12 hours finishing this thing,
        # and all that time I was ~supposed~ to be studying.
        #
        # Details are below, or far below somewhere, I'm sure, but the gist is this:
        #   Default view has an itemized budget for the month feature
        #   An itemized budget for any period should also be creatable
        #   The user can do this with the proj command
        #   These mostly project from the current day
        #   I'm not sure if there's any reason to proj from a different day. Per se. Ergo. Vis a vis. Concordantly.
        # Those are the details. Know them. Work them. Serve them. Fuck you.
        #
        # Oh, also, I don't actually know how this boy handles an empty file anymore.
        # I thought that it freaked out the last time I tried, and hung in an infinite loop.
        # So, I dunno, check?
        #
        # Oh, and last-thing, last-thing: fix that fucking relative-path problem, god damn.
        
        # proj MM-DD-YY
        # proj 6m 3d 2y
        #           displays a net-income projection for either the specified amount of time, or until the given date.
        #           a projection is always displayed, this just modifies the projection period
        #           the table that always prints below the upcoming month will just project farther (or shorter?)
        #           than usual.

        # A thought: what about monthly periods like "3rd Thu of the Month"?
        # I'm not concerned, but still. Depends on how monthly salaries are distributed, really. I have no idea.

        # If I add Luxury tallying:
        #   these items do not need IDs, they are one-time payments, usually entered the day of,
        #   and are only meant to add up against the month's net total. They should still have a date attached.

        # Also, I forgot to consider monthly budgets.
        #   'Food', for instance, does not have a DDATE, but should count against net totals per month.
        #   I'll have to consider how to model this.
        #   I think if I set 'budgeted' as a flag, I can choose to ignore the DATE object (but still have one),
        #   and I can roll the item forward by any Period (maybe 'Food' is bi-weekly, huh?)

        if len(argv) < 2:      # If 'budgetboy' is the only argument: Default View
            # Block 1: Display 1-month forward, list all expenses as events
            self.d_eventListProjection(Time(days=30))

            # Find the first of the current relevant month
            start = self.curDate.clone()
            if start.day > 25: start + Time(months=1)   # Advance the month forward once this month is almost over
            start.day = 1

            # Find the last of the current relevant month
            end = start.clone()
            end.day = Month.length(end.month)

            # Block 2: Display an itemized budget for the current relevant month
            self.d_itemizedProjection(start, end)

        elif len(argv) >= 2:
            # Add a new expense object
            if (argv[1] == 'add' or
                argv[1] == 'new' or
                argv[1] == '-a'):
                self.addItem()

            # Add a new 'income' object
            elif (argv[1] == 'addi' or
                  argv[1] == 'newi' or
                  argv[1] == '-ai'):
                self.addItem(True)

            # Remove an expense object by its ID
            elif (argv[1] == 'rem' or
                  argv[1] == '-r'):
                self.removeItem()

            # Roll an expense object's date forward, by its ID
            elif (argv[1] == 'payed' or
                  argv[1] == '-p'):
                self.advanceItemDate()

            # Add a termination date to an object, by its ID
            elif (argv[1] == 'terminate' or
                  argv[1] == 'term' or
                  argv[1] == '-t'):
                self.terminateItem()

            # Toggles an expense object's 'important' flag, by ID
            elif (argv[1] == 'important' or
                  argv[1] == 'star' or
                  argv[1] == '-i'):
                self.toggleItemImportance()

            # Changes the name of an expense object, by ID
            elif (argv[1] == 'name' or
                  argv[1] == '-n'):
                self.changeItemName()
            
            elif (argv[1] == 'amount' or
                  argv[1] == 'amt' or
                  argv[1] == '-m'):
                self.changeItemAmount()

            # List items in the budget by a given string, or list all
            elif (argv[1] == 'list' or
                  argv[1] == '-l'):
                self.listItems()
            
            # List all items in the budget
            elif (argv[1] == 'listall'):
                self.listAll()

            # Default case
            else:
                print('Actionable command not understood: ' + argv[1])
                print()

    ## Adds a new expense object to the global list
    # 'income' determines the sign of the amount field, and is for the command addi specifically.
    def addItem(self, income=False):
        # Arguments must be between 5 and 7 inclusive
        argNum = len(argv)
        if argNum < 5 or argNum > 7:
            print("Item could not be added: malformed request.")
            print()
            return

        # Collect user input. Provide feedback if incorrect.
        name = argv[2]
        amt = self.parseAmount(argv[3], income)
        date = self.parseDate(argv[4])
        prd = Period.Monthly
        impt = False
        for i in range(5, argNum):
            prd = self.parsePeriod(argv[i])
            impt = self.parseImportance(argv[i])

        # Generate a unique ID for the new expense object
        newid = self.newID()
        self.IDs.append(newid)

        # Build a new expense object
        fields = {}
        fields[Terms.NAME] = name
        fields[Terms.ID] = newid
        fields[Terms.AMOUNT] = amt
        fields[Terms.DDATE] = date
        fields[Terms.TDATE] = date if prd == Period.Singular else None
        fields[Terms.PERIOD] = prd
        fields[Terms.IMPORTANT] = impt

        expense = Expense(fields)

        # Inform the user it was successful, and add it.
        print(expense.displayStr())
        print("New expense object successfully added.")
        print()

        self.budgetItems.append(expense)

    ## Parses a string for an expense amount
    def parseAmount(self, s, income=False):
        if len(s) == 0:
            return None

        # 'income' labels what kind of 'expense' this amount is. This is given by the program.
        # An '+' or an '-' found in the string forces one or the other.
        if s.find('+') != -1:
            income = True
            s = s.replace('+', '', 1)
        elif s.find('-') != -1:
            income = False
            s = s.replace('-', '', 1)

        # Remove one '$' if the user (was stupid enough! Ha! Take that user!) included one
        if s.find('$'):
            s = s.replace('$', '', 1)

        try:
            amt = int(s)
        except ValueError:
            print("Item could not be added: the amount integer could not be parsed.")
            print()
            exit()
        
        amt = abs(amt)  # I dunno. Users are weird.
        return amt if income else -amt
    
    ## Parse a string for a date object
    def parseDate(self, s):
        # Dates can be given:
        #   MM-DD-YYYY
        #   MM-DD-yy
        #   MM-DD       Year assumed: this
        #   DD          Month and year assumed: this
        #  '[name] 6'       Year assumed: this
        #  '[name] 6 2019'
        # TODO I will try harder later. Right now, only MM-DD-YYYY is accepted.

        # I can at least add support for MM-DD
        if len(s) == 5:
            s = s + '-' + str(self.curDate.year)

        try:
            date = DueDate()
            date.fromString(s)
        except ValueError:
            print("Item could not be added: the date integers could not be parsed.")
            print()
            exit()
        except Exception:
            print("Item could not be added: date object did not fit MM-DD-YYYY")
            print()
            exit()
        
        return date

    ## Parse a string for a Period.Value
    def parsePeriod(self, s):
        kw_singular = ['s', 'singular', 'one-time', 'once']
        kw_weekly = ['w', 'weekly', '7']
        kw_biweekly = ['b', 'biweekly', 'bi-weekly', '14']
        kw_monthly = ['m', 'monthly']
        kw_annually = ['y', 'a', 'yearly', 'annually', 'annual']
        full_list = [kw_singular, kw_weekly, kw_biweekly, kw_monthly, kw_annually]
        repr_list = [Period.Singular, Period.Weekly, Period.BiWeekly, Period.Monthly, Period.Annually]

        for i in range(0, len(full_list)):
            for w in full_list[i]:
                if w == s.lower():
                    return repr_list[i]
        
        return Period.Monthly       # No terms found, return the default


    ## Parse a string for an 'Important' flag
    def parseImportance(self, s):
        r = False
        keywords = ['*', '**', 'star', 'starred', 'important', 'always-show']
        for k in keywords:
            if k == s.lower():
                r = True
        return r

    ## Removes an item by its ID
    def removeItem(self):
        # Assert argument length
        if not self.assertArgNum(3):
            print('Could not delete item: malformed request.')
            print()
            exit()
        
        item, idx = self.searchByID(argv[2])

        # Inform the user
        if item:
            self.budgetItems.pop(idx)
            print(item.displayStr())
            print("This item has been deleted.")
        else:
            print("An item with the ID " + argv[2] + " could not be found.")
        print() # Final spacer

    ## Advances a budget item's date, item targeted by its ID
    def advanceItemDate(self):
        # payed [ID]
        # -p [ID]
        #           "pays" the ID'd bill (or income; they're the same object)
        #           All this actually does is roll the object's DDate one period back
        if not self.assertArgNum(3):
            print('Could not advance item date: malformed request.')
            print()
            exit()
        
        item, idx = self.searchByID(argv[2])
        
        # Inform the user, and also do the thing
        if item:
            oldDate = item.fields[Terms.DDATE].clone()
            item.rollForward()
            newDate = item.fields[Terms.DDATE].clone()
            itemID = item.fields[Terms.ID]
            itemName = item.fields[Terms.NAME]
            # Why am I doing this?
            print(itemID + "  " + itemName + "    : " + oldDate.get() + " --> " + newDate.get())
        else:
            print("An item with the ID " + argv[2] + " could not be found.")
        print() # Final spacer

    ## Adds a termination date to an object, object by ID
    def terminateItem(self):
        if not self.assertArgNum(4):
            print('Could not add termination date: malformed request.')
            print()
            exit()
        
        item, idx = self.searchByID(argv[2])
        date = self.parseDate(argv[3])

        # Inform the user, and also do the thing
        if item:
            oldDate = 'None'
            if item.fields[Terms.TDATE] != None:
                oldDate = item.fields[Terms.TDATE].clone().getFull()
            newDate = date.getFull()
            itemID = item.fields[Terms.ID]
            itemName = item.fields[Terms.NAME]
            
            item.fields[Terms.TDATE] = date
            print(itemID + '  ' + itemName + '    : ' + oldDate + " --> " + newDate)
        else:
            print("An item with the ID " + argv[2] + " could not be found.")
        print()

    ## Toggles an expense item's 'important' flag, searched for by ID
    def toggleItemImportance(self):
        if not self.assertArgNum(3):
            print('Could not toggle item importance: malformed request.')
            print()
            exit()
        
        item, idx = self.searchByID(argv[2])

        if item:
            flag = item.fields[Terms.IMPORTANT]
            item.fields[Terms.IMPORTANT] = not flag
            itemID = item.fields[Terms.ID]
            itemName = item.fields[Terms.NAME]

            print(itemID + '  ' + itemName + '    : ' + ('starred' if not flag else 'unstarred'))
        else:
            print("An item with the ID " + argv[2] + " could not be found.")
            # TODO I really repeat myself a lot here, don't I?
        print()


    ## Changes an expense item's name, searched for by ID
    def changeItemName(self):
        if not self.assertArgNum(4):
            print('Could not update item name: malformed request.')
            print()
            exit()
        
        item, idx = self.searchByID(argv[2])
        newName = argv[3]

        if item:
            oldName = item.fields[Terms.NAME]
            item.fields[Terms.NAME] = newName
            itemID = item.fields[Terms.ID]

            print(itemID + '  ' + oldName + '    -->    ' + newName)
        else:
            print("An item with the ID " + argv[2] + " could not be found.")
        print()

    ## Changes an expense item's amount, serached for by ID
    def changeItemAmount(self):
        if not self.assertArgNum(4):
            print('Could not update item amount: malformed request.')
            print()
            exit()
        
        item, idx = self.searchByID(argv[2])

        if item:
            newVal = self.parseAmount(argv[3], item.amount() >= 0)
            oldAmount = item.amountStr()
            item.fields[Terms.AMOUNT] = newVal
            newAmount = item.amountStr()
            itemID = item.fields[Terms.ID]
            itemName = item.fields[Terms.NAME]

            print(itemID + '  ' + itemName + '    : ' + oldAmount + ' --> ' + newAmount)
        else:
            print("An item with the ID " + argv[2] + " could not be found.")
        print()

    ## Lists all items in the budget so long as they contain a search string
    def listItems(self):
        if self.assertArgNum(2):
            self.listAll()
            return
        
        expenses = self.copyList()
        expenses = self.sortList(expenses)
        successful = False

        # Display any items which match any argv[idx] with idx >= 2
        for exp in expenses:
            match = False

            for i in range(2, len(argv)):
                if exp.fields[Terms.ID] == argv[i]:
                    match = True
                    break
                if exp.fields[Terms.NAME].lower().find(argv[i].lower()) != -1:
                    match = True
                    break
            
            if match:
                print(exp.displayAllStr())
                successful = True
        
        # If a list was produced, do nothing, but if one wasn't, apologize profusely
        if not successful:
            print("No items found.")

        print() # Final spacer

    ## Lists all items in the budget
    def listAll(self):
        if not self.assertArgNum(2):
            print("Too many arguments: did you mean to do something different?")
            print()
            exit()

        expenses = self.copyList()
        expenses = self.sortList(expenses)
        
        for item in expenses:
            print(item.displayAllStr())
        print()

    ## Sort a list of Expense objects by expiry, then by amount, then name
    # This sort method has a different result and a different use case from self.sort()
    def sortList(self, ls):
        # Deep copy
        expenses = []
        for i in ls:
            expenses.append(i.clone())

        # Sort
        for i in range(1, len(expenses)):
            k = i
            j = i - 1

            # The block I have down there.
            # I know.
            # My head hurts right now.
            # I wish it weren't so stupid.
            # TODO Make it not stupid.
            while j > -1:
                swap = False
                # Expired items filter to the bottom
                if expenses[j].expired() and not expenses[k].expired():
                    swap = True
                elif not expenses[j].expired() and expenses[k].expired():
                    swap = False
                # Positive items filter to the top
                elif expenses[j].amount() < 0 and expenses[k].amount() >= 0:
                    swap = True
                elif expenses[j].amount() >= 0 and expenses[k].amount() < 0:
                    swap = False
                # Smaller amounts filter to the bottom
                elif abs(expenses[j].amount()) < abs(expenses[k].amount()):
                    swap = True
                elif abs(expenses[j].amount()) > abs(expenses[k].amount()):
                    swap = False
                # Sort remaining alphabetically
                elif expenses[j].fields[Terms.NAME] > expenses[k].fields[Terms.NAME]:
                    swap = True
                
                if swap:
                    tmp = expenses[k]
                    expenses[k] = expenses[j]
                    expenses[j] = tmp
                
                j = j - 1
                k = k - 1

        # Done
        return expenses

    ## Displays an at-a-glance of the coming bills (within 30 days)
    # timeLength should be a Time object
    # Does not have a clock roll-back feature because that's not what this is for.
    def d_eventListProjection(self, timeLength):
        endDate = self.curDate + timeLength     # The time-window we are considering.
        expenses = self.copyList()              # Exists so that changes to item dates do not reflect on the actual list.
        netTotal = 0
        width = Expense.displayWidth()

        print(self.curDate.getFull())
        print()

        done = False
        while not done:
            # Find the next, soonest expense
            nxt = None
            idx = None
            for i in range(0, len(expenses)):
                if expenses[i].fields[Terms.DDATE] <= endDate:
                    if nxt == None or nxt > expenses[i]:
                        nxt = expenses[i]
                        idx = i
            
            # Display the next, soonest expense, if one was found, and roll its date forward
            if nxt != None:
                print(nxt.displayStr())
                nxt.rollForward()
                netTotal += nxt.amount()    # Tally up
                if nxt.fields[Terms.PERIOD] == Period.Singular:
                    expenses.pop(idx)       # If event is one-time, stop considering
                if nxt.expired():
                    expenses.pop(idx)       # If event expires after the just-printed date, stop considering
            # However, if one wasn't found, stop looking
            else:
                done = True
        
        print() # Spacer

        # Print any '**' important items outside the time-window in a separate block
        block2 = False
        for i in range(0, len(self.budgetItems)):
            if self.budgetItems[i].fields[Terms.IMPORTANT]:
                if self.budgetItems[i].fields[Terms.DDATE] > endDate:
                    print(self.budgetItems[i].displayStr())
                    block2 = True

        if block2: print() # Spacer

        # Final Statement: Financial Net Total
        s = '{:>' + str(width-10) + '}  '
        s = s.format("Net total for 30-day projection:")
        sign = '+' if netTotal > 0 else '-'
        s = s + "{:>8}".format(sign + "$" + str(abs(netTotal)))
        print(s)

        print() # Final Spacer

    ## Displays an itemized "receipt" of all expenses and incomes from the startDate to the endDate
    # startDate and endDate should be DueDate objects
    def d_itemizedProjection(self, startDate, endDate):
        pass
        # print("Itemized Budget (" + self.getPeriod(startDate, endDate) + ")")
        # print(self.horizontalRule())

        # TODO
        # This one is gonna have to do some stuff:
        #   It needs a list of expense objects, and their count
        #   It needs to print its own version of Expense.display()
        #     with the net-total of all its occurrences

    ## Returns a string detailing a time-period's start to end in a nice format
    def getPeriod(self, start, end):
        # Get all string displays / add a space for auto-format
        m1 = Month.name(start.month) + ' '
        d1 = str(start.day) + ' '
        y1 = str(start.year) + ' '
        m2 = Month.name(end.month) + ' '
        d2 = str(end.day) + ' '
        y2 = str(end.year) + ' '
        sep = '- '

        # Years are the same
        if (start.year == end.year):
            # years are omitted
            y1 = ''
            y2 = ''
            # start.day is omitted if it's the first
            if start.day == 1:
                d1 = ''
            # end.day is omitted if it's the last
            if end.day == Month.length(end.month):
                d2 = ''
            # end.month is omitted if it's the same, but not if day isn't
            if d2 == '' and end.month == start.month:
                m2 = ''
        # Years are different
        else:
            # day is omitted if it's the first
            if start.day == 1:
                d1 = ''
            if end.day == 1:
                d2 = ''
            # month is omitted if it's Jan, but not if day isn't
            if d1 == '' and start.month == 1:
                m1 = ''
            if d2 == '' and end.month == 1:
                m2 = ''
        # sep is omitted if end is completely omitted
        if d2 == '' and m2 == '' and y2 == '':
            sep = ''
        
        # Return the built string
        s = m1 + d1 + y1 + sep + m2 + d2 + y2
        return s[0:len(s)-1]        # Removes the trailing space

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
    
    ## Searches for a given ID, returning the object and its index, or [None, None] if it could not be found
    def searchByID(self, s):
        # Make sure search string is correct
        try:
            int(s)
            if len(s) != 3:
                raise Exception()
        except Exception:
            print("Search ID is malformed, cannot complete.")
            print()
            exit()
        
        item = None
        idx = None

        # Perform the search
        for i in range(0, len(self.budgetItems)):
            if self.budgetItems[i].fields[Terms.ID] == s:
                item = self.budgetItems[i]
                idx = i
        
        # Be careful not to accept None as a result
        return item, idx

    ## Deep copies the expense list and returns it
    def copyList(self):
        l = []
        for item in self.budgetItems:
            l.append(item.clone())
        return l

    ## Returns a string of '=' equal in length to the width of the display area
    def horizontalRule(self):
        return '=' * Expense.displayWidth()

    ## Returns true if the number of arguments given to the program equals n
    def assertArgNum(self, n):
        return len(argv) == n










class Expense:

    def __init__(self, fields=None):
        if fields == None:
            self.fields = {}
        else:
            self.fields = fields
        
    def __eq__(self, o):
        if o is None: return False
        return self.compare(o) == 0

    def __gt__(self, o):
        return self.compare(o) == 1
    
    def __ge__(self, o):
        return self.compare(o) > -1

    def __lt__(self, o):
        return self.compare(o) == -1

    def __le__(self, o):
        return self.compare(o) < 1

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
            Period.valid(self.fields[Terms.PERIOD]) and
            self.fields[Terms.DDATE].valid()):
            t2 = True

        return t1 and t2

    # Returns a formatted line considered this expense object's 'formal display'
    # Full width = 56
    def displayStr(self):
        s = '' + self.fields[Terms.ID] + '  '
        s = s + self.fields[Terms.DDATE].get(self.lastPayment()) + ' '
        s = s + '{:35.35}'.format(self.fields[Terms.NAME]) + (' **' if self.fields[Terms.IMPORTANT] else '   ') + '  '
        s = s + "{:>8}".format(self.amountStr())
        return s

    @staticmethod
    def displayWidth():
        return 61       # Would be nice, I guess, to calculate this.

    ## Returns a formatted line containing all the information this object has
    def displayAllStr(self):
        period = "One-Time"
        if self.fields[Terms.PERIOD] != Period.Singular:
            period = self.fields[Terms.PERIOD].name

        s = '' + self.fields[Terms.ID] + '  '
        s = s + '{:35.35}'.format(self.fields[Terms.NAME]) + (' **' if self.fields[Terms.IMPORTANT] else '   ') + '  '
        s = s + "{:>8}".format(self.amountStr()) + '  '
        s = s + "{:8}".format(period) + '  '
        s = s + self.fields[Terms.DDATE].getFull(self.lastPayment())

        if self.fields[Terms.TDATE] != None:
            s = s + ' x  ' + self.fields[Terms.TDATE].getFull()

        return s

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
        if not self.expired():
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
        if self.fields[Terms.TDATE] == None:
            return False
        return self.fields[Terms.DDATE] > self.fields[Terms.TDATE]

    # Returns true if this is the last occurrence of this payment, meaning the next period interval lies
    # beyond the termination date.
    def lastPayment(self):
        if self.fields[Terms.PERIOD] == Period.Singular:
            return True     # This is by-default the last payment
        if self.fields[Terms.TDATE] is None:
            return False    # This payment does not end
        
        last = False

        # Must be valid ~and~ its advance must be invalid to be the last payment
        date = self.fields[Terms.DDATE]
        if (date <= self.fields[Terms.TDATE] and
            date.advancePeriod(self.fields[Terms.PERIOD]) > self.fields[Terms.TDATE]):
            last = True

        return last
    
    # Returns true if the given var represents an instance of Expense (this class)
    def verifyOther(self, other):
        return isinstance(other, Expense)
    
    # Returns 1 if this object comes logically after the 'other' in ordering, -1 if before, 0 if indeterminate.
    def compare(self, other):
        if not self.verifyOther(other):
            raise TypeError("expected {} object, recieved {}".format(type(self), type(other)))
        val = 1 if self.expired() and not other.expired else (-1 if not self.expired and other.expired else 0)
        if val == 0: val = self.fields[Terms.DDATE].compare(other.fields[Terms.DDATE])
        if val == 0: val = 1 if self.fields[Terms.AMOUNT] > other.fields[Terms.AMOUNT] else (-1 if self.fields[Terms.AMOUNT] < other.fields[Terms.AMOUNT] else 0)
        if val == 0: val = 1 if self.fields[Terms.NAME] > other.fields[Terms.NAME] else (-1 if self.fields[Terms.NAME] < other.fields[Terms.NAME] else 0)
        return val
    
    # Returns a copy of this instance.
    def clone(self):
        e = Expense()
        for term in Terms:
            e.fields[term] = self.fields[term]
        e.fields[Terms.DDATE] = self.fields[Terms.DDATE].clone()
        if self.fields[Terms.TDATE] == None:
            e.fields[Terms.TDATE] = None
        else:
            e.fields[Terms.TDATE] = self.fields[Terms.TDATE].clone()
        return e
    









class DueDate:

    def __init__(self, day=1, month=1, year=1):
        self.day = day
        self.month = month
        self.year = year
        self.assertValidity()
    
    def __str__(self):
        return "{:02d}-{:02d}-{}".format(self.month, self.day, self.year)
    
    def __eq__(self, o):
        if o is None:
            return False
        if not isinstance(o, DueDate):
            raise TypeError("expected a DueDate object, recieved {}".format(type(o)))
        day = self.effectiveDate()
        oday = o.effectiveDate()
        return day == oday and self.month == o.month and self.year == o.year
        
    def __gt__(self, o):
        day = self.effectiveDate()
        oday = o.effectiveDate()

        if self.year != o.year:      b = self.year > o.year
        elif self.month != o.month:  b = self.month > o.month
        else:                        b = day > oday

        return b
        
    def __ge__(self, o):
        return self.__eq__(o) or self.__gt__(o)
        
    def __lt__(self, o):
        day = self.effectiveDate()
        oday = o.effectiveDate()

        if self.year != o.year:      b = self.year < o.year
        elif self.month != o.month:  b = self.month < o.month
        else:                        b = day < oday
        
        return b
    
    def __le__(self, o):
        return self.__eq__(o) or self.__lt__(o)
    
    def __add__(self, o):
        d = self.clone()
        d.addTime(o)
        return d
    
    def __iadd__(self, o):
        self.addTime(o)
        return self
    
    def __sub__(self, o):
        d = self.clone()
        o = Time(days=(-o.day), months=(-o.month), years=(-o.year))
        d.addTime(o)
        return d
    
    def __isub__(self, o):
        self.addTime(o)
        return self
    
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

        self.month = int(ls[0])
        self.day = int(ls[1])
        self.year = int(ls[2])

        self.assertValidity()

    def checkType(self, o):
        if not isinstance(o, Time):
            raise TypeError("expected a Time object, recieved {}".format(type(o)))
    
    def addTime(self, time):
        self.checkType(time)

        # Resolve months and years first.
        self.year += time.year
        self.month += time.month

        # Overflow months-out-of-range into years
        while self.month < Month.minimum:
            self.month += Month.maximum
            self.year -= 1
        while self.month > Month.maximum:
            self.month -= Month.maximum
            self.year += 1
        
        # If days are being added/subtracted, then throw out the idealized date.
        if time.day != 0:
            self.day = self.effectiveDate() # Calc from a real point in time in the resulting month
            self.day += time.day

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
        if period == Period.Weekly:     d += Time(days=7)
        elif period == Period.BiWeekly: d += Time(days=14)
        elif period == Period.Monthly:  d += Time(months=1)
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
        string = self.get()
        string = string[0:len(string)-1]        # Remove trailing space from get()
        string = string + ', ' + str(self.year)
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
    
    ## Frontloads all fields into one int value approximating the number of days each describes.
    def lengthInDays(self):
        return self.day + self.month*30 + self.year*365










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
        if type(n) == int:
            return (within(n, 1, len(Period)))
        elif type(n) == Period:
            return True
        else:
            raise Exception("Cannot validate parameter against enum values with {}".format(type(n)))
    
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

    def __str__(self):
        return self.name

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

# debug feature
def log(s):
    print(s)

## Here's the epics:
program = Program()

program.run()
