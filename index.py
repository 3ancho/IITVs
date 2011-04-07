#!/usr/bin/env python
# Ruoran Wang IITVs
import os
import logging
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from util.sessions import Session
from google.appengine.ext import db


# A Model for a User
class User(db.Model):
    username = db.StringProperty()
    password = db.StringProperty()
    name = db.StringProperty()
    created = db.DateTimeProperty(auto_now=True)
    #admin = db.BooleanProperty()
    admin = db.StringProperty()

class Location(db.Model):
    rname = db.StringProperty()
    camera = db.StringProperty()
    size = db.StringProperty()

class Course(db.Model):
    cname = db.StringProperty() # course name (major)
    cnumber = db.IntegerProperty() # course number 
    loc = db.ReferenceProperty(Location)
    time = db.IntegerProperty() # time = [0 to 6]
    ''' 8:30am-9:45am 	    0
        10:00am-11:15am     1
        11:30am-12:40pm 	2
        1:50pm-3:00pm 	    3
        3:15pm-4:30pm 	    4
        5:00pm-6:10pm 	    5
        6:30pm-9:10pm       6
    '''
    csession = db.StringProperty() # '1234567' 
    #csection = db.IntegerProperty() # course section number
    #lecturer = db.StringProperty() # lecturer name
    #start = db.TimeProperty()
    #end = db.TimeProperty()

class CSession(Course): #course session
    td = db.ReferenceProperty(User)
    w_day = db.StringProperty() # one digit number

class Sheet(db.Model): # delete this March 05
    date = db.StringProperty() # Mar 09
    day = db.IntegerProperty() # Mon- 0, Tue- 1, etc. 
    loc_list = db.StringListProperty() 
    time_list = db.ListProperty(int)

class XY(db.Model):
    x = db.StringProperty()
    y = db.IntegerProperty()

# A Model for a ChatMessage
class ChatMessage(db.Model):
    user = db.ReferenceProperty()
    text = db.StringProperty()
    created = db.DateTimeProperty(auto_now=True)

def noUser(handler):
   '''
   For Each <inside> Handler, noUser check is needed
   '''
   handler.session = Session()
   pkey = handler.session.get('userkey')
   if pkey == None:
       doRender(handler, 'index.html', {})
       return True 
   else:
       return False 

def Admin():
    '''
    check if current user is admin, return true if yes.
    '''
    current_user = db.get(pkey)
    if current_user.admin == "False":
        doRender(self, 'main.html', {'msg' : 'Require admin previlege!'})
        return

def doRender(handler, tname = 'index.html', values = { }):
    if tname == '/' or tname == '' or tname == None:
        tname = 'index.html'
    
    handler.session = Session()
    flag = True 
    if tname == '/loginscreen.html' or tname == '/register.html' or \
            tname =='loginscreen.html' or tname =='register.html':
        flag = False 

    if handler.session.get('username') == None and flag:
        tname = 'index.html'

    temp = os.path.join(os.path.dirname(__file__), 'templates/' + tname)
    if not os.path.isfile(temp):
        return False

    # Make a copy of the dictionary and add basic values
    newval = dict(values)
    newval['path'] = handler.request.path
    if 'username' in handler.session:
        newval['username'] = handler.session['username']

    outstr = template.render(temp, newval)
    handler.response.out.write(outstr)
    return True

class RegisterHandler(webapp.RequestHandler):
    def get(self):
        doRender(self, 'register.html') 

    def post(self):
        self.session = Session()
        n = self.request.get("name")
        un = self.request.get("username")
        pw = self.request.get("password")

        if pw == '' or un == '' or n == '':
            doRender(
                    self,
                    'register.html',
                    {'error' : 'Please fill in all fields'} )
            return

        que = db.Query(User).filter('username =', un)
        results = que.fetch(limit = 1)

        if len(results) > 0:
            doRender(
                    self,
                    'register.html',
                    {'error' : 'Username already exists'} )
            return
        #if success, create new user
        newuser = User(name = n, username = un, password = pw, admin = "False")
        pkey = newuser.put()
        self.session['username'] = un 
        self.session['userkey'] = pkey
        doRender(self, 'register.html', \
            {'error' : 'Register Success! Welcome, ' + un} )
      
class LoginHandler(webapp.RequestHandler):
    def get(self):
        doRender(self, 'loginscreen.htm')
    
    def post(self):
        self.session = Session()
        un = self.request.get('username')
        pw = self.request.get('password')

        self.session.delete_item('username')
        self.session.delete_item('userkey')

        if pw == '' or un == '':
            doRender(
                    self,
                    'loginscreen.html',
                    {'error': 'Please specify Username and Password'} )
            return

        que = db.Query(User)
        que = que.filter('username =', un)
        que = que.filter('password =', pw)
        # above two may combine

        results = que.fetch(limit = 1)

        if len(results) > 0:
            user = results[0]
            self.session['userkey'] = user.key()
            self.session['username'] = un
            doRender(self,'main.html', {} ) # if ok, go to main.html (logged in)
        else:
            doRender(
                    self,
                    'loginscreen.html',
                    {'error' : 'Username or Password wrong' } )

class LogoutHandler(webapp.RequestHandler):
    def get(self):
        if noUser(self):
            return
        self.session.delete_item('username')
        self.session.delete_item('userkey')
        doRender(self, 'index.html', {'msg' : ' Logout successful.'} ) 

class IndexHandler(webapp.RequestHandler):
    def get(self):
        if doRender(self,self.request.path) :
            return
        doRender(self,'index.html')

class MainHandler(webapp.RequestHandler):
    def get(self):
        if noUser(self):
            return
        que = db.Query(Location)
        location_list = que.fetch(limit = 5000) # number of rows

        days = ['1','2','3','4','5','6','7'] 
        day_list = [] # list of course_list

        for day in days:
            course_list = [] # list of row_list
            row_list = [] # may deleted
            time_list = [0,1,2,3,4,5,6]

            for location in location_list:
                row_list = []
                row_list.append(location) #row_list[0]: operand Location

                t_key = location.key()
                que_course = db.Query(CSession).filter('w_day =', day).filter('loc =', t_key)

                test = que_course.fetch(limit = 2) 
                if len(test) == 0: # no course in this location
                    for item in time_list:
                        object_xy = XY(x = location.rname, y = item)
                        row_list.append( object_xy ) #cell, operand: Object XY()
                else:

                    for item in time_list:
                        que_cell = db.Query(CSession).filter('w_day =', day).filter('loc =', t_key).filter('time =', item)  
                        result = que_cell.fetch(limit = 1) # should be: limit = 1
                        if len(result) != 0:
                            row_list.append(result[0]) #cell, operand:Course
                        else:
                            object_xy = XY(x = location.rname, y = item)
                            row_list.append( object_xy ) #cell, oerand: Object XY() 
                                                
                course_list.append(row_list)
                # end for location in location_list
            day_list.append(course_list) 
            # end for day in days
        
        doRender(self, 'main.html', {'day_list' : day_list})


class ShowUserHandler(webapp.RequestHandler):
    def get(self):
        if noUser(self):
            return
        
        pkey = self.session['userkey']
        current_user = db.get(pkey)
        if current_user.admin == "True":
            doRender(self, 'show_user.html', { })
        else:
            doRender(self, 'main.html', {'msg' : 'Require admin previlege!'})

    def post(self):
        if noUser(self):
            return
        pkey = self.session['userkey']
        current_user = db.get(pkey)
        if current_user.admin == "False":
            doRender(self, 'main.html', {'msg' : 'Require admin previlege!'})
            return

        que = db.Query(User)
        
        if self.request.get('show_admin') == 'True': # if this will show admin
            admin = que.filter('admin =', 'True')
            admin = admin.fetch(limit = 100) 
            doRender(self, 'show_user.html', {'user_list' : admin } )
            return
        else:
            user = que.filter('admin =', 'False')
            user = user.fetch(limit = 500)
            doRender(self, 'show_user.html', {'user_list' : user } )
            return

class DeleteUserHandler(webapp.RequestHandler):
    def post(self):
        if noUser(self):
            return
        current_user = db.get(pkey)
        
        if current_user.admin == "False":
            doRender(self, 'main.html', {'msg' : 'Require admin previlege!'})
            return

        delete_list = self.request.get_all('key_to_delete')
        ''' # Testing!
        doRender(self, 'test.html', {'msg' : first[0], 'msg2': str(len(first))})
        return
        '''
        if len(delete_list) == 0:
            doRender(self, 'show_user.html', {})
            return

        for item in delete_list:
            que = db.Query(User).filter('username =', item)
            result = que.fetch(limit = 1)
            result[0].delete()

        doRender(self, 'show_user.html', {})

class ShowSettingHandler(webapp.RequestHandler):
    def get(self):
        if noUser(self):
            return
        que = db.Query(Location)
        location_list = que.fetch(limit = 5000) # number of rows

        course_list = [] # list of row_list
        row_list = [] # may deleted
        time_list = [0,1,2,3,4,5,6]

        for location in location_list:
            row_list = []
            row_list.append(location) #row_list[0]: operand Location

            t_key = location.key()
            que_course = db.Query(Course).filter('loc =', t_key)

            test = que_course.fetch(limit = 2) 
            if len(test) == 0: # no course in this location
                for item in time_list:
                    object_xy = XY(x = location.rname, y = item)
                    row_list.append( object_xy ) #cell, operand: Object XY()
            else:

                for item in time_list:
                    que_cell = db.Query(Course).filter('loc =', t_key).filter('time =', item)  
                    result = que_cell.fetch(limit = 1) # should be: limit = 1
                    if len(result) != 0:
                        row_list.append(result[0]) #cell, operand:Course
                    else:
                        object_xy = XY(x = location.rname, y = item)
                        row_list.append( object_xy ) #cell, oerand: Object XY() 
                                            
            course_list.append(row_list)
        
        doRender(self, 'setting.html', {'course_list' : course_list})

class AddLocationHandler(webapp.RequestHandler):
    
    def post(self):
        if noUser(self):
            return
        pkey = self.session['userkey']
        current_user = db.get(pkey)

        t_rname = self.request.get('name')
        t_camera = self.request.get('camera')
        t_size = self.request.get('size')

        new_location = Location(rname = t_rname, camera = t_camera, size = t_size)
        new_location.put()

        que = db.Query(Location)
        location_list = que.fetch(limit = 5000)
        doRender(self, 'setting.html', {'location_list' : location_list}) 
        # course_list needed: March 29

class PreCourseHandler(webapp.RequestHandler):
    def post(self):
        if noUser(self):
            return
        location_name = self.request.get('row')
        time_index = int(self.request.get('column'))
        #que = db.Query(Location).filter('rname =', location_name) 
        #t_location = que.fetch(limit = 1)[0]
        doRender(self, 'add_course.html', \
                {'loc' : location_name, 't_index' : time_index} )

class AddCourseHandler(webapp.RequestHandler):
    def post(self):
        if noUser(self):
            return
        location_name = self.request.get('location')
        time_index = int(self.request.get('time_index'))
        t_cname = self.request.get('cname')
        t_cnumber = int(self.request.get('cnumber'))
        t_csession = self.request.get('csession') # String of numbers.
        #t_time = self.request.get('time')  # March 31 need improve!
        
        que = db.Query(Location).filter('rname =', location_name) 
        location_key = que.fetch(limit = 1)[0].key()

        new_course = Course(loc = location_key, time = time_index, \
                cname = t_cname, cnumber = t_cnumber, csession = t_csession )
        new_course.put()

        for i in  t_csession:
            new_csession = CSession(loc = location_key, time = time_index, \
                cname = t_cname, cnumber = t_cnumber, \
                csession = t_csession, w_day = i)
            new_csession.put()
        
        que_loc = db.Query(Location)
        location_list = que_loc.fetch(limit = 500)

        que_course = db.Query(Course)
        course_list = que_course.fetch(limit = 500)

        doRender(self, 'setting.html', { } ) 

class TDSettingHandler(webapp.RequestHandler):
    def get(self):
        if noUser(self):
            return
        que = db.Query(Location)
        location_list = que.fetch(limit = 5000) # number of rows

        days = ['1','2','3','4','5','6','7'] 
        day_list = [] # list of course_list

        for day in days:
            course_list = [] # list of row_list
            row_list = [] # may deleted
            time_list = [0,1,2,3,4,5,6]

            for location in location_list:
                row_list = []
                row_list.append(location) #row_list[0]: operand Location

                t_key = location.key()
                que_course = db.Query(CSession).filter('w_day =', day).filter('loc =', t_key)

                test = que_course.fetch(limit = 2) 
                if len(test) == 0: # no course in this location
                    for item in time_list:
                        object_xy = XY(x = location.rname, y = item)
                        row_list.append( object_xy ) #cell, operand: Object XY()
                else:

                    for item in time_list:
                        que_cell = db.Query(CSession).filter('w_day =', day).filter('loc =', t_key).filter('time =', item)  
                        result = que_cell.fetch(limit = 1) # should be: limit = 1
                        if len(result) != 0:
                            row_list.append(result[0]) #cell, operand:Course
                        else:
                            object_xy = XY(x = location.rname, y = item)
                            row_list.append( object_xy ) #cell, oerand: Object XY() 
                                                
                course_list.append(row_list)
                # end for location in location_list
            day_list.append(course_list) 
            # end for day in days
        
        doRender(self, 'td_setting.html', {'day_list' : day_list})

class PreAssignHandler(webapp.RequestHandler):
    def post():
        pass

class AssignTDHandler(webapp.RequestHandler):
    def post():
        pass

def main():
    application = webapp.WSGIApplication([
        ('/login', LoginHandler),
        ('/logout', LogoutHandler),
        ('/register', RegisterHandler),
        ('/main', MainHandler), 
        ('/show_user', ShowUserHandler),
        ('/delete_user', DeleteUserHandler),
        ('/show_setting', ShowSettingHandler),
        ('/add_location', AddLocationHandler),
        ('/pre_course', PreCourseHandler),
        ('/add_course', AddCourseHandler),
        ('/td_setting',TDSettingHandler),
        ('/assign_td', AssignTDHandler),
        ('/.*', IndexHandler)],
        debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()

