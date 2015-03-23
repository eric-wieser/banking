from abc import ABCMeta, abstractmethod

class Account(object, metaclass=ABCMeta):
	def __init__(self, name):
		self.name = name

	@abstractmethod
	def get_qif_statements(self, from_date, to_date):
		pass


class BankAccount(Account):
	def __init__(self, name, sort_code, account_no):
		super().__init__(name);
		self.sort_code = sort_code
		self.account_no = account_no

	@property
	def id(self):
		return self.sort_code, self.account_no
