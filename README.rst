pktizr
======

.. image:: https://travis-ci.org/ghedo/pktizr.png
  :target: https://travis-ci.org/ghedo/pktizr

pktizr_ is a command-line packet generator and analyzer. It lets you generate
custom IP/ICMP/TCP/UDP packets, send them over the network and analyze replies
using Lua scripts.

Among other things, pktizr can be used to test firewall/IDS rules, perform
host discovery, port scanning and OS fingerprinting, test network performance
and so on.

pktizr is fully asynchronous, meaning that it has separate transmit and receive
threads and Lua contexts. The "sending" part of a script can't communicate with
the "receiving" part.

This makes it possible for pktizr to send packets as fast as possible without the
need to synchronously wait for replies, and send as many packets as needed
without worrying about memory exhaustion since it doesn't need to keep track of
sent packets. However this makes writing scripts a little bit trickier.

Getting Started
---------------

Under the scripts_ directory you can find some example scripts. To
run a script you need to specify a list of target hosts (e.g. `192.168.1.0/24`),
a port range (e.g. `1-65535`) and obviously the script you want to run::

   $ sudo pktizr 192.168.1.0/24 -p 1 -S scripts/ping.lua

This will run the `ping.lua` script against all the hosts on the 192.168.0/24
network. The script simply sends out ICMP echo requests like the `ping(8)`
utility does, and can be used to discover active hosts from a set of IP ranges.

The port range (specified with the `-p` option) is `1`, since we only want to
send a single packet per host::

   $ sudo pktizr 192.168.1.0/24 -p 1-65535 -S scripts/syn.lua

The `syn.lua` script sends out TCP SYN packets and can be used to discover open
ports on target hosts. In this case the port range is `1-65353` which means all
ports on the targets will be scanned.

Note that by default pktizr sends packet at a rate of 100 packets per second, in
order to avoid flooding the local network or the target hosts. You can specify a
different value using the `-r` command-line option::

   $ sudo pktizr 192.168.1.0/24 -p 1-65535 -S scripts/syn.lua -r 1000

This will send 1000 packets per second instead. To disable rate limiting, the
value `0` (which means "send packets as fast as possible") can be used (**use
this option with caution**)::

   $ sudo pktizr 192.168.1.0/24 -p 1-65535 -S scripts/syn.lua -r 0

See the `man page`_ for more information.

Dependencies
------------

* `liblua5.1/5.2/jit`
* `liburcu`

Building
--------

pktizr is distributed as source code. Install with::

   $ ./bootstrap.py
   $ ./waf configure
   $ ./waf build

Fuzzing
-------

pktizr's packet decoder can be tested by using the afl fuzzer as follows::

   $ CC=afl-gcc ./waf configure --sanitize=address
   $ ./waf build_fuzz
   $ afl-fuzz -i tests/ -o results/ -m none build/pkt_fuzz @@

Copyright
---------

Copyright (C) 2015 Alessandro Ghedini <alessandro@ghedini.me>

See COPYING_ for the license.

.. _pktizr: https://ghedo.github.io/pktizr/
.. _scripts: https://github.com/ghedo/pktizr/tree/master/scripts
.. _`man page`: https://ghedo.github.io/pktizr/pktizr.html
.. _COPYING: https://github.com/ghedo/pktizr/tree/master/COPYING
