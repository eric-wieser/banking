import re
import urllib.parse
from datetime import timedelta

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
import requests

from common import BankAccount

class LloydsAccount(BankAccount):
	def __init__(self, name, sort_code, account_no):
		super().__init__(name, sort_code, account_no)
		self.auth(None, None, None)
		self.driver = None

	def auth(self, user, password, mem_info):
		self.user = user
		self.password = password
		self.mem_info = mem_info


	def login(self, driver_cls=webdriver.PhantomJS):
		self.driver = driver = driver_cls()

		driver.get('https://online.lloydsbank.co.uk/personal/logon/login.jsp')

		# login
		driver.implicitly_wait(3)
		user_e = driver.find_element_by_id('frmLogin:strCustomerLogin_userID')
		pass_e = driver.find_element_by_id('frmLogin:strCustomerLogin_pwd')
		user_e.send_keys(self.user)
		pass_e.send_keys(self.password)
		pass_e.send_keys(Keys.RETURN)

		# secret word
		char_es = driver.find_elements_by_css_selector('#frmentermemorableinformation1 .formField div.clearfix')
		for char_e in char_es:
			label_e = char_e.find_element_by_css_selector('label')
			select_e = char_e.find_element_by_css_selector('select')

			char_n = int(re.search(r'\d+', label_e.text).group()) - 1
			Select(select_e).select_by_value(
				'&nbsp;' + self.mem_info[char_n]
			)

		driver.find_element_by_id('frmentermemorableinformation1:btnContinue').click()


		if 'Interstitial' in driver.title:
			driver.find_element_by_id('continueLnk1').click()

		# choose account
		driver.implicitly_wait(3)
		accounts = (driver
			.find_element_by_css_selector('#lstAccLst')
			.find_elements_by_css_selector('.accountDetails')
		)

		account_map = {}
		for acc in accounts:
			num_e = acc.find_element_by_css_selector('.numbers')
			if num_e.text:
				sc, an = [
					x.strip()
					for x in acc.find_element_by_css_selector('.numbers').text.split(',')
				]

				account_map[sc, an] = acc

		# choose our account
		try:
			acc = account_map[self.id]
		except KeyError:
			raise ValueError("Could not find account {} {}: accounts found were {}".format(
				self.sort_code, self.account_no, account_map.keys()
			))
		acc.find_element_by_css_selector('a').click()


	def get_qif_statements(self, from_date, to_date):
		driver = self.driver

		# open download form
		link = driver.find_element_by_id('pnlgrpStatement:conS1:lkoverlay')
		download_url = urllib.parse.urljoin(driver.current_url, link.get_attribute('href'))
		driver.get(download_url)

		# set options
		driver.find_element_by_id('frmTest:rdoDateRange:1').click()
		Select(
			driver.find_element_by_id('frmTest:strExportFormatSelected')
		).select_by_visible_text('Quicken 98 and 2000 and Money (.QIF)')

		# yield statements in 3-month intervals
		while from_date < to_date:
			next_date = from_date + timedelta(days=84)
			if next_date > to_date:
				next_date = to_date

			yield from_date, next_date, self._get_single_statement(from_date, next_date)

			from_date = next_date

		# return to index
		driver.find_element_by_id('frmTest:lnkCancel1').click()


	def _get_single_statement(self, from_date, to_date):
		driver = self.driver

		params, target_url, user_agent = driver.execute_script("""
			return (function() {
				var form = document.forms[0];
				var es = [].map.call($(form).serializeArray(), function(e) {
					return [e.name, e.value];
				});
				return [es, form.getAttribute('action'), navigator.userAgent];
			})();
		""")
		params = dict(params)

		params.update({
			'frmTest:dtSearchToDate':       '{:%d}'.format(to_date),
			'frmTest:dtSearchToDate.month': '{:%m}'.format(to_date),
			'frmTest:dtSearchToDate.year':  '{:%Y}'.format(to_date),
			'frmTest:dtSearchFromDate':       '{:%d}'.format(from_date),
			'frmTest:dtSearchFromDate.month': '{:%m}'.format(from_date),
			'frmTest:dtSearchFromDate.year':  '{:%Y}'.format(from_date),

			'frmTest:btn_Export': ''
		})


		cookies = {
			c['name']: c['value']
			for c in driver.get_cookies()
		}

		r = requests.post(
			urllib.parse.urljoin(driver.current_url, target_url),
			data=params,
			cookies=cookies,
			headers = {
				'User-Agent': user_agent,
				'Referer': driver.current_url
			}
		)

		return r.content


	def _get_single_statement_new(self, from_date, to_date):
		driver = self.driver

		params, target_url, user_agent = driver.execute_script("""
			return (function() {
				var form = document.forms[0];
				var es = [].map.call($(form).serializeArray(), function(e) {
					return [e.name, e.value];
				});
				return [es, form.getAttribute('action'), navigator.userAgent];
			})();
		""")

		params = dict(params)
		from pprint import pprint as print
		params.update({
			'frmTest:btn_Export': '',

			'frmTest:dtSearchToDate':       '{:%Y}'.format(to_date),
			'frmTest:dtSearchToDate.month': '{:%m}'.format(to_date),
			'frmTest:dtSearchToDate.year':  '{:%d}'.format(to_date),
			'frmTest:dtSearchFromDate':       '{:%Y}'.format(from_date),
			'frmTest:dtSearchFromDate.month': '{:%m}'.format(from_date),
			'frmTest:dtSearchFromDate.year':  '{:%d}'.format(from_date)
		})
		print(params)

		cookies = { c['name']: c['value'] for c in driver.get_cookies()	}
