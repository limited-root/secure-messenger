import netifaces as nf
import re

def check_mac(mac_addr):
	expr = "[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$"
	if re.match(expr, mac_addr.lower()):
		return True
	else:
		return False

def get_mac():
	mac = ''
	networks = nf.interfaces()
	for n in networks:
		if 'eth' in n or 'wlan' in n:
			info = nf.ifaddresses(n)
			#print info
			port = nf.AF_LINK
			if port in info and check_mac(info[port][0]['addr']):
				mac = info[port][0]['addr'] 
	return mac

if __name__ == '__main__':
	print get_mac()
