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
		driver.implicitly_wait(5)
		field_wrapper = driver.find_element_by_css_selector('#frmentermemorableinformation1')
		char_es = field_wrapper.find_elements_by_css_selector('.formField div.clearfix')
		if len(char_es) != 3:
			raise ValueError("Only got {}".format(char_es))
		for char_e in char_es:
			label_e = char_e.find_element_by_css_selector('label')
			select_e = char_e.find_element_by_css_selector('select')

			char_n = int(re.search(r'\d+', label_e.text).group()) - 1
			Select(select_e).select_by_value(
				'&nbsp;' + self.mem_info[char_n]
			)

		driver.find_element_by_id('frmentermemorableinformation1:btnContinue').click()


		if 'Interstitial' in driver.title:
			btn = driver.find_elements_by_css_selector('.primaryBtn')
			assert len(btn) == 1
			btn = btn[0]
			# assert 'continue' in btn.text.lower(), btn.text
			btn.click()

		# choose account
		driver.implicitly_wait(3)
		accounts = (driver
			.find_element_by_css_selector('#des-m-sat-xx-1')
			.find_elements_by_css_selector('.des-m-sat-xx-account-information')
		)

		account_map = {}
		for acc in accounts:
			dds = acc.find_elements_by_css_selector('dd')
			sc = dds[1].text.strip()
			an = dds[2].text.strip()
			account_map[sc, an] = acc

		# choose our account
		try:
			acc = account_map[self.id]
		except KeyError:
			raise ValueError("Could not find account {} {}: accounts found were {}".format(
				self.sort_code, self.account_no, account_map.keys()
			))
		acc.find_element_by_css_selector('a.ViewOnlineStatementsAnchor1').click()


	def get_qif_statements(self, from_date, to_date):
		driver = self.driver

		# open download form
		try:
			link = driver.find_element_by_id('pnlgrpStatement:conS1:lkoverlay')
			download_url = urllib.parse.urljoin(driver.current_url, link.get_attribute('href'))
		except:
			download_url = 'https://secure.lloydsbank.co.uk/personal/a/viewproductdetails/ress/m44_exportstatement_fallback.jsp'
		driver.get(download_url)

		# set options
		Select(
			driver.find_element_by_id('export-format')
		).select_by_visible_text('Quicken 98 and 2000 and Money (.QIF)')

		# yield statements in 3-month intervals
		while from_date < to_date:
			next_date = from_date + timedelta(days=84)
			if next_date > to_date:
				next_date = to_date

			yield from_date, next_date, self._get_single_statement(from_date, next_date)

			from_date = next_date

		# return to index
		driver.find_element_by_css_selector('.non-js-back-button').click()

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

		to_date_incl = to_date - timedelta(days=1)

		params.update({
			'searchDateTo':    '{:%d/%m/%Y}'.format(to_date_incl),
			'searchDateFrom':  '{:%d/%m/%Y}'.format(from_date),
			'exportDateRange': 'between',

			'export-statement-form:btnQuickTransferRetail': 'Export'
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
