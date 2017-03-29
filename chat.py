from Tkinter import *
import easygui as eg
import encrypt
import thread
import redis
import json
import pika
import os

class Chat(object):
    """ Chat Window and all functionality in it """
    def __init__(self, username, re):
        """ Initialization function """
        self.title = "Javid Secure Chat System"
        self.enc = encrypt.Encryption()
        self.username = username
        self.connection()
        self.kidu_key = ""
        self.data = ""
        self.re = re

    def chat_window_gui(self):
        """ Chat Window GUI """
        img = "chat.gif"
        msg = "Choose the Friends to talk!"
        # No. of users registered in DB
        # nou = self.re.dbsize()
        # Friends added to profile
        fr = json.loads(self.re.get(self.username))
        if fr[4] == []:
            friends = ['']
        else:
            friends = fr[4]

        fr = eg.multchoicebox(msg, self.title, friends, image=img)
        if fr == ['']:
            eg.msgbox("Add Friends to Start Chatting!", title=self.title)
            return 0
        else:
            self.friends = fr
            return self.gui()

    def connection(self):
        """ Connection to Pika """
        self.conn = pika.BlockingConnection(pika.ConnectionParameters(
                                            host='localhost'))
        self.channel = self.conn.channel()
        self.channel.exchange_declare(exchange='chat', type='fanout')
        self.channel.queue_declare(queue=self.username, durable=True)
        self.channel.queue_bind(exchange='chat', queue=self.username)
        #self.channel.confirm_delivery()
        
    def send(self, msg):
        """ Sender function used for sending msgs to other friends """
        if self.data == '':
            enc_msg = self.enc.encrypt_msg(msg)
            if enc_msg[0] == '2':
                img = open('send.png', 'rb').read()
                #img = img.encode('ascii', 'ignore')
                self.channel.basic_publish(exchange='chat', routing_key='chat', body="I~"+img)
            data = "T~"+enc_msg
        else:
            data = self.data
            self.data = ''
        self.channel.basic_publish(exchange='chat', routing_key='chat', body=data)
    
    def recv(self):
        """ Receiver function used to receive msgs from other friends """
        def callback(ch, method, properties, body):
            msg = body[2:]
            if body[:2] == "T~":
                dec_msg = self.enc.decrypt_msg(msg, self.kidu_key)
                
                # Message archieve file
                fo = open("msgs/"+self.username+','+','.join(self.friends)+'.txt', 'a+')
                arc_msg = self.enc.aes_encrypt(dec_msg)
                fo.write(arc_msg + "\n")
                fo.close()
                self.lb.insert(END, dec_msg)
                self.lb.pack(side=TOP, anchor=W)                

                if msg[0] == '2':
                    os.remove('send.png')
                    self.kidu_key = ''
            elif body[:2] == "I~":
                fobj = open('send.png', 'wb')
                fobj.write(msg)
                fobj.close()
                self.kidu_key = self.enc.steg_decrypt()
            elif body[:2] == "F~":
                txt, file_data = msg.split('!@!')
                #print txt, file_data
                if txt.find(self.username+":") != 0:
                    fn = txt.split(':')[1]
                    resp = eg.filesavebox('Select Location to save Received file', 
                                           self.title, fn)
                    if resp is not None:
                        fobj = open(resp, 'wb')
                        fobj.write(file_data)
                        fobj.close()
                    else:
                        fobj = open(fn.split('/')[-1], 'wb')
                        fobj.write(file_data)
                        fobj.close()
                fn = txt
                self.lb.insert(END, fn)
                self.lb.pack(side=TOP, anchor=W)                

        self.channel.basic_consume(callback, queue=self.username, no_ack=True)
        self.channel.start_consuming()

    def mfetch(self):
        """ Fetching msg from Box """
        msg = self.text.get()
        self.text.delete(0, len(msg)+1)
        #self.text.pack(side=BOTTOM, fill=X)
        if msg == '':
            return 

        if self.data == '':
            msg = self.username + ":    " + msg
        else:
            msg = self.data
        self.send(msg)

    def send_file(self):
        # Reading file from location selected by user and sending 
        # to another user 
        fpath = eg.fileopenbox("Select File to Send", self.title, default=os.getcwd())
        if fpath is not None:        
            fobj = open(fpath, "rb")
            self.text.insert(0, str(fpath))
            self.text.pack(side=BOTTOM, fill=X)
            self.data = "F~" + self.username + ": " + str(fpath) + "!@!" + str(fobj.read())
            fobj.close()

    def gui(self):
        self.msger = Tk()
        self.msger.title(string = self.username + " chatting with: " + ','.join(self.friends))
        # Running message receiving function in background
        thread.start_new_thread(self.recv,())
        self.msger.geometry("400x600")
        self.text = Entry(self.msger)
        self.text.pack(side=BOTTOM, fill=X)
        # Horizontal Scrolbar for above TextBox
        self.sbh = Scrollbar(self.msger, orient=HORIZONTAL)
        self.sbh.pack(side=BOTTOM, fill="x")
        # Vertical Scroll bar for above TextBox
        self.sbv = Scrollbar(self.msger)
        self.sbv.pack(side=RIGHT, fill="y")
        self.lb = Listbox(self.msger, width=400, height=500, xscrollcommand=self.sbh.set, \
yscrollcommand=self.sbv.set)
        
        # Reading previous messages from file
        try:
            fo = open("msgs/"+self.username+','+','.join(self.friends)+'.txt')
            msg = fo.readline()
            while msg:
                msg = msg.replace('\n', '')
                met, iv, enc_msg = msg.split('!@!')
                arc_msg = self.enc.aes_decrypt(iv, enc_msg)
                self.lb.insert(END, arc_msg)
                self.lb.pack(side=TOP, anchor=W)
                self.sbh.config(command = self.lb.xview)
                self.sbv.config(command = self.lb.yview)
                msg = fo.readline()
            fo.close()
        except:
            pass

        self.text.focus()        # Saves a click
        self.text.bind('<Return>', (lambda event: self.mfetch()))
        self.msgbtn = Button(self.msger, text='SEND!', command=self.mfetch)
        self.msgbtn.pack(side=BOTTOM, anchor=E, after=self.text)
        self.filebtn = Button(self.msger, text='Select FILE!', command=self.send_file)
        self.filebtn.pack(side=BOTTOM, anchor=W, after=self.text)
        self.logbtn = Button(self.msger, text='Leave Chat!', command=self.msger.destroy)
        self.logbtn.pack(side=TOP, anchor=E, after=self.text)
        self.msger.mainloop()
        return 0


if __name__ == '__main__':
    ch = Chat('Aki', redis.StrictRedis())
    ch.chat_window_gui()