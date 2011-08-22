from google.appengine.ext import db

#from wtforms.ext.appengine.db import model_form
from wtforms import * 
from wtforms.validators import *
import wtforms.widgets

# User Model 
class User(db.Model):
    username = db.StringProperty()
    password = db.StringProperty()
    confirm = db.StringProperty()
    name = db.StringProperty()
    created = db.DateTimeProperty(auto_now=True)
    admin = db.BooleanProperty()
    email = db.EmailProperty()
    cwid = db.StringProperty()
    major = db.StringProperty()
    phone = db.PhoneNumberProperty()
    d_hours = db.IntegerProperty()
    a_hours = db.IntegerProperty(default = 0)

class UserForm(Form):
    cwid = TextField('CWID', [required(), Length(min=8, max=10)] )
    major = TextField('Major', [required(), Length(min=2, max=20) ] )# Regexp check needed Aug
    email = TextField('Email', [required()] )
    phone = TextField('Phone', [required(), Length(min=10, max=13)] ) 
    d_hours = IntegerField('Desired Hours', [NumberRange(min = 0, max = 40), required()] ) 
# User Form
class LoginForm(Form):
    username = TextField('User Name', \
            [required(), Length(min=3, max=30)])
    password = PasswordField('Password', \
            [required(), Length(min=3, max=40)]) 
# User Form
class RegisterForm(LoginForm):
    name = TextField('Full Name', [required()])
    confirm = PasswordField('Repeat Password', \
            [EqualTo('password', message = 'Passwords must match')])

# Location Model
class Location(db.Model):
    rname = db.StringProperty(required=True)
    camera = db.IntegerProperty(default = 1)
    size = db.IntegerProperty()

# Location Form
class LocationForm(Form):
    rname = TextField('Room Name', [required(), Length(min=2, max=30)])
    camera = IntegerField('Camera(s)', \
            [required(), NumberRange(min=0, max=3, \
            message=('Value should be 0 to 3'))])
    size = IntegerField('Room Size', \
            [NumberRange(min=0, max=400)])

# Course Model
class Course(db.Model):
    ''' duration index pairs 
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
    snumber = db.IntegerProperty() # course number 
    loc = db.ReferenceProperty(Location)
    time = db.IntegerProperty() # time = [0 to 6]
    csessions = db.StringListProperty() # '1234567' 
   # td_list = db.ListProperty(db.Key)


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

# Course Form
class CourseForm(Form):
    cname = TextField('Course Name', \
            [required(), Length(min=2, max=30)] )
     
    snumber = IntegerField('Section', \
            [required(), NumberRange(min=0, max=9)] )
    csessions = MultiCheckboxField('Session(s)', [required()],\
            choices=[('1', 'Mon'),('2', 'Tue'),('3', 'Wed'),
                ('4','Thr'), ('5','Fri'), ('6','Sat'), ('7','Sun')])

class Event(db.Model):
#    note = db.TextProperty()
    created = db.DateTimeProperty(auto_now = True)
    active = db.BooleanProperty()
    csession = db.StringProperty()
#    backup_td = db.StringProperty() 
    messages = db.ListProperty(db.Key) # list with message.key 

class Message(db.Model):
    note = db.StringProperty(multiline = True)
    user = db.ReferenceProperty(User)
    created = db.DateTimeProperty(auto_now=True) # auto created, no worry

class CSession(Course): # Course session inherits Course model
    w_day = db.StringProperty() # one digit number
    td_list = db.ListProperty(db.Key)
    td = db.ReferenceProperty(User)
    event = db.ReferenceProperty(Event)


class Cell(db.Model): # an object helps to pass values
    x = db.StringProperty() # row: location -> location.rname
    y = db.IntegerProperty() # column: time slot -> Ingeter
    z = db.StringProperty() # specify a day, Required
#    zz = db.StringProperty() # specify course_session name

class Compact:
    # A class wraps two objects, for template value passing
    def __init__(self, info1, info2):
        self.info1 = info1
        self.info2 = info2

# end of class definitions, start of helper functions

