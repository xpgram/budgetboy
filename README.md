# budgetboy

A simple CLI program.

It keeps track of your bills, your earnings, and your balance, as well as allowing you to project your budget into the future showing you what you could earn in so much time if you'd stop spending it on dumb.

It's written in Python, but it's trivial to setup a shell script which does the extra/redundant typing for you. I'll probably include one in this repository at some point.

Currently, it does these things:
 - Maintains a relative calendar of upcoming bills and incomes.
 - Reports the net total of earnings against expenses.
 - Can generate a calendar with this net total over long periods of time into the future.
 - Easy add/remove methods for incomes and expenses. Particularly of one-time expenses which significantly affect your savings.

In the future, it will do these things:
 - A 'what if' mode which will allow heavy modification of the budget without affecting the real one.
 - Inform you of recent/past-due bills in case you weren't paying attention.
 - Allow setup of savings sums which can be 'auto-deposited into' or 'withdrawn from' to simulate what you ought to be doing in real life.
 - Display a condensed, itemized budget instead of the calendar view for long periods of time.
 - Have a help screen.
 
 In addition to several QOL adjustments I plan on making.
   
 This script, obviously, does not handle your money for you. It's simply a planning tool.
