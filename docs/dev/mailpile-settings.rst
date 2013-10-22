Setting up Mailpile as your mail agent
======================================

``Thunderbird`` is the mail client that we currently recommend. But if you want to
try some experimental setup with the taste of webmail, keep reading.

.. note:: this setup might be risky for your privacy. proceed at your own risk!

Get a working Bitmask client
----------------------------

Indeed, you need a working Bitmask installation, free of bugs, and an activated
account with a provider that supports the Encrypted Mail service. Your Email
indicator should be shiny green :)

Get a working Mailpile environment
-----------------------------------

Refer to `Mailpile README <https://github.com/pagekite/Mailpile/blob/master/README.md>`_ for that.
Install the dependencies into a virtualenv, you know the drill. 

Setup Mailpile with your Bitmask account
----------------------------------------

Tell ``Mailpile`` about your Bitmask Mail account::

        $ ./mp --set "my_from: your_user@bitmask.provider.net = Your Name" --setup

And make it use the local ``smtp`` port for outgoing mail too::

        $ ./mp --set "my_sendmail: default = smtp:localhost:2013"

Configure sync with the local IMAP service
------------------------------------------

We will use ``offlineimap`` for  syncing mail with the local ``IMAP`` service
exposed by ``Bitmask``. But first, we will create an encrypted folder for
storing the mail.

Create encrypted directory
++++++++++++++++++++++++++

This is not strictly needed, but we will create an encrypted folder for the
local Bitmask Inbox. First we install the needed programs::

        $ sudo apt-get install encfs fuse-utils
        $ sudo modprobe fuse
        $ sudo adduser <your username> fuse

Create a folder for the encrypted dirs, and a mountpoint too::

        $ mkdir .bitmask-folder
        $ mkdir BitmaskMail

Create the encrypted filesystem, and mount it::

        $ encfs /abspath/to/.bitmask-folder /abspath/to/BitmaskMail

(note that encfs *wants* absolute paths). It will ask for a password for this
encrypted folder, that you will have to enter each time to decrypt it. For unmounting it, do::

        $ fusermount -u /home/<your username>/BitmaskMail

Install and configure offlineimap
+++++++++++++++++++++++++++++++++

First of all, install offlineimap::

        $ sudo apt-get install offlineimap

Then, create a suiting config file. You can use this template::

> [general]
> accounts = bitmask
> [Account bitmask]
> localrepository = BitmaskEncrypted
> remoterepository = BitmaskService
> [Repository BitmaskEncrypted]
> type = Maildir
> localfolders = ~/BitmaskMail
> [Repository BitmaskService]
> type = IMAP
> ssl = no
> remotehost = localhost
> remoteport = 1984
> remoteuser = <your_username@your_leap_provider.net>
> remotepass = 0000

You can save it anywhere you like, say ``~/.bitmask-offlineimaprc``

Run offlineimap periodically
++++++++++++++++++++++++++++

Now, you can add offlineimap to you crontab (remember to point to the
configuration file above, and to decrypt your encfs folder each session)::

        $ offlineimap -c ~/.bitmask-offlineimaprc

Import your Bitmask INBOX to Mailpile
-------------------------------------
::

        $ ./mp --add ~/BitmaskMail/INBOX --rescan

For checking new mail, you can do::

        $  offlineimap -c ~/.bitmask-offlineimaprc && ./mp --rescan


Enjoy!
------
Aaaaand... that should be all for now. Stay tuned for more awesomeness::

        $ ./mp
        $ chromium localhost:33411

Hint: increase your mail-check period
-------------------------------------
::
        $ BITMASK_MAILCHECK_PERIOD=60 bitmask --debug
