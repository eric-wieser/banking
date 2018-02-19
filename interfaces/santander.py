import urllib.parse
from datetime import timedelta

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests

from common import BankAccount

class SantanderAccount(BankAccount):
	def __init__(self, name, sort_code, account_no):
		super().__init__(name, sort_code, account_no)
		self.auth(None, None, None)
		self.driver = None

	def auth(self, user, password, reg_num):
		self.user = user
		self.password = password
		self.reg_num = reg_num

	def login(self, driver_cls=webdriver.PhantomJS):
		self.driver = driver = driver_cls()

		driver.get('https://retail.santander.co.uk/LOGSUK_NS_ENS/BtoChannelDriver.ssobto?dse_operationName=LOGON&dse_processorState=initial&redirect=S')

		driver.implicitly_wait(3)
		elem = driver.find_element_by_id('infoLDAP_E.customerID')
		elem.send_keys(self.user)
		elem.send_keys(Keys.RETURN)

		try:
			challenge = driver.find_element_by_css_selector('[id="cbQuestionChallenge.responseUser"]')
			question = driver.find_element_by_css_selector('form .form-item .data').text.strip()
			answer = input("Verifying new computer:\n\t{}? ".format(question))
			challenge.send_keys(answer)
			challenge.send_keys(Keys.RETURN)
		except NoSuchElementException as e:
			print("Verification not needed?")

		try:
			phrase = driver.find_element_by_css_selector('.imgSection span')
			print(phrase.text.strip())
		except NoSuchElementException:
			print("No magic phrase")


		# login
		passcode_e = driver.find_element_by_id('authentication.PassCode')
		reg_num_e = driver.find_element_by_id('authentication.ERN')
		passcode_e.send_keys(self.password)
		reg_num_e.send_keys(self.reg_num)
		passcode_e.send_keys(Keys.RETURN)

		# list accounts
		accounts = (driver
			.find_element_by_css_selector('.accountlist')
			.find_elements_by_css_selector('li .info')
		)
		account_map = {
			tuple(acc.find_element_by_css_selector('.number').text.split(' ')): acc
			for acc in accounts
		}

		# choose our account
		acc = account_map[self.id]
		acc.find_element_by_css_selector('a').click()


	def get_qif_statements(self, from_date, to_date):
		driver = self.driver

		# upper bound is inclusive for santander
		to_date_incl = to_date - timedelta(days=1)

		download_link = WebDriverWait(driver, 10).until(
	        EC.presence_of_element_located((By.CSS_SELECTOR, ".download"))
	    )
		download_link.click()

		Select(driver.find_element_by_css_selector('#sel_downloadto')).select_by_visible_text('Intuit Quicken (QIF)')


		from_day = driver.find_element_by_css_selector('[name="downloadStatementsForm.fromDate.day"]')
		from_month = driver.find_element_by_css_selector('[name="downloadStatementsForm.fromDate.month"]')
		from_year = driver.find_element_by_css_selector('[name="downloadStatementsForm.fromDate.year"]')

		from_day.clear()
		from_day.send_keys(str(from_date.day))
		from_month.clear()
		from_month.send_keys(str(from_date.month))
		from_year.clear()
		from_year.send_keys(str(from_date.year))


		to_day = driver.find_element_by_css_selector('[name="downloadStatementsForm.toDate.day"]')
		to_month = driver.find_element_by_css_selector('[name="downloadStatementsForm.toDate.month"]')
		to_year = driver.find_element_by_css_selector('[name="downloadStatementsForm.toDate.year"]')

		to_day.clear()
		to_day.send_keys(str(to_date_incl.day))
		to_month.clear()
		to_month.send_keys(str(to_date_incl.month))
		to_year.clear()
		to_year.send_keys(str(to_date_incl.year))

		params, target_url, user_agent = driver.execute_script("""
			return (function() {
				var data = $('form').serializeArray();
				data.push({ name: 'downloadStatementsForm.events.0', value: 'Download' });
				return [$.param(data), $('form').attr('action'), navigator.userAgent];
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
				'Referer': driver.current_url,
				'Content-Type': 'application/x-www-form-urlencoded'
			}
		)

		driver.find_element_by_css_selector('[name="downloadStatementsForm.events.1"]').click()

		return [(from_date, to_date, r.content)]
