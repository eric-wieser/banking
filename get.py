#! python3
"""
Usage:
	get.py [--ff] <from> <to> <banks>...

"""
import sys
import re
from getpass import getpass
from datetime import datetime

from docopt import docopt
from selenium import webdriver
from dateutil.parser import parse as parse_date

import config

def find_account(q):
	from config import accounts

	matches = [a for a in config.accounts if re.match(q, a.name)]
	if len(matches) == 1:
		return matches[0]
	elif matches:
		raise ValueError("Multiple matches for {}: {}".format(
			q, ', '.join(m.name for m in matches)
		))
	else:
		raise ValueError("No matches for {}".format(q))


opts = docopt(__doc__)

if opts['--ff']:
	driver_cls = webdriver.Firefox
else:
	driver_cls = webdriver.PhantomJS

from_date = parse_date(opts['<from>'])
to_date = parse_date(opts['<to>'])

accounts = [find_account(b) for b in opts['<banks>']]

print("""
Downloading transactions
	after {} (inclusive)
	until {} (exclusive)
	from {}
""".format(
	from_date,
	to_date,
	', '.join('{!r}'.format(acc.name) for acc in accounts)
))

# force a credential check
config.cred_store.keyring_key
for a in accounts:
	a.auth_from_store(config.cred_store)



qif_fix = lambda qif: re.sub(rb'(?m)(^D.*/)20(\d\d\r?)$', rb'\1\2', qif)

for acc in accounts:
	print("Logging in to {}".format(acc.name))
	acc.login(driver_cls)
	print("Getting statements for {}".format(acc.name))
	for f, t, qif in acc.get_qif_statements(from_date, to_date):
		print('  Downloaded {} to {}'.format(f, t))
		with open('downloads/{} {:%Y-%m-%d} {:%Y-%m-%d}.qif'.format(acc.name, f, t), 'wb') as f:
			f.write(qif_fix(qif))