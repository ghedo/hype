-- This script sends out ICMP echo requests and listens for matching replies
-- like the ping(8) utility.

local bin = require("pktizr.bin")
local pkt = require("pktizr.pkt")
local std = require("pktizr.std")

-- template packets
local local_addr = std.get_addr()
local local_port = 64434

local pkt_ip4  = pkt.IP({id=1, src=local_addr})
local pkt_icmp = pkt.ICMP({type=8, id=1})
local pkt_raw  = pkt.Raw({})

function loop(addr, port)
	pkt_ip4.dst = addr

	pkt_icmp.seq = pkt.cookie16(local_addr, addr, local_port, 0)

	pkt_raw.payload = bin.pack('=n', std.get_time())

	return pkt_ip4, pkt_icmp, pkt_raw
end

function recv(pkts)
	local pkt_ip4  = pkts[1]
	local pkt_icmp = pkts[2]
	local pkt_raw  = pkts[3]

	if #pkts < 3 or pkt_icmp._type ~= 'icmp' or pkt_raw._type ~= 'raw' then
		return
	end

	-- ignore if not icmp echo reply
	if pkt_icmp.type ~= 0 then
		return
	end

	local seq = pkt.cookie16(pkt_ip4.dst, pkt_ip4.src, local_port, 0)

	if pkt_icmp.seq ~= seq then
		return
	end

	local now   = std.get_time()
	local clock = bin.unpack('=n', pkt_raw.payload)

	std.print("Host %s is up, time %f ms", pkt_ip4.src, (now - clock) * 1000)
	return true
end
