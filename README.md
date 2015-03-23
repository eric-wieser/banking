banking
=======

Python 3.4. Because compiling modules for windows x64 just isn't fun enough.

You'll need to patch PyCrypto [like this](https://github.com/dlitz/pycrypto/commit/10abfc8633bac653eda4d346fc051b2f07554dcd#diff-f14623ba167ec6ff27cbf0e005d732a7) to make it work on 3.4

Usage
-----

Currently has interfaces to Tesco credit cards, Santander accounts, and lloyds account(s). Patches adding interfaces welcome.

Modify `config.py` to something like:

    accounts = [
        SantanderAccount('santander saver', '12-23-34', '12345678'),
        LloydsAccount('lloyds gold', '98-76-54', '11223344'),
        TescoAccount('tesco')
    ]

Then download `.qif` statements with

    $ get.py llo san
    Please set a password for your new keyring:
    Please confirm the password:
    Missing credentials for account 'lloyds gold'
      Enter user:
      Enter password:
      Enter mem_info:
    Missing credentials for account 'santander saver'
      Enter user:
      Enter password:
      Enter reg_num:
    [random print statements while downloading follow]

Next time you run, it'll be faster:

    $ get.py llo san
    Please enter password for encrypted keyring:
    [random print statements while downloading follow]

To debug with firefox, use

    get.py tesco --ff
