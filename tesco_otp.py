from binascii import hexlify, unhexlify
import hashlib
import hmac
import struct


def _build(pdk, ctr):
	digest = bytearray(
		hmac.new(
			pdk,
			struct.pack('>Q', ctr),
			hashlib.sha1
		).digest()
	)

	offset = digest[-1] & 15

	otp_i = struct.unpack('>L', digest[offset:offset + 4])[0]

	return "{:08d}".format(otp_i % 10 ** 8)

def crypto_mgf1(key, length):
	i = 0
	res = bytearray()
	while len(res) < length:
		res += hashlib.sha1(key + struct.pack('>L', i)).digest()
		i += 1

	return res[:length]

def crypto_maskDES(data, key):
    res = crypto_mgf1(key, len(data))

    return bytearray(
    	d ^ r
    	for d, r in zip(bytearray(data), bytearray(res))
    )

def build(password, udk, t):
	return _build(
		pdk=crypto_maskDES(udk, password),
		ctr=t // 30
	)