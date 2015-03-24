import keyring

from interfaces import *

cred_store = keyring.backends.file.EncryptedKeyring()
cred_store.file_path = 'cred.cfg'

# force a credential check
cred_store.keyring_key

accounts = [
	TescoAccount('tesco')
]


for a in accounts:
	a.auth_from_store(cred_store)

if __name__ == '__main__':
	for a in accounts:
		print(a.name)
		print(vars(a))
		print()