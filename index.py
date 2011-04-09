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
    ''' time matching pairs 
        8:30am-9:45am 	    0
        10:00am-11:15am     1
        11:30am-12:40pm 	2
        1:50pm-3:00pm 	    3
        3:15pm-4:30pm 	    4
        5:00pm-6:10pm 	    5
        6:30pm-9:10pm       6
    '''
    created = db.DateTimeProperty(auto_now = True)
    cname = db.StringProperty() # course name (major)
    cnumber = db.IntegerProperty() # course number 
    loc = db.ReferenceProperty(Location)
    time = db.IntegerProperty() # time = [0 to 6]
    csessions = db.StringProperty() # '1234567' 
    #lecturer = db.StringProperty() # lecturer name
    #start = db.TimeProperty()
    #end = db.TimeProperty()

class CSession(Course): #course session
    td = db.ReferenceProperty(User)
    w_day = db.StringProperty() # one digit number
    td_list = db.ListProperty(db.Key)

class XY(db.Model): # an object helps to pass values
    x = db.StringProperty() # row: location -> location.rname
    y = db.IntegerProperty() # column: time slot -> Ingeter
    z = db.StringProperty() # specify a day
    zz = db.StringProperty() # specify course_session name

# end of class definitions, start of helper functions

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

# end of helper functions, start of Handlers

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
            self.redirect('/main') 
            #doRender(self,'main.html', {} ) # if ok, go to main.html (logged in)
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
        location_list = que.fetch(limit = 500) # number of rows

        days = ['1','2','3','4','5','6','7'] 
        day_list = [] # list of course_list

        for day in days:
            course_list = [] # list of row_list
            #row_list = [] # may deleted
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
    '''
    Correspond to (setting.html)
    '''
    def get(self):
        if noUser(self):
            return
        que = db.Query(Location)
        location_list = que.fetch(limit = 500) # number of rows

        c_list = [] # list of row_list
        time_list = [0,1,2,3,4,5,6]

        for location in location_list:
            row_list = []
            row_list.append(location) #row_list[0]: operand Location
            t_key = location.key()

            for item in time_list:
                object_xy = XY(x = str(location.key()), y = item)
                row_list.append( object_xy ) #cell, oerand: Object XY() 
            c_list.append(row_list)
        # This c_list only have Location (1st for each row)
        # and XY(add bottoms)

        que_recent = db.Query(CSession).order('-created')
        cs_list = que_recent.fetch(limit = 6)
        doRender(self, 'setting.html', {'course_list' : c_list, 'csession_list' : cs_list}) 

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

        self.redirect('/show_setting')

class PreCourseHandler(webapp.RequestHandler):
    def post(self):
        if noUser(self):
            return
        loc_key = self.request.get('row')
        time_index = int(self.request.get('column')) 
        doRender(self, 'add_course.html', \
                {'loc_key' : loc_key, 'time_index' : time_index} )

class AddCourseHandler(webapp.RequestHandler):
    '''
    Add both Course and CSession
    '''
    def post(self):
        if noUser(self):
            return
        location_key = db.Key(self.request.get('loc_key'))
        time_index = int(self.request.get('time_index'))
        t_cname = self.request.get('cname')
        t_cnumber = int(self.request.get('cnumber'))
        t_csessions = self.request.get('csessions') # String of numbers.
        #t_time = self.request.get('time')  # March 31 need improve!
        ''' 
        que = db.Query(Location).filter('rname =', location_name) 
        location_key = que.fetch(limit = 1)[0].key()
        '''
        for i in  t_csessions: # this loop is to find if a conflict exists.
            que_test = db.Query(CSession).filter('loc =', location_key).filter('time =', time_index).filter('w_day =', i)
            result_test = que_test.fetch(limit = 1)
            if len(result_test) != 0:
                doRender(self,'setting.html', {'msg': 'Session Conflict'})
                return

        for i in t_csessions:
            new_csession = CSession(loc = location_key, time = time_index, \
                cname = t_cname, cnumber = t_cnumber, \
                csessions = t_csessions, w_day = i)
            new_csession.put()
        
        new_course = Course(loc = location_key, time = time_index, \
                cname = t_cname, cnumber = t_cnumber, csessions = t_csessions )
        new_course.put()
        self.redirect('/show_setting')

class TDSettingHandler(webapp.RequestHandler):
    def get(self):
        '''
        Disply 7 Sheet of data. Display Course_Sessions.
        '''
        if noUser(self):
            return
        que = db.Query(Location)
        location_list = que.fetch(limit = 500) # number of rows

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
                        result = que_cell.fetch(limit = 1) # A Query for CSession Object, cs result
                        if len(result) != 0:
                            #location_name = result[0].loc.rname # result[0] is CSession Obj
                            cname = result[0].cname
                            object_xy = XY(x = str(result[0].key()), z = cname)
                            row_list.append(object_xy) #cell, operand: Object XY(), have z element 
                        else:
                            object_xy = XY(x = location.rname, y = item)
                            row_list.append( object_xy ) #cell, oerand: Object XY() 
                                                
                course_list.append(row_list)
                # end for location in location_list
            day_list.append(course_list) 
            # end for day in days
        
        doRender(self, 'td_setting.html', {'day_list' : day_list})

class ListTDHandler(webapp.RequestHandler):
    def post(self):
        '''
        When TD select a desired session, TD's key(current User key)
        will be added to this session's td_list.
        '''
        if noUser(self):
            return
        self.session = Session()
        user_key = self.session['userkey'] 

        cs_key = db.Key(self.request.get('cs_key'))
        cs = db.get(cs_key) # Course Session Obj

        cs.td_list.append(user_key)
        cs.put()

        self.redirect('/td_setting')

class PreAssignTDHandler(webapp.RequestHandler):
    def get(self):
        '''
        Disply 7 sheets. Display Course_Sessions.
        '''
        if noUser(self):
            return
        que = db.Query(Location)
        location_list = que.fetch(limit = 500) # number of rows

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
                        object_xy = XY(x = ' ')
                        row_list.append( object_xy ) #cell, operand: Object XY()
                else:

                    for item in time_list:
                        que_cell = db.Query(CSession).filter('w_day =', \
                                day).filter('loc =', t_key).filter('time =', item)  
                        result = que_cell.fetch(limit = 1) 
                        
                        if len(result) != 0:
                            row_list.append(result[0]) # CS object 
                        else:
                            row_list.append(" ") # empty string
                course_list.append(row_list)
                # end for location in location_list
            day_list.append(course_list) 
            # end for day in days
        
        doRender(self, 'pre_assign_td.html', {'day_list' : day_list})

    def post(self):
        '''
        When Clicked, a td_list of that session will displayed.
        '''
        if noUser(self):
            return
         
        cs_key = db.Key(self.request.get('cs_key'))
        cs = db.get(cs_key) # CSession obj
        
        td_list = []
        for key in cs.td_list:
            a_td = []
            user = db.get(key) # User Object
            #a_td.append(user.key())
            #a_td.append(user.name)
            #a_td.append(user.username)
            #a_td.append(user.password)
            td_list.append(user)

        doRender(self, 'show_td_list.html', {'td_list' : td_list, 'cs_key' : cs_key})

class AssignTDHandler(webapp.RequestHandler):
    def post(self):
        td_key = db.Key( self.request.get('td_key') )
        cs_key = db.Key( self.request.get('cs_key') )
        td = db.get(td_key)
        cs = db.get(cs_key)
        
        # Update TD assiged hours !!!!!!
        cs.td = td_key
        cs.td_list.remove(td_key)
        cs.put()
       
        doRender(self, 'assign_ok.html', {'td': td.name, 'cs': cs.cname, 'day': cs.w_day} ) 

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
        ('/list_td', ListTDHandler),
        ('/pre_assign_td',PreAssignTDHandler),
        ('/assign_td',AssignTDHandler),
        ('/.*', IndexHandler)],
        debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()

