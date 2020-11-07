from datetime import date
from datetime import datetime
from datetime import timedelta
from calendar import monthrange
import sys
import os
import shlex
import json
import re
import random
import copy

# TODO Readjust display to fit 20.20 names. Increase amount width, for instance.

# TODO It just occurred to me, separate accounts as they're implemented don't accomplish much.
# If I make $600 on payday, deposited into General, then I have a $50 deposit into "New PC",
# "New PC" never deducts itself from my paycheck. Essentially, I "make" $650, which isn't true.
# I mean, a workaround is to make the "New PC" "savings" account negative, which is semi-sensible
# since it'll eventually be an expense anyway, I guess. Yeah.
# I might think about fixing it if I were publishing, but eh.

# TODO Rewrite the Forecast to display in two columns?
# It can get pretty long.


helptext = """
By default, the script will print a 30-day calendar extending from today's date.

A note on reading the display:

541  Aug 24* Phonebill            **          -$90
ID   Due     Name              Important    Amount

Asterisks (*) denote final payments when next to dates, automatic payments when
next to a period length, and "importance" when double-printed. "Important" expenses
are always printed, even when outside the forecast window, to remind of their
existence.

Commands:

Project Budget          project "Oct 9", project "Jan 1, 2021"
    Prints an itemized list of all expenses between today and the given date.
    A date string without a year is assumed to be of this year.
    Will fail if the given date is in the past.

List All Objects        all
    Displays in list form all details about all expenses and all accounts.

Enable Free-Editing     playground
    Enables continuous-polling and disables saving, allowing free edits of the
    budget while preserving the current one.

Re-Enable Saving        enable-saving
    While free-editing, this command signals that the script should save all
    changes upon closure of the script.

Script Closure          done
    While free-editing, requests the script be closed. Closure must occur this
    way if the script is to save any changes.

Declare Payment         pay 132 015 ...,  pay 132 15 ...
    Every listed ID which refers to an expense object will add its sum to its
    linked account and strike its earliest date due from the calendar.

Undo Payment            undo-pay 132 015 ...,  pay 132 15 ...
    Reverses the last payment of every listed ID refering to an expense object.

Add a New Expense       add ...
    Adds a new expense to the record. The command may be followed with:

    Set Name                "a string"
        Expenses must have a name.

    Set Value               700, +700, $700
        Value must be nonzero. Always assumed to be negative without a preceeding '+'.

    Set Account             acc 141, account 15
        Value will auto-convert to a 3-length ID ('0'-left-padded), but must be numeric only.
        Account will only be set if the given ID refers to an existing account object.

    Set Date Due            "Aug 7, 2020" "Aug 7" — Some other formats are acceptable.
        The due date is 'today' by default.

    Set Period Start        start [date]
        The due date supercedes the start date setting in all contexts and start date will be
        changed to reflect this; start <= due <= termination must be true.
        
    Set Period End          term [date], terminate [date]
        None by default. An expense with no termination date simply extends forever.
        If due-date is set after the term-date, the addition or edit will fail.

    Set Important           important, always-show, *, **
        Declares the expense is always displayed on the calendar.
        Useful for large, far-off payments.

    Unset Important         common, forecast-show
        Default value for importance.

    Set Automatic           auto, automatic, autopay
        Declares the expense is never overdue and will auto-pay on its due-date.

    Unset Automatic         manual, manualpay
        Default value for automatic.

    Set Recurrence Period   [varies]
        The intermission value between payments of this expense. May have the value:
        s, singular, once, one-time     (Default)
        w, week, weekly
        b, biweek, biweekly
        m, month, monthly
        y, year, yearly, annual

Add a New Account       new-account ...
    Adds a new account to the record. The command may be followed with:

    Set Name                "a string"
        Accounts must have a name.

    Set Value               700, +700, $700
        For consistency, always assumed to be negative without preceeding '+'.
        0 by default.

Change an Object        edit 143 ...
    Reopens the object with the given ID for editing. Rules for editing depend
    on whether the object is an expense or an account. See above.

Delete an Object        del 143 015 ...,  del 143 15 ...
    Every listed ID which refers to an existing object is printed and then deleted
    from the record. Expenses linked to accounts that are to be deleted are first
    relinked to the general account before account deletion.
"""


####################################################################################################
#### Regex Patterns                                                                             ####
####################################################################################################

regex_currency = r'^(?!.*[\-\+]{2})[\-\+\$]{0,2}?\d+$'      # Matches '100', '-100', '+$100' and '$+100'


####################################################################################################
#### General, Helpful Functions                                                                 ####
####################################################################################################

####################################################################################################
#### Debug Convenience Methods

show_debug_messages = True

def log(s=''):
    "Prints a suppressable message to the console."
    if show_debug_messages:
        print('DEBUG: ' + str(s))


####################################################################################################
#### General Convenience Methods

def constrain(n, n_min, n_max):
    "Returns n as limited to the range [n_min, n_max]."
    assert n_min <= n_max, "Minimum range must be less than or equal to maximum."
    return min(n_max, max(n, n_min))


####################################################################################################
#### Dictionary and List Convenience Methods

def shift(a):
    "Returns the first value of array a and the remaining values as a new list, or None and [] if a was empty to begin with."
    v = a[0] if len(a) > 0 else None
    a = a[1:]
    return (v, a)

def get(i, a):
    "Returns the value held under index i of array a if one exists, returns None if not."
    return a[i] if i >= 0 and i < len(a) else None

def find_key(f, d):
    "Returns the key to dictionary d where f( d[k] ) returns True, returns None otherwise."
    results = [k for k, v in d.items() if f(v) == True]
    return results[0] if results else None

def string_to_int(s):
    "Converts a given string to a number, or returns None on failure."
    try:
        return int(s)
    except (ValueError, TypeError):
        return None

def destructure(dict, *keys):
    "Returns a list of values for the given keys in the order they appear as arguments to this function."
    if (t := type(keys[0])) == list or t == tuple:
        keys = keys[0]
    return [dict[key] for key in keys]


####################################################################################################
#### Date functions

def date_tostring(d):
    "Converts a date object to a formatted string."
    return d.strftime('%b %d, %Y')

def date_fromstring(s):
    "Converts a formatted string to a date object."
    return datetime.strptime(s, '%b %d, %Y').date()

def parse_date(s):
    "Returns a date object parsed from a string s, or returns None if one couldn't be retrieved."
    result = None
    patterns = (
        '%b %d, %Y',
        '%b %d',
        '%m-%d-%y',
        '%m-%d-%Y',
        '%m-%d'
        )
    for pattern in patterns:
        try:
            result = datetime.strptime(s, pattern).date()
            break
        except ValueError:
            pass
    if result != None:
        if result.year == 1900:     # Just assume a year wasn't provided; I got no relationship with 1900
            result = result.replace(year=date.today().year)
    return result


####################################################################################################
#### Other parsing functions

def parse_idnumber(s, l=3):
    "Given a numerical string s, returns a zero-padded string of length l."
    r = '{0:0>{1}}'.format(s, l) if type(s) == str and s.isnumeric() else None
    if not r:
        print(f"String '{s}' could not be interpreted as an ID (length 3, numeric).")
    return r

def parse_amount(s):
    "Given a currency string, extracts its numerical. Unsigned numbers are assumed to be expenses (negative)."
    assert re.search(regex_currency, s), f"Cannot parse the string '{s}' for a currency amount: does not match regex."
    s = s.replace('$','')
    income = s.startswith('+')
    return int(s) if income else -abs(int(s))


####################################################################################################
#### Enum Types                                                                                 ####
####################################################################################################

class Period():
    "Labels for different lengths of periodic occurrence."
    singular = 'One-Time'
    weekly   = 'Weekly'
    biweekly = 'Biweekly'
    monthly  = 'Monthly'
    annual   = 'Annual'


####################################################################################################
#### Expense Type                                                                               ####
####################################################################################################

def new_expense():
    "Returns a new dictionary type with fields relevant to budgetary line-items."
    duedate = date_tostring(date.today())
    return {
        'id': newID(),                  # String-copy of the key pointing to this object in the global index.
        'name': '',                     # The name of this expense object.
        'account': g_default_account_id,# None or string ID linking this expense to an estimation account.
        'amount': 0,                    # The sum of this payment: negative are payments from the user, positive are to the user.
        'period': Period.singular,      # Period length between payments — ~only~ describes duedate movement, not occurrence.
        'duedate': duedate,             # The next unpaid date for this expense.
        'startdate': duedate,           # Start of effective period
        'termdate': duedate,            # End of effective period — set to startdate for non-recurring payments.
        'automatic': False,             # Whether this payment requires manual initiation of payment.
        'important': False,             # Whether this payment gets special treatment in the 30-day forecast.
        'active': True                  # Whether this payment still affects the budget.
    }

####################################################################################################
#### Supporting Methods

class Expense():

    @staticmethod
    def duedate(e):
        "Returns a date object from the given expense dict's duedate field."
        return date_fromstring(e['duedate'])

    @staticmethod
    def startdate(e):
        "Returns a date object from the given expense dict's startdate field."
        return date_fromstring(e['startdate'])
    
    @staticmethod
    def termdate(e):
        "Returns a date object from the given expense dict's termdate field, or None."
        return date_fromstring(e['termdate']) if e['termdate'] else None

    @staticmethod
    def firstpayment(e):
        "Returns True if the given expense dict's duedate is its first duedate within its effective period."
        duedate = date_fromstring(e['duedate'])
        prevdate = regress_date(duedate, e['period'])
        startdate = date_fromstring(e['startdate'])

        return e['period'] == Period.singular or startdate > prevdate

    @staticmethod
    def lastpayment(e):
        "Returns True if the given expense dict's duedate is its last duedate within its effective period."
        if e['period'] == Period.singular:
            return True
        else:
            duedate = date_fromstring(e['duedate'])
            nextdate = advance_date(duedate, e['period'])
            termdate = date_fromstring(e['termdate']) if e['termdate'] else None
            return termdate and termdate < nextdate

    @staticmethod
    def rollforward(e):
        """Returns a copy of the given expense dict with its duedate rolled forward one period.
        Fails if the duedate is the last for its period, or if the period is one-time."""
        assert not Expense.lastpayment(e), f"Cannot roll date '{e['duedate']}' beyond its termination date '{e['termdate']}'."

        new_e = e.copy()
        duedate = Expense.duedate(new_e)
        new_e['duedate'] = date_tostring(advance_date(duedate, new_e['period']))
        return new_e

    @staticmethod
    def rollbackward(e):
        """Returns a copy of the given expense dict with its duedate rolled backward one period.
        Fails if the duedate is the first payment for its period, or if the period is one-time."""
        assert not Expense.firstpayment(e), f"Cannot roll date '{e['duedate']}' beyond its starting date '{e['startdate']}'.'"

        new_e = e.copy()
        duedate = date_fromstring(new_e['duedate'])
        new_e['duedate'] = date_tostring(regress_date(duedate, new_e['period']))
        return new_e

    @staticmethod
    def pay(e):
        """Renders the expense object effectual and routes its payment to its assigned account, then rolls
        its date to next. If on lastpayment, object will deactivate. Inactive objects affect no accounts."""
        new_e = e.copy()

        # Setup fields for user feedback
        ID, name, amount, duedate = destructure(new_e, 'id','name','amount','duedate')
        amount = format_currency(amount)
        nextdate = 'X'

        if new_e['active']:
            Account.adjust(new_e['account'], new_e['amount'])
            if not Expense.lastpayment(new_e):
                new_e = Expense.rollforward(new_e)
                nextdate = new_e['duedate']
            else:
                new_e['active'] = False
            g_index['expenses'][ID] = new_e
            print(f"Payed:     {ID}  {name:20.20}  {amount:>12},  {duedate} —→ {nextdate}")
        else:
            print(f"No Change: {ID}  {name:20.20}  {amount:>12},  {duedate}")

        # TODO Reorganize this.
        # I slapped the print() feedback for pay() and unpay() together to get it working quickly.
        # Maybe someday I will do it one better. Maybe not. Probably not.

        return new_e

    @staticmethod
    def unpay(e):
        """Renders the expense object ineffectual and unroutes its payment from its assigned account, then
        rolls its date to previous. If on firstpayment and already active, nothing changes."""
        new_e = e.copy()
        firstpayment = Expense.firstpayment(new_e)

        # Setup fields for user feedback
        ID, name, amount, duedate = destructure(new_e, 'id','name','amount','duedate')
        amount = format_currency(amount)
        prevdate = 'X'

        if not new_e['active'] or not firstpayment:
            new_e['active'] = True
            Account.adjust(new_e['account'], -new_e['amount'])
            if not firstpayment:
                new_e = Expense.rollbackward(new_e)
                prevdate = new_e['duedate']
            g_index['expenses'][ID] = new_e
            print(f"Reverted:  {ID}  {name:20.20}  {amount:>12},  {prevdate} ←— {duedate}")
        else:
            print(f"No Change: {ID}  {name:20.20}  {amount:>12},  {duedate}")

        return new_e

    @staticmethod
    def expand(e, days):
        """Returns a generator object which yields all expense objects with duedates extending from its
        current date through either its termination date or a date 'days' number of days beyond today."""
        expense = e.copy()
        end_date = date.today() + timedelta(days=days)
        while Expense.duedate(expense) <= end_date:
            yield expense
            if not Expense.lastpayment(expense):
                expense = Expense.rollforward(expense)
            else:
                break

    @staticmethod
    def compare_str(e):
        "Returns a string which is imperfectly comprehensive, but meaningfully hashable."
        expired = '1' if e['active'] else '0'
        duedate = date_fromstring(e['duedate']).strftime('%Y%m%d')
        amount = f"{(10**20-1) - abs(e['amount'])}"                 # This sorts by largest number first
        name = e['name']

        # String comparable
        return f"{expired}{duedate}{amount}{name}"


####################################################################################################
#### Account Type                                                                               ####
####################################################################################################

def new_account():
    "Returns a new dictionary type with fields relevant to savigns accounts."
    ID = newID()
    return {
        'id': ID,
        'name': '',
        'balance': 0
    }

####################################################################################################
#### Supporting Methods

class Account():

    @staticmethod
    def adjust(accID, amt):
        "Affects the balance of the Account object referenced by accID to the amount of amt."
        assert accID in g_index['accounts'], f"Cannot find account with ID '{accID}'."
        g_index['accounts'][accID]['balance'] += amt
        
        # TODO What is..? Rewrite this.


####################################################################################################
#### Time Manipulators                                                                          ####
####################################################################################################

####################################################################################################
#### Functions

def rolldate(d, period, regressing=False):
    "Helper to advance_date and regress_date functions."

    dirword = 'regress' if regressing else 'advance'
    standardrange = (d.day <= 28)
    leapday = (d.month == 2 and d.day == 29)
    assert period != Period.singular, f"Cannot {dirword} a date by zero: irresponsible."
    assert period != Period.monthly or standardrange, f"Cannot {dirword} a due-date by month with an ideal date of 29–31: information loss."
    assert period != Period.annual or not leapday, f"Cannot {dirword} a due-date by year with an ideal date of Feb 29th: information loss."
    # TODO These assertions should probably be formal exceptions.

    # Calc month-range for month rolls
    month = d.month if not regressing else (d.month - 1 if d.month != 1 else 12)
    m_range = monthrange(d.year, month)[1]

    # Calc year-range for annual rolls
    year = d.year + 1*(not regressing) - 1*(regressing)
    day = min(d.day, monthrange(year, month)[1])
    y_range = abs(d - date(year, d.month, day)).days
    
    switcher = {
        Period.singular: timedelta(days=0),
        Period.weekly: timedelta(days=7),
        Period.biweekly: timedelta(days=14),
        Period.monthly: timedelta(days=m_range),
        Period.annual: timedelta(days=y_range)
    }
    return d + switcher[period] if not regressing else d - switcher[period]

def advance_date(d, period):
    "Given a date and its recurrence period, returns the next occurrence date."
    return rolldate(d, period)
    
def regress_date(d, period):
    "Given a date and its recurrence period, returns the previous occurrence date."
    return rolldate(d, period, regressing=True)


####################################################################################################
#### ID Management Functions                                                                    ####
####################################################################################################

def newID():
    "Returns a 3-length numerical ID string not found in list IDs, or None if ID space is full."
    IDs = list(g_index['accounts'].keys()) + list(g_index['expenses'].keys())
    id = None
    if len(IDs) < 1000:
        potential = set(f'{i:0>3}' for i in range(0,1000))
        used = set(IDs)
        available = tuple(potential.difference(used))
        idx = random.randint(0, len(available)-1)
        id = available[idx]
    return id


####################################################################################################
#### Print Functions                                                                            ####
####################################################################################################

displaystring = ['','']

def printbuffer(s=''):
    "'Prints' to an internal buffer string. Must be shown with displayBuffer()."
    displaystring.insert(-1, s)

def displaybuffer():
    "Prints the internal buffer string to the console and clears the buffer."
    global displaystring
    if len(displaystring) > 2:
        print('\n'.join(displaystring))
    displaystring = ['','']


####################################################################################################
#### String Formatting

def horizontalrule(length):
    "Returns a string of '=' characters of some length."
    return '='*length

def format_currency(amt):
    "Given an int, returns a formatted currency string."
    sign = '-' if amt < 0 else '+'
    return "{}${}".format(sign, str(abs(amt)))

def format_expense(e):
    "Returns a single-line string describing an expense object."
    fields = ['id', 'name','important','amount','duedate']
    ID, name, important, amount, duedate = destructure(e, fields)

    date = duedate[:-6] # cuts the comma-year off
    star = '*' if Expense.lastpayment(e) else ''
    dblstar = '**' if important else ''
    amtstr = format_currency(amount)

    return f"{ID}  {date}{star:1} {name:20.20} {dblstar:2}  {amtstr:>12}"

def format_expense_full(e):
    "Returns a string describing all known information about an expense object."
    fields = ['id', 'name','account','important','amount','period','duedate','startdate','termdate','automatic']
    ID, name, account, important, amount, period, duedate, startdate, termdate, auto = destructure(e, fields)

    dblstar = '**' if important else ''
    amtstr = format_currency(amount)
    crossdate = 'x' if termdate and termdate != startdate else ''
    termdate_str = termdate if crossdate else ''
    period += '*' if auto else ''

    return f"{account} ←—  {ID}  {name:20.20} {dblstar:2}  {amtstr:>12}  {period:9}  {duedate} {crossdate} {termdate_str}"

def format_account(a):
    "Returns a single-line string describing an account object."
    fields = ['id', 'name', 'balance']
    ID, name, balance = destructure(a, fields)
    amt_str = format_currency(balance)

    return f"{ID}  {name:20.20}  {amt_str:>23}"

def format_daterange(startstr, endstr):
    "Given two date strings, returns their period as a formatted string emphasizing readability."
    # If you'd like to know what I mean, produces strings of the form:
    #   Feb – Apr           Mar, 2019 – Feb, 2020
    #   Aug 01 – 26         Jan 16 – Dec 31
    #   2019 – 2020         2020

    start = date_fromstring(startstr)
    end = date_fromstring(endstr)

    assert start <= end, "Start date must precede end date to build date-range string."

    syear, smonth, sday = start.strftime('%Y %b %d').split()
    eyear, emonth, eday = end.strftime('%Y %b %d').split()

    def monthend(d):
        return monthrange(d.year, d.month)[1]

    # Omit day numbers if they are the first and last of their respective months.
    if start.day == 1 and end.day == monthend(end):
        sday, eday = '',''

    # Omit months if they are the first an last of their respective years ~and~ day numbers are omitted.
    if start.month == 1 and end.month == 12 and not (sday and eday):
        smonth, emonth = '',''

    # Omit years if they are the same
    if start.year == end.year:
        syear, eyear = '',''
    
    # Omit end month if it is the same and year has already been omitted
    if start.month == end.month and not eyear:
        emonth = ''

    # Assembly
    def assemble_date_string(year, month, day):
        parts = [
            month,
            ' ' if month and day else '',
            day,
            ', ' if month and year else '',
            year
        ]
        return ''.join(parts)

    # Gather date strings to assemble date-range string
    startstring = assemble_date_string(syear,smonth,sday)
    endstring = assemble_date_string(eyear,emonth,eday)
    separator = '–' if endstring else ''

    # The only way startstring is blank is if the period was from start to end for a single year.
    if not startstring: startstring = start.strftime('%Y')

    return ' '.join([startstring, separator, endstring])


####################################################################################################
#### Script Variables                                                                           ####
####################################################################################################

# File path constants
path_datafolder = os.path.expandvars('%LOCALAPPDATA%\\budgetboy')
path_datafile = path_datafolder + '\\budgetboy_data'
path_backupfile = path_datafolder + '\\budgetboy_backup'

save_on_exit = True         # Whether to save changes to the working save file.
last_datafile_string = ''   # Records the loaded save-data file before changes are made.

# Global index of expense and account instances.
g_index = {
    'accounts': {},
    'expenses': {}
}

# Default savings account
g_default_account_id = '999'

general_account = new_account()
general_account['id'] = g_default_account_id
general_account['name'] = 'General Account'
g_index['accounts'][general_account['id']] = general_account

argv = sys.argv[1:]         # Passed in script arguments, minus the script's name


####################################################################################################
#### Open Script                                                                                ####
####################################################################################################

# Try to make the datafile directory if it does not exist
try:
    os.mkdir(path_datafolder)
except OSError:
    pass

# Restore backedup old datafile if told to
if get(0, argv) == 'restore-backup':
    try:
        with open(path_backupfile, 'r') as backup:
            with open(path_datafile, 'w') as datafile:
                save = backup.read()
                datafile.write(save)
        print('Backup data restored.')
    except FileNotFoundError:
        print('Failed: no backup file exists for budgetboy.')
    finally:
        exit()  # Force quit script

# Open and read the datafile, if it exists
try:
    with open(path_datafile, 'r') as datafile:
        string = datafile.read().strip()
        if string:
            g_index = json.loads(string)
            last_datafile_string = string
except FileNotFoundError:
    pass    # Nothing to read here — use default, empty expenses list
except json.decoder.JSONDecodeError as e:
    print(e)
    print('Failed: datafile for budgetboy exists, but could not be read.')
    exit()  # Force quit script


####################################################################################################
#### Processor State and Handler                                                                ####
####################################################################################################

class InputProcessorState:
    "Represents the input-looper's state at any one instant."

    def __init__(self, index, args, command_set):
        self.index = index
        self.record = None
        self.discard_record = False
        self.args = args
        self.last_arg = None
        self.command_set = command_set
        self.polling_enabled = False

    def shift(self):
        self.last_arg, self.args = shift(self.args)
        return self.last_arg

    def unshift(self):
        if self.last_arg != None:
            self.args = [self.last_arg] + self.args
            self.last_arg = None

    def clear(self):
        self.args = []

    def polling_requested(self):
        "Returns True if this state desires user-input polling fill its arguments queue."
        return (not self.args) and self.polling_enabled and not self.record

def input_processor(state):
    "The game-loop, if you will."
    while True:
        if state.polling_requested():
            try:
                state.args = shlex.split( input('> ') )
            except ValueError:
                print('Input was malformed. Try again.')

        # Execute command instruction and collect new state for next iteration.
        command = state.shift()
        state = state.command_set.switch(command)(state)
        assert type(state) == InputProcessorState, 'Command switch must return and object of type InputProcessorState.'

        # until clause
        if not state.args and not state.record and not state.polling_requested():
            break

class Switcher:
    """Value switch-case framework for matching keys to returns.
    Acceptable input for 'dictionary' are {key: value}, (key, value) and ([keys], value).
    The 'default' value is returned when switch(value) doesn't return a match."""
    def __init__(self, dictionary, default):
        self.switcher = {}
        self.default = default

        if type(dictionary) == dict:
            self.switcher = dictionary
        else:
            # Assembles a dict of strictly unique keys and non-unique functions from a list of tuples.
            for pair in dictionary:
                keys, value = pair[0], pair[1]
                if type(keys) != list and type(keys) != tuple:
                    keys = [keys]
                for key in keys:
                    assert key not in self.switcher, f"Switcher Assembly: Key '{key}' is already in use."
                    self.switcher[key] = value
    
    def switch(self, key):
        return self.switcher.get(key, self.default)


####################################################################################################
#### User-Input Interpreter: Command Sets                                                       ####
####################################################################################################

####################################################################################################
#### Global Set

def display_forecast(state):
    "Prints a 30-day from today upcoming payments update."

    forecast = 30       # Number of days to look ahead

    today = date.today()                                # Period start date
    forecast_date = today + timedelta(days=forecast)    # Period end date
    net_total = 0                                       # The sum of all expenses in the 30-day forecast (including overdue)
    expenses = []                                       # The expanded list of all expense objects within the forecast.
    section_strings = []                                # Final display strings for each section of the forecast.

    # Expand the index of expense objects into all relevant dates within the forecast period.
    # This assumes that the global index has already been updated to revolve around the current date.
    for e in g_index['expenses'].values():
        if e['active']:
            expenses.extend(Expense.expand(e, forecast))
            if e['important'] and Expense.duedate(e) > forecast_date:
                expenses.append(e)

    # Sort the resulting list
    expenses = sorted(expenses, key=lambda e: Expense.compare_str(e))

    # Divide the list of expenses into sections
    e_overdue = [ e for e in expenses if Expense.duedate(e) < today ]
    e_forecast = [ e for e in expenses if today <= Expense.duedate(e) <= forecast_date ]
    e_important = [ e for e in expenses if forecast_date < Expense.duedate(e) ]

    # Build the display string

    # Returns the string s with duplicate duedates detailed by expenses replaced with whitespace.
    def simplify_dates(expenses, s):
        date_strings = { e['duedate'][:-6]: 0 for e in expenses }.keys()
        blank = '      '
        for dt in date_strings:
            li = s.rsplit(dt, s.count(dt)-1)
            s = blank.join(li)
        return s

    # Header
    printbuffer(f'{date_tostring(today)} — Next 30 Days:')
    printbuffer()

    # Overdue expenses
    if e_overdue:
        lines = ['Overdue:']
        lines.extend( [format_expense(e) for e in e_overdue] )
        net_total += sum([ int(e['amount']) for e in e_overdue ])
        string = simplify_dates(e_overdue, '\n'.join(lines))
        if string:
            section_strings.append(string)
    
    # Expenses through the 30-day forecast
    if e_forecast:
        lines = [ format_expense(e) for e in e_forecast ]
        net_total += sum([ int(e['amount']) for e in e_forecast ])
        net_str = format_currency(net_total)
        lines.append('')
        lines.append(f"{'Net Total':>22} {net_str:>27}")
        string = simplify_dates(e_forecast, '\n'.join(lines))
        if string:
            section_strings.append(string)

    # Important (marked) expenses upcoming.
    if e_important:
        lines = [ format_expense(e) for e in e_important ]
        string = simplify_dates(e_important, '\n'.join(lines))
        if string:
            section_strings.append(string)

    # Include account summaries
    lines = [ format_account(a) for a in g_index['accounts'].values() ]
    string = '\n'.join(lines)
    if string:
        section_strings.append(string)

    # Final display (buffer print)
    if section_strings:
        printbuffer('\n\n'.join(section_strings))
    else:
        printbuffer('No items listed.')

    displaybuffer()
    return state

def display_all_expenses(state):
    "Prints all objects in the expenses list, then all accounts."

    expenses = g_index['expenses'].values()
    expenses = sorted(expenses, key=lambda e: Expense.compare_str(e))
    for e in expenses:
        printbuffer(format_expense_full(e))

    printbuffer()

    accounts = g_index['accounts'].values()
    for a in accounts:
        printbuffer(format_account(a))

    displaybuffer()
    return state

def display_projection(state):
    "Displays an itemized expense list for today through some date."

    # Get the projection date in days from today from the user.
    s = state.shift()
    today = date.today()
    default_future_date = today + timedelta(days=30)            # Not necessary, but neat trick for itemized list instead of date view.
    future_date = parse_date(s) if s else default_future_date
    days = (future_date - today).days if future_date else None

    # Malformed request handling
    if days == None:
        print(f"Could not interpret '{s}' as a date.")
    elif days < 0:
        print(f"Cannot project into the past.")
    # Date was valid, proceed
    else:
        net_total = 0
        itemized_budget = []

        # For all active expenses, sum all occurrences between now and future.
        active_expenses = list(filter(lambda e: e['active'], g_index['expenses'].values()))
        for e in active_expenses:
            li = list(Expense.expand(e, days))
            ID = e['id']
            name = e['name']
            count = f'x{len(li)}'
            sum_total = sum([ e['amount'] for e in li ])
            sum_str = format_currency(sum_total)
            display_str = f"{ID}  {name:20.20}  {count:>3} = {sum_str:>13}"
            itemized_budget.append([display_str, sum_total])
            net_total += sum_total
        
        # Cull and sort items by largest sum
        itemized_budget = list(filter(lambda p: p[1] != 0, itemized_budget))
        itemized_budget = [ p[0] for p in sorted(itemized_budget, key=lambda p: abs(p[1]), reverse=True) ]

        net_str = format_currency(net_total)
        today_str = date_tostring(today)
        future_str = date_tostring(future_date)
        
        # Empty budget message.
        if not itemized_budget:
            itemized_budget.append(f"No expenses during this period.")

        # Formal print
        printbuffer("{}".format(format_daterange(today_str, future_str)))
        printbuffer()
        printbuffer('\n'.join(itemized_budget))
        printbuffer()
        printbuffer(f"{'Net Total':>30}  {net_str:>14}")

        # TODO Simulate payments into accounts and display those here, too.
        # 999 General Account                   +$3866
        # 442 New PC Savings Account             +$550
        #
        # I could possibly copy the accounts list and make deposits into those based on keys from expenses.
        # I cannot use Account.adjust() because that's not how it was written... hm.

        displaybuffer()

    state.clear()
    return state

def create_new_expense(state):
    ""
    state.record = new_expense()
    state.discard_record = False
    state.command_set = expense_command_set
    return state

def create_new_account(state):
    ""
    state.record = new_account()
    state.discard_record = False
    state.command_set = account_command_set
    return state

def edit_record(state):
    ID = parse_idnumber(state.shift())

    if not ID:
        state.clear()

    elif ID in g_index['expenses'].keys():
        state.record = g_index['expenses'][ID]
        state.discard_record = False
        state.command_set = expense_command_set

    elif ID in g_index['accounts'].keys():
        state.record = g_index['accounts'][ID]
        state.discard_record = False
        state.command_set = account_command_set

    else:
        print(f"No item with ID '{ID}' found in record.")
        state.clear()

    return state

def del_records(state):
    "Attempts to delete from the record the expense object described by ID-string via the next user argument."

    expenses = g_index['expenses']
    accounts = g_index['accounts']

    def delete(index, key, display, unlink=False):
        if key == '999':
            print("Cannot delete the global account.")
        else:
            if unlink:
                linked_expenses = filter(lambda e: e['id'] == key, expenses.values())
                for e in linked_expenses:
                    e['id'] = g_default_account_id
            print( display(index[key]) )
            print('Deleted.')
            del index[key]

    while (arg := state.shift()):
        ID = parse_idnumber(arg)
        if ID in accounts.keys():
            delete(accounts, ID, format_account, unlink=True)
        elif ID in expenses.keys():
            delete(expenses, ID, format_expense_full)
        else:
            print(f"No item exists with the ID '{ID}'.")

    state.clear()
    return state

def pay_expense(state):
    """For each valid ID submitted by the user, rolls the associated expense's date forward and adds its sum
    to its linked account."""
    expenses = g_index['expenses']
    while (arg := state.shift()):
        ID = parse_idnumber(arg)
        if ID in expenses.keys():
            Expense.pay(expenses[ID])
        else:
            print(f"No expense exists with the ID '{ID}'.")
    state.clear()
    return state

def undo_pay_expense(state):
    """For each valid ID submitted by the user, rolls the associated expense's date back and subtracts its
    sum from its linked account."""
    expenses = g_index['expenses']
    while (arg := state.shift()):
        ID = parse_idnumber(arg)
        if ID in expenses.keys():
            Expense.unpay(expenses[ID])
        else:
            print(f"No expense exists with the ID '{ID}'.")
    state.clear()
    return state

def playground_mode(state):
    "Enables free-edit mode by turning on continuous polling and disabling saving."
    global save_on_exit
    save_on_exit = False
    state.polling_enabled = True
    state.clear()
    return state

def end_playground_mode(state):
    "Disenables free-edit mode by turning of continuous polling."
    if state.polling_enabled:
        state.polling_enabled = False
        state.clear()
    return state

def reenable_save(state):
    "Re-enables saving on exit, if it was disabled already (by playground mode)."
    global save_on_exit
    if state.polling_enabled:
        save_on_exit = True
        state.clear()
    return state

def display_helptext(state):
    "Prints the script's manual, if you will."
    print(helptext)
    state.clear()
    return state

global_command_set = Switcher({
    None: display_forecast,
    'all': display_all_expenses,
    'project': display_projection,
    'pay': pay_expense,
    'undo-pay': undo_pay_expense,
    'add': create_new_expense,
    'new-account': create_new_account,
    'del': del_records,
    'edit': edit_record,
    'playground': playground_mode,
    'done': end_playground_mode,
    'enable-saving': reenable_save,
    'help': display_helptext
    },
    lambda state: state
    )


####################################################################################################
#### New Expense Set

def expense_discard(state, msg):
    """Feedback and consequence pair for convenience. Any error in user input for new expense should
    result in discarding the data and requesting a second attempt."""
    print(msg)
    state.discard_record = True

def expense_done(state):
    "New expense object creation is finished: validate and add, or discard."
    # Date fixing — duedate setting superceeds startdate
    duedate = date_fromstring(state.record['duedate'])
    startdate = date_fromstring(state.record['startdate'])
    termdate = date_fromstring(state.record['termdate']) if state.record['termdate'] else None
    if duedate < startdate:
        startdate = duedate
    if state.record['period'] == Period.singular:
        termdate = startdate = duedate
    state.record['duedate'] = date_tostring(duedate)
    state.record['startdate'] = date_tostring(startdate)
    state.record['termdate'] = date_tostring(termdate) if termdate else None

    # Final validation check
    if state.record['name'] == '':
        expense_discard(state, "This expense was never named.")
    if state.record['amount'] == 0:
        expense_discard(state, "An amount wasn't given for this expense: has a value of $0.")
    if startdate > duedate or termdate and duedate > termdate:
        expense_discard(state, f"The duedate and active period do not align: s={startdate} → d={duedate} → t={termdate}")
    
    # Make sure duedate matches allowable dates.
    if state.record['period'] == Period.monthly and 29 <= duedate.day <= 31:
        expense_discard(state, f"A duedate of 29–31 for a monthly recurrence period is not allowed: given {duedate}")
    if state.record['period'] == Period.annual and duedate.month == 2 and duedate.day == 29:
        expense_discard(state, f"A duedate on leapday for an annual recurrence period is not allowed: given {duedate}")

    # Feedback to user, or final add
    if state.discard_record:
        print("New expense was not added.")
    else:
        state.index['expenses'][state.record['id']] = state.record

    # Reset interpreter to global set
    state.record = None
    state.command_set = global_command_set
    return state

def expense_setinterpretable(state):
    "Last user token is an unknown string: interpreted as a date, amount or name."
    arg = state.last_arg
    # Try to set duedate
    if parse_date(arg):
        state.unshift()
        expense_setdate(state, 'duedate')
    # Try to set amount
    elif re.search(regex_currency, arg):
        state.record['amount'] = parse_amount(arg)
    # Assume it's a name then
    else:
        state.record['name'] = arg
    return state

def expense_setaccount(state):
    "Next user token is an account ID to link this expense to."
    arg = state.shift()
    if not arg.isnumeric() or not len(arg) == 3:
        expense_discard(state, f"The string '{arg}' is not interpretable as an ID (length 3, numbers only).")
    else:
        ID = parse_idnumber(state.shift())
        if ID not in state.index['accounts']:
            expense_discard(state, f"No account with the ID '{ID}' was found.")
        else:
            state.record['account'] = ID
    
    return state

def expense_setdate(state, field):
    arg = state.shift()
    if (d := parse_date(arg)):
        state.record[field] = date_tostring(d)
    else:
        expense_discard(state, f"Token '{arg}' could not be parsed as a date.")
    return state

def expense_setstartdate(state):
    return expense_setdate(state, 'startdate')

def expense_settermdate(state):
    return expense_setdate(state, 'termdate')

def expense_setperiod(state, period):
    state.record['period'] = period
    if period != Period.singular and state.record['termdate'] == state.record['startdate']:
        state.record['termdate'] = None
    return state

def expense_setperiod_single(state):
    return expense_setperiod(state, Period.singular)
def expense_setperiod_week(state):
    return expense_setperiod(state, Period.weekly)
def expense_setperiod_biweek(state):
    return expense_setperiod(state, Period.biweekly)
def expense_setperiod_month(state):
    return expense_setperiod(state, Period.monthly)
def expense_setperiod_annual(state):
    return expense_setperiod(state, Period.annual)

def expense_setimportant(state):
    state.record['important'] = True
    return state

def expense_setnotimportant(state):
    state.record['important'] = False

def expense_setautomatic(state):
    state.record['automatic'] = True
    return state

def expense_setnotautomatic(state):
    state.record['automatic'] = False
    return state

expense_command_set = Switcher((
    (None, expense_done),
    (['acc', 'account'], expense_setaccount),
    (['s', 'singular', 'one-time', 'once'], expense_setperiod_single),
    (['w', 'week', 'weekly'], expense_setperiod_week),
    (['b', 'biweek', 'biweekly', 'bi-weekly'], expense_setperiod_biweek),
    (['m', 'month', 'monthly'], expense_setperiod_month),
    (['y', 'year', 'yearly', 'annual', 'annually'], expense_setperiod_annual),
    (['start', 'startdate', 'start-date'], expense_setstartdate),
    (['term', 'termdate', 'term-date', 'terminate'], expense_settermdate),
    (['*', '**', 'important', 'always-show'], expense_setimportant),
    (['common', 'normal-show'], expense_setnotimportant),
    (['auto', 'automatic', 'autopay'], expense_setautomatic),
    (['manual', 'manualpay'], expense_setnotautomatic)
    ),
    expense_setinterpretable
    )


####################################################################################################
#### New Account Set

def account_done(state):
    "New account object creation is finished: validate and add, or discard."
    # Final validation check
    if state.record['name'] == '':
        print("This account was never named.")
        state.discard_record = True

    # Feedback to user, or final add.
    if state.discard_record:
        print("New account was not added.")
    else:
        state.index['accounts'][state.record['id']] = state.record
    
    # Reset interpreter to global set
    state.record = None
    state.command_set = global_command_set
    return state

def account_setinterpretable(state):
    "Last user token is an unknown string: interpreted as a name or an account balance."
    arg = state.last_arg
    # Try to set balance
    if re.search(regex_currency, arg):
        state.record['balance'] = parse_amount(arg)
    # Assume it's a name then.
    else:
        state.record['name'] = arg
    return state

account_command_set = Switcher((
    (None, account_done),
    ),
    account_setinterpretable
    )


####################################################################################################
#### Run Script                                                                                 ####
####################################################################################################

####################################################################################################
#### General Support Functions

def update_global_index():
    "Brings the official record up to the current date."
    today = date.today()
    overdue_begin_date = today - timedelta(days=7)

    past_overdue = lambda e: not e['automatic'] and Expense.duedate(e) < overdue_begin_date
    not_current = lambda e: e['automatic'] and Expense.duedate(e) < today

    for e in g_index['expenses'].values():
        while e['active'] and (past_overdue(e) or not_current(e)):
            e = Expense.pay(e)

def clean_global_index():
    """Removes outdated expense objects from the global index.
    This function assumes the global index has been updated to revolve around the current date."""
    today = date.today()
    historical_cutoff = today - timedelta(days=365)                 # I don't care about leap-years
    validator = lambda kv: Expense.duedate(kv[1]) >= historical_cutoff
    g_index['expenses'] = dict(filter( validator, g_index['expenses'].items() ))


####################################################################################################
#### Execute

update_global_index()
clean_global_index()

processor_state = InputProcessorState(g_index, argv, global_command_set)
input_processor(processor_state)


####################################################################################################
#### Close Script                                                                               ####
####################################################################################################

# Save the program and backup the old data collected before program execution.
#save_on_exit = False
if save_on_exit:
    with open(path_backupfile, 'w') as backup:  # Save the last-known-working-copy of the datafile.
        backup.write(last_datafile_string)
    with open(path_datafile, 'w') as datafile:  # Save the new changes to the working datafile.
        save = json.dumps(g_index)
        datafile.write(save)