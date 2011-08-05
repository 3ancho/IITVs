from google.appengine.ext import db

# A Model for a User
class User(db.Model):
    username = db.StringProperty()
    password = db.StringProperty()
    name = db.StringProperty()
    created = db.DateTimeProperty(auto_now=True)
    #admin = db.BooleanProperty()
    admin = db.StringProperty()
    email = db.EmailProperty()
    cwid = db.StringProperty()
    major = db.StringProperty()
    phone = db.PhoneNumberProperty()
    d_hours = db.IntegerProperty()
    a_hours = db.IntegerProperty(default = 0)

class Location(db.Model):
    rname = db.StringProperty()
    camera = db.StringProperty()
    size = db.StringProperty()

class Course(db.Model):
    ''' time matching pairs 
        8:30am-9:45am       0
        10:00am-11:15am     1
        11:30am-12:40pm     2
        1:50pm-3:00pm       3
        3:15pm-4:30pm       4
        5:00pm-6:10pm       5
        6:30pm-9:10pm       6
    '''
    created = db.DateTimeProperty(auto_now = True)
    cname = db.StringProperty() # course name (major)
    cnumber = db.IntegerProperty() # course number 
    loc = db.ReferenceProperty(Location)
    time = db.IntegerProperty() # time = [0 to 6]
    csessions = db.StringProperty() # '1234567' 

class CSession(Course): #course session
    td = db.ReferenceProperty(User)
    w_day = db.StringProperty() # one digit number
    td_list = db.ListProperty(db.Key)

class XY(db.Model): # an object helps to pass values
    x = db.StringProperty() # row: location -> location.rname
    y = db.IntegerProperty() # column: time slot -> Ingeter
    z = db.StringProperty() # specify a day
    zz = db.StringProperty() # specify course_session name

class Compact:
    def __init__(self, info1, info2):
        self.info1 = info1
        self.info2 = info2

# end of class definitions, start of helper functions

