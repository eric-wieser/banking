"""
Usage:
	get.py [--ff] <banks>...

"""
import sys
import re
from getpass import getpass
from datetime import datetime

from docopt import docopt
from selenium import webdriver

from config import accounts

def find_account(q):
	matches = [a for a in accounts if re.match(q, a.name)]
	if len(matches) == 1:
		return matches[0]
	elif matches:
		raise ValueError("Multiple matches for {}: {}".format(
			q, ', '.join(a.name for a in accounts)
		))
	else:
		raise ValueError("No matches for {}".format(q))


opts = docopt(__doc__)

if opts['--ff']:
	driver_cls = webdriver.Firefox
else:
	driver_cls = webdriver.PhantomJS

from_date = datetime(2014, 9, 6)
to_date = datetime(2015, 3, 5)


for b in opts['<banks>']:
	acc = find_account(b)
	print("Getting statements for {}".format(acc.name))
	acc.login(driver_cls)
	for f, t, qif in acc.get_qif_statements(from_date, to_date):
		with open('downloads/{} {:%Y-%m-%d} {:%Y-%m-%d}.qif'.format(acc.name, f, t), 'wb') as f:
			f.write(qif)