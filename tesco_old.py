import requests
import json
import re
import os
from contextlib import contextmanager
import pickle
import urlparse
import time

from bs4 import BeautifulSoup

# credential
from config import *

cookie_fname = 'cookies.dump'

s = requests.Session()
try:
	with open(cookie_fname) as f:
		s.cookies = pickle.load(f)
except IOError:
	pass

print s.cookies

for fname in os.listdir('.'):
	if fname.startswith('dump'):
		os.remove(fname)

@contextmanager
def section(message):
	global r
	print message, "..."
	try:
		yield
	except:
		print "FAIL"
		raise
	else:
		print "DONE"
	finally:
		dump(r, message)
		with open(cookie_fname, 'w') as f:
			pickle.dump(s.cookies, f)

def check(soup):
	error = soup.find(class_='error')
	if error:
		raise RuntimeError(error.get_text().strip())
	return soup

def dump(r, name):
	with open('dump-{}-{}.html'.format(dump.count, name.lower().replace(' ', '_')), 'w') as f:
		print >> f
		print >> f, r.text.encode('utf-8')
	with open('dump-{}-{}-req.html'.format(dump.count, name.lower().replace(' ', '_')), 'w') as f:
		print >> f, r.url
		print >> f, [(h, h.url) for h in r.history]
		print >> f, (r.request.body or u'').encode('utf-8')

	dump.count += 1

dump.count = 0

def extract_form_args(f):
	return (
		f.attrs.get('action'),
		{
			i['name']: i.attrs.get('value') or ''
			for i in f.find_all('input')
			if 'name' in i.attrs
		}
	)


def show_me(r):
	import tempfile
	import webbrowser
	import time

	f = tempfile.NamedTemporaryFile(suffix='.html', delete=False)
	f.write(r.text.encode('utf8'))
	f.flush()
	webbrowser.open_new_tab(f.name)

	time.sleep(1)

with section("Load login page"):
	r = s.get('https://www.tescobank.com/sss/authcc')

with section("Sending username"):
	r = s.post('https://www.tescobank.com/sss/authccl',
		data=dict(
			productType='creditcards',
			uid=userid,
			deviceCompatible='YES',
			submit='LOGIN'
		)
	)
	soup = check(BeautifulSoup(r.text))


with section("Identifying device"):
	# submit the device identification form
	params = {
		i['name']: i.attrs.get('value') or ''
		for i in soup.find('form').find_all('input')
	}
	params['DeviceIDType'] = "httpcookie"
	params['MFP'] = json.dumps({
		"navigator":{
			"onLine": True,
			"language": "en-US",
			"userAgent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36",
			"product":"Gecko",
			"platform":"Win32",
			"appVersion":"5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36",
			"appName":"Netscape",
			"appCodeName":"Mozilla",
			"hardwareConcurrency":4,
			"maxTouchPoints":20,
			"vendorSub":"",
			"vendor":"Google Inc.",
			"productSub":"20030107",
			"cookieEnabled": True
		},
		"plugins":[],
		"screen":{"availHeight":984,"availWidth":1280,"colorDepth":24,"height":1024,"pixelDepth":24,"width":1280},
		"extra":{"timezone":-60,"sigVersion":"1.5"}
	})
	if 'ArcotAuthDid' in s.cookies:
		params['DeviceID'] = s.cookies['ArcotAuthDid']


	r = s.post(r.url, data=params)
	soup = check(BeautifulSoup(r.text))


with section("Doing misc login"):
	# now the AOTP_STATE form
	_, params = extract_form_args(soup.find('form'))
	# params['AUTHTOKEN_PRESENT'] = 'true'

	r = s.post(r.url, data=params)
	soup = check(BeautifulSoup(r.text))

with section("Filling in pin"):
	_, params = extract_form_args(soup.find('form', id='inputForm'))

	params['SUBMIT'] = 'Next'
	for i, c in enumerate(pin, 1):
		params['DIGIT{}'.format(i)] = c


	r = s.post(r.url, data=params)

with section("Sending one-time-pass request"):
	soup = check(BeautifulSoup(r.text))
	_, params = extract_form_args(soup.find('form', id='inputForm'))

	params['SUBMIT'] = 'SEND'

	r = s.post(r.url, data=params)
	soup = check(BeautifulSoup(r.text))


with section("Sending one-time-pass"):
	_, params = extract_form_args(soup.find('form', id='inputForm'))

	otp = raw_input()

	params['OTP'] = otp
	params['SUBMIT'] = 'NEXT'

	r = s.post(r.url, data=params)
	soup = check(BeautifulSoup(r.text))


with section("Filling in password"):
	_, params = extract_form_args(soup.find('form', id='inputForm'))

	udk = re.search(r'UDK_=(.+?)\b', r.text).group(1)
	udk = bytearray.fromhex(udk)
	print udk

	import tesco_otp
	server_time = int(soup.find(id='SERVERTIME')['value'])
	time_diff = time.time() - server_time

	params['AUTHTOKEN_PRESENT'] = 'true'
	params['GENERATEDOTP'] = tesco_otp.build(password, udk, server_time / 1000)
	params['DIFFINTIME'] = time_diff
	params['PROPOSALTIME'] = server_time
	params['DOWNLOADAID'] = 'Y'
	params['SUBMIT'] = 'NEXT'

	r = s.post(r.url, data=params)
	soup = check(BeautifulSoup(r.text))


while True:
	device_id_match = re.search('var deviceID = "(.*?)"', r.text)
	if device_id_match:
		with section("Saving device ID"):

			# now the deviceid form
			device_id = device_id_match.group(1)
			s.cookies['ArcotAuthDid'] = device_id

			target, params = extract_form_args(soup.find('form'))

			r = s.post(target, data=params)
			soup = check(BeautifulSoup(r.text))
		break
	else:
		with section("Doing a thing"):
			_, params = extract_form_args(soup.find('form', id='inputForm'))
			r = s.post(r.url, data=params)
			soup = check(BeautifulSoup(r.text))

with section("Continuing"):
	# we load another background page to be notified when the server is actually ready
	initial_res_url = re.search(r"initial_data_resource_url: '(.*?)'", r.text).group(1)
	initial_res_url = urlparse.urljoin(r.url, initial_res_url)
	s.get(initial_res_url)

	# when this happens, it's safe to post the form
	target, params = extract_form_args(soup.find('form', id='initial-data-processing-autosubmit-form'))
	target = urlparse.urljoin(r.url, target)

	r = s.post(target, data=params)
	soup = check(BeautifulSoup(r.text))

with section("Navigating to card"):
	target, params = extract_form_args(soup.find('form', id='navigate'))
	target = urlparse.urljoin(r.url, target)

	r = s.post(target, data=params)
	soup = check(BeautifulSoup(r.text))

with section("Continuing"):
	target, params = extract_form_args(soup.find('form', id='manage-creditcard-account-autosubmit-form'))
	target = urlparse.urljoin(r.url, target)

	r = s.post(target, data=params)
	soup = check(BeautifulSoup(r.text))

print s.cookies