#from uuid import getnode as get_mac
from find_mac import get_mac
import easygui as eg
import redis
import hmac
import json
import chat
import re

class Gui(object):
    """ GUI class handling all gui windows """
    def __init__(self):
        """ All important variables initialized """
        self.key = "enkidu"
        self.title = "JSCS Instant Messenger!"
        self.username = ""
        # Making connection with Redis Server
        self.make_connection()
        self.welcome()

    def make_connection(self):
        """ Making connection to Redis Server """
        # Put server address in place of localhost
        self.re = redis.StrictRedis(host='localhost', port=6379)

    def welcome(self):
        """ Welcome window """
        img = "chat.gif"
        msg = "Welcome to Javid Secure Chat System"
        choices = ("Login!", "Signup!", "Reset Password!", "Exit")
        reply = eg.buttonbox(msg, title=self.title, image=img, choices=choices)
        if reply == "Login!":
            rl = self.login()
            while rl == 2:
                rl = self.login()
            if rl == 1:
                #print "logged in"
                self.updprof_addfr_remfr_chat_gui()
            else:
                self.welcome()
        elif reply == "Signup!":
            rs = self.signup()
            while rs == 2:
                rs = self.signup()
            self.welcome()
        elif reply == "Reset Password!":
            rrp = self.reset_password()
            self.welcome()
        else:
            exit(0)

    def check_password(self, password):
        """ Checking if password contains atleast 1 Caps letter and 1 digit """
        digit = re.search(r"\d", password)
        uppercase = re.search(r"[A-Z]", password)
        lowercase = re.search(r"[a-z]", password)
        length = len(password)
        if digit and uppercase and lowercase and length > 4:
            return True
        else:
            return False

    def check_emailid(self, emailid):
        """ Checking if EmailID format is correct or not """
        if re.match(r'[^@]+@[^@]+\.[^@]+', emailid):
            return True
        else:
            return False

    def make_password(self, password):
        """ Make an encrypted password """
        return hmac.new(self.key, password).hexdigest()

    def check_up(self, username, password, mac):
        """ Checking details with Redis DB"""
        val = self.re.get(username)
        if val is not None:
            val = json.loads(val)
            #print val, self.make_password(password)
            if self.make_password(password) == val[0]:
                if mac in val[5:]:
                    return 1
                else:
                    return 2
        return 0

    def check_usc(self, username, security_code, mac):
        """ Checking details with Redis DB"""
        val = self.re.get(username)
        if val is not None:
            val = json.loads(val)
            if security_code == val[1]:
                if mac in val[5:]:
                    return 1
                else:
                    return 2
        return 0

    def check_security_code(self, username, mac, security_code):
        """ Adding data to Redis key-value pair"""
        val = self.re.get(username)
        if val is not None:
            val = json.loads(val)
            if security_code == val[1]:
                val.append(mac)
                val = json.dumps(val)
                self.re.set(username, val)
                self.re.bgsave()
                return True
        return False

    def login(self):
        """ Login Window """
        msg = " Enter Login Credentials"
        fnames = ["UserName: ", "Password: "]
        errormsg = ""
        fvals = []
        fvals = eg.multpasswordbox(msg, self.title, fnames)
        # make sure that none of the fields was left blank
        if fvals is not None:
            if fvals[0] == '' or fvals[1] == '':
                errormsg = "Fill both UserName & Password!"
            else:
                mac = get_mac()
                # Matching user details in Redis DB
                resp = self.check_up(fvals[0], fvals[1], mac)
                if resp == 1:
                    self.username = fvals[0]
                    return 1
                elif resp == 2:
                    msg = "Your Device MAC address is NOT present in our DB! \
Add it by entering your Security Code entered at time of Signup"
                    img = "mac.gif"
                    while True:
                        security_code = eg.passwordbox(msg, self.title, image=img)
                        if security_code is not None:
                            if security_code != "":
                                if self.check_security_code(fvals[0], mac, security_code):
                                    self.username = fvals[0]
                                    return 1
                                else:
                                    errmsg = "Security Code Doesn't matched!"
                            else:
                                errmsg = "Security Code can't be empty"
                            eg.msgbox(errmsg, title=self.title)
                        else:
                            return 0
                else:
                    errormsg = "Details didn't matched matched"
            if errormsg != "":
                eg.msgbox(errormsg, title=self.title)
                return 2
        else:
            return 0

    def reset_password(self):
        """ Reset Password Window """
        msg = "Enter Details!"
        fnames = ["UserName: ", "Security Code: "]
        errormsg = ""
        fvals = []
        fvals = eg.multpasswordbox(msg, self.title, fnames)
        # make sure that none of the fields was left blank
        if fvals is not None:
            if fvals[0] == '' or fvals[1] == '':
                errormsg = "Fill both UserName & Security Code!"
            else:
                mac = get_mac()
                #print mac
                # Matching user details in Redis DB
                resp = self.check_usc(fvals[0], fvals[1], mac)
                if resp == 1:
                    msg = "Enter New Password!"
                    while True:                        
                        pas = eg.passwordbox(msg, self.title)
                        if pas and self.check_password(pas):
                            pas = self.make_password(pas)
                            val = json.loads(self.re.get(fvals[0]))
                            val[0] = pas
                            val = json.dumps(val)
                            self.re.set(fvals[0], val)
                            self.re.bgsave()
                            return 1
                        elif pas is None:
                            return 0
                        else:
                            errmsg = """ Password should contain atleast 1 digit,
1 uppercase chars, 1 lowercase chars & should be of atleast 8 chars! """                            
                            eg.msgbox(errmsg, title=self.title)
                elif resp == 2:
                    errormsg = "Your Device MAC address is NOT present in our DB! \
So please RESET PASSWORD from the system you signed up."
                else:
                    errormsg = "Details didn't matched!"
            if errormsg != "":
                eg.msgbox(errormsg, title=self.title)
        return 0

    def add_friends(self):
        """ Adding Friends to Personal List """
        img = "chat.gif"
        msg = "Select People to add as your Friends!"
        un = self.username
        val = json.loads(self.re.get(un))
        # Users registered in DB
        self.users = self.re.keys('*')
        self.users.remove(self.username)
        friends = eg.multchoicebox(msg, self.title, self.users,image=img)
        if friends is not None:
            fr = list(set(friends))
            val[4].extend(fr)
            #print val[4]
            val[4] = list(set(val[4]))
            val = json.dumps(val)
            self.re.set(un, val)
            self.re.bgsave()
            return 1
        else:
            return 0

    def remove_friends(self):
        """ Removing Friends from Friends List """
        img = "chat.gif"
        msg = "Select Friends to Remove!"
        un = self.username
        val = json.loads(self.re.get(un))
        # Users registered in DB
        friends = eg.multchoicebox(msg, self.title, val[4],image=img)
        if friends is not None:
            fr = set(friends)
            temp = set(val[4])
            temp.difference_update(fr)
            val[4] = list(temp)
            val = json.dumps(val)
            self.re.set(un, val)
            self.re.bgsave()
            return 1
        else:
            return 0

    def updprof_addfr_remfr_chat_gui(self):
        """ Update Profile and Move to Chat Windows choosing GUI """
        img = "choose.gif"
        msg = "What to do?"
        choices = ("Chat!", "Update Profile!", "Add Friends!", "Remove Friends!", "See Others Profile!", "Exit")
        reply = eg.buttonbox(msg, title=self.title, image=img, choices=choices)
        if reply == "Chat!":
            ch = chat.Chat(self.username, self.re)
            if ch.chat_window_gui() == 0:
                self.updprof_addfr_remfr_chat_gui()
        elif reply == "Update Profile!":
            rl = self.update_profile()
            self.updprof_addfr_remfr_chat_gui()
        elif reply == "Add Friends!":
            if self.add_friends() == 1:
                msg = "Friends Added Successfully!"
                eg.msgbox(msg, self.title)
            self.updprof_addfr_remfr_chat_gui()
        elif reply == "Remove Friends!":
            if self.remove_friends() == 1:
                msg = "Selected Friends Removed Successfully!"
                eg.msgbox(msg, self.title)
            self.updprof_addfr_remfr_chat_gui()                
        elif reply == "See Others Profile!":
            msg = "Choose the Person to see details"
            choices = self.re.keys('*')
            ch = eg.choicebox(msg, self.title, choices)
            if ch is not None:
                data = json.loads(self.re.get(ch))
                msg = """ Username:\t%s \n\n Name:\t\t%s \n\n EmailID:\t\t%s """ \
                      % (ch, data[2], data[3])
                eg.msgbox(msg, self.title)
            self.updprof_addfr_remfr_chat_gui()
        else:
            exit(0)

    def update_profile(self):
        """ Update Profile class """
        msg = " Update Details!"
        fnames = ["\tFull Name: ", "\tEmail-ID",
        "Security Code:\n(for adding new devices later)", "\tPassword: "]
        errormsg = ""
        fvals = []
        fvals = eg.multpasswordbox(msg, self.title, fnames)
        if fvals is not None:
            val = json.loads(self.re.get(self.username))
            """ Updating Full Name """
            if fvals[0] != '':
                while len(fvals[0]) < 6:
                    ermsg = "Full Name should be of atleast 6 chars"
                    eg.msgbox(ermsg, title=self.title)
                    fvals = eg.multpasswordbox(msg, self.title, fnames)
                    if fvals is None:
                        return 0
                val[2] = fvals[0]
            """ Updating EmailID """
            if fvals[1] != '':
                while not self.check_emailid(fvals[1]):
                    ermsg = "Enter Email-ID in proper format"
                    eg.msgbox(ermsg, title=self.title)
                    fvals = eg.multpasswordbox(msg, self.title, fnames, (val[2]))
                    if fvals is None:
                        return 0
                val[3] = fvals[1]            
            """ Updating Security Code """
            if fvals[2] != '':
                while len(fvals[2]) < 6:
                    ermsg = "Security Code should be of atleast 6 chars"
                    eg.msgbox(ermsg, title=self.title)
                    fvals = eg.multpasswordbox(msg, self.title, fnames, (val[2], val[3]))
                    if fvals is None:
                        return 0
                val[1] = fvals[2]
            """ Updating Password """
            if fvals[3] != '':
                while len(fvals[3]) < 8 and self.check_password(fvals[3]):
                    ermsg = """ Password should contain atleast 1 digit,
1 uppercase chars, 1 lowercase chars & should be of atleast 8 chars! """
                    eg.msgbox(ermsg, title=self.title)
                    fvals = eg.multpasswordbox(msg, self.title, fnames, (val[2], val[3], val[1]))
                    if fvals is None:
                        return 0
                pas = self.make_password(fvals[3])
                val[0] = pas

            val = json.dumps(val)
            self.re.set(self.username, val)
            eg.msgbox("Profile Updated Successfully!", self.title)
            self.re.bgsave()
            return 1
        else:
            return 0

    def signup(self):
        """ New user Signup class """
        msg = " Enter Details!"
        fnames = ["Full Name(atleast 6 chars): ", "Email-ID: ", 
        "UserName:", 
        "Security Code(Atleast 6 chars):", 
        "Password(Atleast 8 chars that includes alpha-numeric):"]
        errormsg = ""
        fvals = []
        mac = get_mac()
        #print mac
        fvals = eg.multpasswordbox(msg, self.title, fnames)
        if fvals is not None:
            if fvals[0] == '' or fvals[1] == '' or fvals[2] == '' or \
            fvals[3] == '' or fvals[4] == '':
                errormsg = "Fill all Boxes!"
            else:
                # Checking if username exists or not
                
                if len(fvals[0]) >= 6:
                    if self.check_emailid(fvals[1]):
                        if len(fvals[2]) >= 3:
                            if self.re.exists(fvals[2]) == False :
                                if len(fvals[3]) >= 6:
                                    if len(fvals[4]) >= 8 and self.check_password(fvals[4]):
                                        pas = self.make_password(fvals[4])
                                        # Empty list => friends of user
                                        # Value in DB: [Password,SC,Name,EmailID,Friend list,mac]
                                        val = json.dumps([pas, fvals[3], fvals[0], fvals[1], [], mac])
                                        self.re.set(fvals[2], val)
                                        self.re.bgsave()
                                        # Making Queues for every signup client so that his friends can send him
                                        # msgs when he is Offline also, and user can get them later :)
                                        ch = chat.Chat(fvals[2], self.re)
                                        ch.connection()
                                        eg.msgbox("You Signup Successfully!", self.title)
                                        return 1
                                    else:
                                        errormsg = """ Password should contain atleast 1 digit,
1 uppercase chars, 1 lowercase chars & should be of atleast 8 chars! """
                                else:
                                    errormsg = "Security Code should be of atleast 6 in length"
                            else:
                                errormsg = "UserName Already Exists"
                        else:
                            errormsg = "UserName should be of atleast 4 chars"
                    else:
                        errormsg = "Enter EmailID in proper format"
                else:
                    errormsg = "Name should be of atleast 6 chars"
            if errormsg != "":
                eg.msgbox(errormsg, title=self.title)
                return 2
        else:
            return 0


if __name__ == "__main__":
    g = Gui()
