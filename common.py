
class Account(object):
	def __init__(self, sort_code, account_no):
		self.sort_code = sort_code
		self.account_no = account_no

	@property
	def id(self):
	    return self.sort_code, self.account_no

