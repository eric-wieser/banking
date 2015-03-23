import getpass
from abc import ABCMeta, abstractmethod
from inspect import signature
from collections import OrderedDict

import keyring.backend

class Account(object, metaclass=ABCMeta):
	def __init__(self, name):
		self.name = name

	@abstractmethod
	def get_qif_statements(self, from_date, to_date):
		pass

	def auth_from_store(self, store):
		sig = signature(self.auth)
		creds = OrderedDict(
			(param.name, store.get_password(self.name, param.name))
			for param in sig.parameters.values()
		)

		not_set = [k for k, v in creds.items() if v is None]
		if not_set:
			print("Missing credentials for account '{}'".format(self.name))
			for k in not_set:
				creds[k] = getpass.getpass('  Enter {}: '.format(k))
				store.set_password(self.name, k, creds[k])

		bound = sig.bind_partial()
		for k, v in creds.items():
			bound.arguments[k] = v

		return self.auth(*bound.args, **bound.kwargs)


class BankAccount(Account):
	def __init__(self, name, sort_code, account_no):
		super().__init__(name);
		self.sort_code = sort_code
		self.account_no = account_no

	@property
	def id(self):
		return self.sort_code, self.account_no
