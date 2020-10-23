# budgetboy

[picture]

Tell it what your bills are and it will tell you when to pay them forever. It can also keep track of income payments, heretofore known as a "negative bill," and account balances (sort of: see footnote).

The script can project your budget far into the future with an itemized list of your expenses and negative bills between today and some date, showing you what you could earn in so much time if you'd just stop spending it on dumb.

And finally, "playground mode" will let you affect your budget in experimental ways without destroying the good one you have now.

It's written in Python, but it's trivial to setup a shell script which does the extra/redundant typing for you. I'll probably include one in this repository at some point.

Call the script:

```powershell
py budgetboy.py help
```

To print an explanation on how to use it.

(Note that this script is separate from any financial services you might use; it is simply a planning tool.)

#### **The Issue With Accounts:**

There is no "transfer" action. As this was written for *me,* there probably won't be one, either.

If you have two accounts, "General" and "Savings," and you want to represent a $50 deposit *from* General *into* Savings, you would add an expense of -50 linked to the savings account. Savings will accumulate a negative number, but the calendar won't think you make $50 more than you do. It will actually think you make $50 less, which is.. sensible, I suppose.