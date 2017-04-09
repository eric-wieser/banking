import urllib.parse
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests

from common import Account

class TescoAccount(Account):
	def __init__(self, name):
		super().__init__(name)
		self.auth(None, None, None)

	def auth(self, user, password, security_number):
		self.user = user
		self.password = password
		self.security_number = security_number

	def login(self, driver_cls):
		self.driver = driver = driver_cls()

		driver.get('https://www.tescobank.com/sss/authcc')

		driver.implicitly_wait(3)
		elem = driver.find_element_by_id('login-uid')
		elem.send_keys(self.user)
		elem.send_keys(Keys.RETURN)

		# check phrase
		try:
			phrase = driver.find_element_by_css_selector('#PAMPhrase')
			print(phrase.text.strip())
		except NoSuchElementException:
			print("No magic phrase")

		# login
		digit_es = [
			driver.find_element_by_id('DIGIT{}'.format(1+i))
			for i in range(6)
		]
		for i, digit_e in enumerate(digit_es):
			if not digit_e.get_attribute('disabled'):
				digit_e.send_keys(self.security_number[i])

		try:
			passcode_e = driver.find_element_by_id('PASSWORD')
			passcode_e.send_keys(self.password)
		except NoSuchElementException:
			print("no password yet")

		driver.find_element_by_id('NEXTBUTTON').click()

		if driver.find_element_by_id('login-send-ota'):
			button = driver.find_element_by_css_selector('[data-value="SENDMOBILE"]')
			assert button
			button.click()

			WebDriverWait(driver, 1).until(lambda d: 'One time' in d.title)

			code = input("OTP sent to mobile: ")

			driver.find_element_by_id('OTA').send_keys(code)
			driver.find_element_by_id('NEXTBUTTON').click()

			driver.find_element_by_id('PASSWORD').send_keys(self.password)
			driver.find_element_by_css_selector('#DOWNLOADAID_Y + *').click()

			driver.find_element_by_id('NEXTBUTTON').click()

		driver.implicitly_wait(5)

		# list accounts
		accounts = driver.find_elements_by_css_selector('#sv-creditcard-product > div')

		# navigate to the first one
		accounts[0].find_element_by_css_selector('#navigate button').click()

		self.driver = driver

	def get_qif_statements(self, from_date, to_date):
		driver = self.driver

		# navigate to the transactions page
		ui_root_url = 'https://onlineservicing.creditcards.tescobank.com/Tesco_Consumer/'
		WebDriverWait(driver, 10).until(lambda d: d.current_url.startswith(ui_root_url))
		driver.get(ui_root_url + 'ViewTransactions.do')

		# process the list of statements into date ranges
		statement_sel = Select(driver.find_element_by_css_selector('[name="cycleDate"]'))
		options = statement_sel.options
		statements = []
		for o1, o2 in zip(options, options[1:]):
			d1 = o1.get_attribute('value')
			d2 = o2.get_attribute('value')

			# add one day, since statements are issued at day ends
			if d1 == '00':
				d1 = datetime.max
			else:
				d1 = datetime.fromtimestamp(int(d1) / 1000) + timedelta(days=1)
			d2 = datetime.fromtimestamp(int(d2) / 1000) + timedelta(days=1)

			statements.append(
				(d2, d1, o1)
			)

		# find the active statements
		statements = [
			(d_s, d_e, o.get_attribute('value'))
			for d_s, d_e, o in statements
			if from_date < d_e and d_s < to_date
		]

		# yield all the statements
		for d_s, d_e, v in statements:
			s = self._get_single_statement(v)
			if s:
				yield d_s, d_e, s

	def _get_single_statement(self, v):
		driver = self.driver

		# choose the date range
		Select(driver.find_element_by_css_selector('[name="cycleDate"]')).select_by_value(v)
		driver.find_element_by_css_selector('[name="TransactionsForm"] input[type="submit"]').click()

		# check we have data
		try:
			driver.find_element_by_css_selector('#displayTransaction .dispute')
			return None
		except NoSuchElementException:
			pass

		# select the download type
		Select(driver.find_element_by_css_selector('[name="downloadType"]')).select_by_value('qif')

		# simulate submitting the form
		params, target_url, user_agent = driver.execute_script("""
			return (function() {
				var form = document.forms.DownLoadTransactionForm;
				var es = [].map.call(form.elements, function(e) {
					return [e.name, e.value];
				});
				return [es, form.getAttribute('action'), navigator.userAgent];
			})();
		""")
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
