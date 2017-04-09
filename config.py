#! python3
import keyrings.alt

from interfaces import *

accounts = [
	TescoAccount('tesco')
]


cred_store = keyrings.alt.file.EncryptedKeyring()
cred_store.file_path = 'cred.cfg'

if __name__ == '__main__':
	for a in accounts:
		print(a.name)
		print(vars(a))
		print()