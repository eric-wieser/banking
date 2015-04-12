import keyring

from interfaces import *

accounts = [
	TescoAccount('tesco')
]


cred_store = keyring.backends.file.EncryptedKeyring()
cred_store.file_path = 'cred.cfg'

if __name__ == '__main__':
	for a in accounts:
		print(a.name)
		print(vars(a))
		print()