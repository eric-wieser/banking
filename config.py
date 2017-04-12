#! python3
import keyrings.alt
from pprint import pprint

from interfaces import *

accounts = [
	TescoAccount('tesco')
]


cred_store = keyrings.alt.file.EncryptedKeyring()
cred_store.file_path = 'cred.cfg'

if __name__ == '__main__':
	for a in accounts:
		print(a.name)
		pprint(vars(a))
		print()

	cred_store.keyring_key
	for a in accounts:
		a.auth_from_store(cred_store)
		print(a.name)
		pprint(vars(a))