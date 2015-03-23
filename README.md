banking
=======

Python 3.4. Because compiling modules for windows x64 just isn't fun enough.

You'll need to patch PyCrypto [like this](https://github.com/dlitz/pycrypto/commit/10abfc8633bac653eda4d346fc051b2f07554dcd#diff-f14623ba167ec6ff27cbf0e005d732a7) to make it work on 3.4

Usage
-----

Currently has interfaces to Tesco credit cards, Santander accounts, and lloyds account(s). Patches adding interfaces welcome