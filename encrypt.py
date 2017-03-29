from Crypto.Cipher import *
from Crypto import Random as RND
from PIL import Image
from random import *
import stepic

class Encryption(object):
	""" Handling all Encryption of msgs """
	def __init__(self):
		""" Initializing all keys """
		# Generating a no. for choosing random algorithm 
		self.rno = randint(0,2)

	def encrypt_msg(self, msg):
		""" Encrypting msg according to random choice """
		if self.rno == 0:
			enc_msg = self.des_encrypt(msg)
		elif self.rno == 1:
			enc_msg = self.aes_encrypt(msg)
		else:
			enc_msg = self.kidu_encrypt(msg)
		return enc_msg

	def decrypt_msg(self, msg, kidu_key=""):
		#print msg
		msg = msg.split('!@!')
		if msg[0] == '0':
			iv = msg[1]
			msg = msg[2]
			dec_msg = self.des_decrypt(iv, msg)
		elif msg[0] == '1':
			iv = msg[1]
			msg = msg[2]
			dec_msg = self.aes_decrypt(iv, msg)
		else:
			msg = msg[1]
			dec_msg = self.kidu_decrypt(kidu_key, msg)
		return dec_msg

	def des_encrypt(self, msg):
		""" DES CFB(Cipher Feedback) Encryption Algo """
		iv = RND.get_random_bytes(8)
		des_enc = DES.new('01234567', DES.MODE_CFB, iv)
		mod = len(msg) % 8 
		if mod != 0:
			msg += "`"*(8-mod)
		encrypted_msg = des_enc.encrypt(msg)
		sending_msg = '0!@!' + iv + "!@!" + encrypted_msg
		return sending_msg

	def des_decrypt(self, iv, enc_msg):
		""" Decrypting received DES encrypted msg """
		des_dec = DES.new('01234567', DES.MODE_CFB, iv)
		dec_msg = des_dec.decrypt(enc_msg)
		return dec_msg.replace("`", "")

	def aes_encrypt(self, msg):
		""" AES Encryption Algorithm """
		iv = RND.get_random_bytes(16)
		aes_enc = AES.new('This is a key123', AES.MODE_CBC, iv)
		mod = len(msg) % 16
		if mod != 0:
			msg += "`"*(16-mod)
		encrypted_msg = aes_enc.encrypt(msg)
		sending_msg = '1!@!' + iv + "!@!" + encrypted_msg
		return sending_msg
		
	def aes_decrypt(self, iv, enc_msg):
		""" Decrypting msg received using AES encryption """
		aes_dec = AES.new('This is a key123', AES.MODE_CBC, iv)
		dec_msg = aes_dec.decrypt(enc_msg)
		return dec_msg.replace("`", "")

	def kidu_encrypt(self, msg):
		""" Enkidu encryption algorithm """
		garbage_val = randint(10,99)
		# 0->dec, 1->hex
		encoded_type = randint(0,1)
		# 0->right, 1->left
		rot_direction = randint(0,1)

		# Generating random chars to merge with original msg
		random_chrs = []
		for i in xrange(65, 91):
			random_chrs.append(chr(i))
		for i in xrange(97, 123):
			random_chrs.append(chr(i))
		for i in xrange(0, 10):
			random_chrs.append(str(i))

		enc_msg = ""
		if encoded_type == 0:
			for ch in msg:
				dec = str(ord(ch))
				if len(dec) != 3:
					dec = '0'*(3-len(dec)) + dec
				enc_msg += dec
		elif encoded_type == 1:
			for ch in msg:
				enc_msg += ch.encode('hex')

		# Mixing message chars with Random chars
		mixed_msg = ""
		for i in xrange(len(enc_msg)):
			mixed_msg += enc_msg[i] + choice(random_chrs)

		length = len(mixed_msg)
		rot = randint(0,length)
		if rot_direction == 0:
			pos = length - rot
			kidu_msg = mixed_msg[pos:] + mixed_msg[:pos]
		else:
			kidu_msg = mixed_msg[rot:] + mixed_msg[:rot]
		
		key = str(garbage_val) + '|' + str(encoded_type) + '|' + str(rot) + '|' + str(rot_direction)
		sending_msg = '2!@!' + kidu_msg
		self.steg_encrypt(key)
		return sending_msg

	def kidu_decrypt(self, key, msg):
		""" Enkidu encryption algorithm """
		print key
		garbage_val, encoded_type, rot, rot_direction = map(int, key.split('|'))
		# Rotation direction: 0->right, 1->left
		if rot_direction == 0:
			msg = msg[rot:] + msg[:rot]
		else:
			pos = len(msg) - rot
			msg = msg[pos:] + msg[:pos]

		# Removing random chars from msg
		enc_msg = ""
		for i in xrange(0,len(msg),2):
			enc_msg += msg[i]

		# Encoded Type: 0->dec, 1->hex
		dec_msg = ""
		if encoded_type == 0:
			for ch in xrange(0,len(enc_msg),3):
				char = chr(int(enc_msg[ch:ch+3].lstrip('0')))
				dec_msg += char
		elif encoded_type == 1:
			for ch in xrange(0,len(enc_msg),2):
				char = enc_msg[ch:ch+2].decode('hex')
				dec_msg += char
		return dec_msg

	def steg_encrypt(self, key):
		""" Encrypting Enkidu Key in logo.png image """
		im = Image.open('logo.png')
		img = stepic.encode(im, key)
		img.save('send.png', 'PNG')

	def steg_decrypt(self):
		""" Decrypting Enkidu Key from send.png image """
		im = Image.open('send.png')
		key = str(stepic.decode(im))
		return key


if __name__ == '__main__':
	enc = Encryption()
	msg = enc.encrypt_msg('hi enkidu how r u ?')
	key = enc.steg_decrypt()
	print enc.decrypt_msg(msg,key)
