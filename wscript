# Copyright (C) 2015 Alessandro Ghedini <alessandro@ghedini.me>
# This file is released under the 2 clause BSD license, see COPYING

import re

from waflib import Utils
from waflib.Build import BuildContext

APPNAME = 'hype'
VERSION = '0.0'

_INSTALL_DIRS_LIST = [
	('bindir',  '${DESTDIR}${PREFIX}/bin',      'binary files'),
	('datadir', '${DESTDIR}${PREFIX}/share',    'data files'),
	('docdir',  '${DATADIR}/doc/hype',          'documentation files'),
	('mandir',  '${DATADIR}/man',               'man pages '),
]

def options(opt):
	opt.load('compiler_c')

	group = opt.get_option_group("build and install options")
	for ident, default, desc in _INSTALL_DIRS_LIST:
		group.add_option('--{0}'.format(ident),
			type    = 'string',
			dest    = ident,
			default = default,
			help    = 'directory for installing {0} [{1}]' \
			            .format(desc, default))

	opt.add_option('--sanitize', action='store', default=None,
	               help='enable specified sanotizer (address, thread, ...)')

def configure(cfg):
	def my_check_cc(ctx, dep, **kw_ext):
		kw_ext['uselib_store'] = dep
		if ctx.check_cc(**kw_ext):
			ctx.env.deps.append(dep)

	def my_check_cfg(ctx, dep, **kw_ext):
		kw_ext['args'] = '--cflags --libs'
		kw_ext['uselib_store'] = dep
		if ctx.check_cfg(**kw_ext):
			ctx.env.deps.append(dep)

	def my_check_lua(ctx, lua_versions):
		for lua in lua_versions:
			if ctx.check_cfg(package=lua, args='--cflags --libs', \
			                 uselib_store=lua, mandatory=False):
				ctx.env.deps.append(lua)
				return

		ctx.fatal('Could not find Lua')

	def my_check_os(ctx):
		ctx.env.deps.append("os-{0}".format(ctx.env.DEST_OS))

	cfg.load('compiler_c')

	for ident, _, _ in _INSTALL_DIRS_LIST:
		varname = ident.upper()
		cfg.env[varname] = getattr(cfg.options, ident)

		# keep substituting vars, until the paths are fully expanded
		while re.match('\$\{([^}]+)\}', cfg.env[varname]):
			cfg.env[varname] = \
			  Utils.subst_vars(cfg.env[varname], cfg.env)

	cfg.env.CFLAGS   += [ '-Wall', '-pedantic', '-g', '-std=gnu99' ]
	cfg.env.CPPFLAGS += [ '-D_GNU_SOURCE' ]

	cfg.env.deps = []

	# OS
	my_check_os(cfg)

	# system libs
	my_check_cc(cfg, 'm',       lib='m',       mandatory=True)
	my_check_cc(cfg, 'pthread', lib='pthread', mandatory=True)
	my_check_cc(cfg, 'resolv',  lib='resolv',  mandatory=True)
	my_check_cc(cfg, 'rt',      lib='rt',      mandatory=True)

	# Lua
	my_check_lua(cfg, ['luajit', 'lua5.2', 'lua5.1'])

	# urcu
	my_check_cc(cfg, 'urcu', lib=['urcu', 'urcu-common'],
	            header_name='urcu/wfcqueue.h', mandatory=True)

	# pcap
	my_check_cc(cfg, 'pcap', lib='pcap',
	            header_name='pcap.h', mandatory=True)

	# ronn
	cfg.find_program('ronn', mandatory=False)

	# afl
	cfg.find_program('afl-fuzz', mandatory=False)

	if cfg.options.sanitize:
		cflags = [ '-fsanitize=' + cfg.options.sanitize ]
		lflags = [ '-fsanitize=' + cfg.options.sanitize ]

		if cfg.options.sanitize == 'thread':
			cflags += [ '-fPIC' ]
			lflags += [ '-pie' ]

		if cfg.check_cc(cflags=cflags,linkflags=lflags,mandatory=False):
			cfg.env.CFLAGS    += cflags
			cfg.env.LINKFLAGS += lflags

def build(bld):
	def filter_sources(ctx, sources):
		def __source_file__(source):
			if isinstance(source, tuple):
				return source[0]
			else:
				return source

		def __check_filter__(dependency):
			if dependency.find('!') == 0:
				dependency = dependency.lstrip('!')
				return dependency not in ctx.env.deps
			else:
				return dependency in ctx.env.deps

		def __unpack_and_check_filter__(source):
			try:
				_, dependency = source
				return __check_filter__(dependency)
			except ValueError:
				return True

		return [__source_file__(source) for source in sources \
		         if __unpack_and_check_filter__(source)]

	sources = [
		# sources
		( 'src/bucket.c'                           ),
		( 'src/hype.c'                             ),
		( 'src/netif_pcap.c',           'pcap'     ),
		( 'src/pkt.c'                              ),
		( 'src/pkt_arp.c'                          ),
		( 'src/pkt_chksum.c'                       ),
		( 'src/pkt_cookie.c'                       ),
		( 'src/pkt_eth.c'                          ),
		( 'src/pkt_icmp.c'                         ),
		( 'src/pkt_ip4.c'                          ),
		( 'src/pkt_raw.c'                          ),
		( 'src/pkt_tcp.c'                          ),
		( 'src/pkt_udp.c'                          ),
		( 'src/printf.c'                           ),
		( 'src/ranges.c'                           ),
		( 'src/resolv.c'                           ),
		( 'src/resolv_linux.c',         'os-linux' ),
		( 'src/routes_linux.c',         'os-linux' ),
		( 'src/script.c'                           ),
		( 'src/util.c'                             ),

		# Lua 5.3 compat
		( 'deps/lua-compat-5.3/c-api/compat-5.3.c' ),
		( 'deps/lua-compat-5.3/lstrlib.c'          ),
		( 'deps/lua-compat-5.3/ltablib.c'          ),
		( 'deps/lua-compat-5.3/lutf8lib.c'         ),

		# siphash
		( 'deps/siphash/siphash24.c'               ),
	]

	bld.env.append_value('INCLUDES', ['deps', 'src'])

	bld(
		name         = 'hype',
		features     = 'c cprogram',
		source       = filter_sources(bld, sources),
		target       = 'hype',
		use          = bld.env.deps,
		install_path = bld.env.BINDIR
	)

	bld.install_files(bld.env.DOCDIR + '/scripts',
	                  bld.path.ant_glob('scripts/*.lua'))

	bld.declare_chain(
		name         = 'ronn',
		rule         = '${RONN} -r < ${SRC} > ${TGT}',
		ext_in       = '.1.md',
		ext_out      = '.1',
		reentrant    = False,
		install_path = bld.env.MANDIR + '/man1',
	)

	if bld.env['RONN']:
		bld(
			name         = 'manpages',
			source       = bld.path.ant_glob('docs/*.md'),
		)

def build_fuzz(bld):
	if not bld.env.AFL_FUZZ:
		bld.fatal("AFL not detected")

	sources = [
		# sources
		'src/pkt.c',
		'src/pkt_arp.c',
		'src/pkt_chksum.c',
		'src/pkt_cookie.c',
		'src/pkt_eth.c',
		'src/pkt_fuzz.c',
		'src/pkt_icmp.c',
		'src/pkt_ip4.c',
		'src/pkt_raw.c',
		'src/pkt_tcp.c',
		'src/pkt_udp.c',
		'src/printf.c',
		'src/util.c',

		# siphash
		'deps/siphash/siphash24.c',
	]

	bld.env.append_value('INCLUDES', ['deps', 'src'])

	bld(
		name         = 'pkt_fuzz',
		features     = 'c cprogram',
		source       = sources,
		target       = 'pkt_fuzz',
		use          = bld.env.deps,
	)

class FuzzContext(BuildContext):
	cmd = 'build_fuzz'
	fun = 'build_fuzz'
