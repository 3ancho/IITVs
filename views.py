# Ruoran Wang IITVs views:
# Handlers....

import os
import logging
import hashlib
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from util.sessions import Session
from models import *


# BaseHandler
class BaseHandler(webapp.RequestHandler):
    def guest(self):
       '''
       For every page,except login and register, guest check is needed.
       If not member, redirect to home.
       '''
       self.session = Session()
       pkey = self.session.get('userkey')
       if pkey == None:
           return True 
       else:
           return False

    def doRender(self, tname = 'index.html', values = {}):
        if tname == '/' or tname == '' or tname == None:
            tname = 'index.html' # this block is required, as path is None.

        if tname[0] == '/':
            tname = tname[1:] 
        
        login_or_signin = tname == 'loginscreen.html' \
                or tname == 'register.html' \
#                or tname == 'loginscreen.html'\
#                or tname == 'register.html'\
#                or tname =='/login' \
#                or tname =='/register' 
        logging.debug('It is login or signin, tname is:' + tname)

        if self.guest() and not login_or_signin:
            logging.debug('guest want to go !login_or_signin, redirect')
            # a msg should be here
            tname = 'index.html'

        temp = os.path.join(os.path.dirname(__file__), 'templates/' + tname)
        if not os.path.isfile(temp):
            temp = os.path.join(os.path.dirname(__file__), 'templates/not_found.html')    
            # not_found.html should be edited.
            
        # Make a copy of the dictionary and add basic values
        newval = dict(values)
        newval['path'] = self.request.path
        if 'username' in self.session:
            newval['username'] = self.session['username']
        admin = self.session.get('admin')
        if admin != 'False':
            newval['admin'] = admin
        
        outstr = template.render(temp, newval)
        self.response.out.write(outstr)
        return True
            
# End Basehandler


# Move this to
def admin(handler):
    '''
    check if current user is admin, return true if yes.
    Ruoran 0805: It is not needed, seems like.
    '''
    current_user = db.get(pkey)
    if current_user.admin == False:
        self.doRender( 'main.html', {'msg' : 'Require admin previlege!'})
        return

#def doRender(handler, tname , values = {}):
#    if tname == '/' or tname == '' or tname == None:
#        tname = 'index.html' # this block is required, as path is None.
#
#    login_or_signin = tname == '/loginscreen.html' or tname == '/register.html' 
#    
#    if guest(handler) and not login_or_signin:
#        logging.info('oh, guest wants to go elsewhere than just login or signin')
#        # a msg should be here
#        tname = 'index.html'
#
#    temp = os.path.join(os.path.dirname(__file__), 'templates/' + tname)
#    if not os.path.isfile(temp):
#        temp = os.path.join(os.path.dirname(__file__), 'templates/not_found.html')    
#        # not_found.html should be edited.
#        
#    # Make a copy of the dictionary and add basic values
#    newval = dict(values)
#    newval['path'] = handler.request.path
#    if 'username' in handler.session:
#        newval['username'] = handler.session['username']
#    admin = handler.session.get('admin')
#    if admin != 'False':
#        newval['admin'] = admin
#    
#    outstr = template.render(temp, newval)
#    handler.response.out.write(outstr)
#    return True

# end of helper functions, start of Handlers

class RegisterHandler(BaseHandler):
    def get(self):
        form = RegisterForm()
        self.doRender('register.html', {'form': form} ) 

    def post(self):
        self.session = Session()

        form = RegisterForm(self.request.POST)
        if form.validate():
            que = db.Query(User).filter('username =', form.username.data) 
            result = que.fetch(limit = 1)
            if len(result) > 0: # If the username exist, display error msg
                self.doRender('register.html', \
                     {'form': form, 'msg': 'Username exist'})
                return


            que = User.all(keys_only = True) # get keys only, faster than entities.
            result = que.fetch(limit = 1)
            if len(result) == 0: 
                admin_flag = True
            else:
                admin_flag = False


            m = hashlib.sha224(form.password.data) #Passwd hash
            newuser = User(name = form.name.data, \
                    username = form.username.data, \
                    password = m.hexdigest(), \
                    admin = admin_flag ) # Default value is False

            pkey = newuser.put()
            self.session['username'] = form.username.data 
            self.session['userkey'] = pkey
            self.doRender( 'register.html', \
                    {'form': form, \
                    'msg' : 'Register Success! Welcome, '\
                    + form.username.data} )
        else:
            self.doRender('register.html', {'form': form}) 
        '''
        n = self.request.get("name")
        un = self.request.get("username")
        pw = self.request.get("password")

        if pw == '' or un == '' or n == '':
            self.doRender(
                    'register.html',
                    {'error' : 'Please fill in all fields'} )
            return

        que = db.Query(User).filter('username =', un)
        results = que.fetch(limit = 1)

        if len(results) > 0:
            self.doRender(
                    'register.html',
                    {'error' : 'Username already exists'} )
            return
        #if success, create new user
        ''' 

#        if pw == '' or un == '':
#            self.doRender('loginscreen.html', \
#                    {'error': 'Please specify Username and Password'} )
#            logging.debug('login handler with no login info')
#            return
class LoginHandler(BaseHandler):
    def get(self):
        form = LoginForm()
        self.doRender('loginscreen.html', {'form': form})
    
    def post(self):
        self.session = Session()

        form = LoginForm(self.request.POST)
        if form.validate():
            self.session.delete_item('username')
            self.session.delete_item('userkey')
            self.session.delete_item('admin')
            
            un = form.username.data 
            pw = form.password.data 
            m = hashlib.sha224(pw)
            que = db.Query(User).filter('username =', un).filter('password =', m.hexdigest())
            # que = que.filter('password =', m.hexdigest())
            # above two may combine
            results = que.fetch(limit = 1)

            if len(results) > 0:
                user = results[0]
                self.session['userkey'] = user.key()
                self.session['username'] = un
                self.session['admin'] = user.admin
                self.redirect('/main') 
                #self.doRender('main.html', {} ) # if ok, go to main.html (logged in)
            else:
                self.doRender(
                        'loginscreen.html',
                        {'error': 'Username or Password wrong', \
                         'form': form} )
        else: # if form.validate() Fails.
            self.doRender('loginscreen.html', {'form': form} )

class LogoutHandler(BaseHandler):
    def get(self):
        if self.guest():
            return
        self.session.delete_item('username')
        self.session.delete_item('userkey')
        self.session.delete_item('admin')
        self.doRender( 'index.html', {'msg' : ' Logout successful.'} ) 

class IndexHandler(BaseHandler):
    # show the index page, if login, redirect to main page
    def get(self):
        logging.debug('went throught Index Handler, with path:')
        self.doRender(self.request.path)
        
class MainHandler(BaseHandler):
    def get(self):
        if self.guest():
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
                        object_xy = Cell(x = location.rname, y = item)
                        row_list.append( object_xy ) #cell, operand: Object Cell()
                else:

                    for item in time_list:
                        que_cell = db.Query(CSession).filter('w_day =', day).filter('loc =', t_key).filter('time =', item)  
                        result = que_cell.fetch(limit = 1) # should be: limit = 1
                        if len(result) != 0: # Result is session obj, and it exists
                            session = result[0]
                            td = session.td
                            info = Compact(info1 = session, info2 = td) 
                            row_list.append( info ) #cell, operand: Session
                        else:
                            #object_xy = Cell(x = location.rname, y = item)
                            row_list.append( '' ) #cell, oerand: Object Cell() 
                                                
                course_list.append(row_list)
                # end for location in location_list
            day_list.append(course_list) 
            # end for day in days
        
        self.doRender('main.html', {'day_list' : day_list})


class ShowUserHandler(BaseHandler):
    def get(self):
        if self.guest():
            return
        
        pkey = self.session['userkey']
        current_user = db.get(pkey)
        if current_user.admin:
            self.doRender( 'show_user.html', { })
        else:
            self.doRender( 'main.html', {'msg' : 'Require admin previlege!'})

    def post(self):
        if self.guest():
            return
        pkey = self.session['userkey']
        current_user = db.get(pkey)
        if current_user.admin == False:
            self.doRender( 'main.html', {'msg' : 'Require admin previlege!'})
            return

        que = db.Query(User)
        
        # Bellow 'True' is String value, that's correct!
        if self.request.get('show_admin') == 'True': # if this will show admin
            admin = que.filter('admin =', True)
            admin = admin.fetch(limit = 100) 
            self.doRender( 'show_user.html', {'user_list' : admin } )
            return
        else:
            user = que.filter('admin =', False)
            user = user.fetch(limit = 500)
            self.doRender( 'show_user.html', {'user_list' : user } )
            return

class DeleteUserHandler(BaseHandler):
    def post(self):
        if self.guest():
            return
        pkey = self.session['userkey']
        current_user = db.get(pkey)
        
        if current_user.admin == False:
            self.doRender( 'main.html', {'msg' : 'Require admin previlege!'})
            return

        delete_list = self.request.get_all('key_to_delete')
        ''' # Testing!
        self.doRender( 'test.html', {'msg' : first[0], 'msg2': str(len(first))})
        return
        '''
        if len(delete_list) == 0:
            self.doRender( 'show_user.html', {})
            return

        for item in delete_list:
            que = db.Query(User).filter('username =', item)
            result = que.fetch(limit = 1)
            result[0].delete()

        self.doRender( 'show_user.html', {})

class SetupHandler(BaseHandler):
    '''
    Correspond to (setup.html)
    '''
    def get(self):
        if self.guest():
            return
        que = db.Query(Location)
        location_list = que.fetch(limit = 200) # number of rows(locations)

        c_list = [] # list of row_list
        time_list = [0,1,2,3,4,5,6] # displayed as columns

        for location in location_list:
            row_list = []
            row_list.append(location) #row_list[0]: operand Location
            t_key = location.key()

            for item in time_list:
                cell = Cell(x = str(location.key()), y = item)
                row_list.append( cell ) 
            c_list.append(row_list)
        # This c_list[0] is an instance of Location (1st for each row)
        # c_list[1:] are instance of Cell(which are insite "add" buttons)
        # Cell.x is x-coordinate, which is location. Cell.y is time.
        # When an 'add' button clicked, Cell.x and Cell.y are passed to next step, Add Course. 

        que_recent = db.Query(Course).order('-created')
        new_courses = que_recent.fetch(limit = 3)
        self.doRender( 'setup.html', {'course_list' : c_list,\
                'new_courses' : new_courses}) 

class QuickDeleteHandler(BaseHandler):
    def get(self):
        pass

    def post(self):
        course_key = self.request.get('course_key')
        t_course = db.get(course_key)
        name = t_course.cname
        t_course.delete()

        self.doRender('setup.html', {'msg': 'deleted course: ' + name})
        

class AddLocationHandler(BaseHandler):
    def get(self):
        form = LocationForm()
        self.doRender('add_location.html', {'form': form})
        

    def post(self):
        if self.guest():
            return
        pkey = self.session['userkey']
        current_user = db.get(pkey)
        
        form = LocationForm(self.request.POST) 
        if form.validate():
            new_location = Location(rname = form.rname.data, \
                    camera = form.camera.data, \
                    size = form.size.data )
            new_location.put()
            self.redirect('/setup')
        else:
            self.doRender('add_location.html', {'form': form})

#        t_rname = self.request.get('name')
#        t_camera = self.request.get('camera')
#        t_size = self.request.get('size')

        # 0807 trying wtf
#       LocationForm = model_form(Location)
#       form = LocationForm(obj = new_location)
#       self.doRender('not_found.html', {'form':form, 'msg':'form haha' })
        # 0807 end trying wtf


class PreCourseHandler(BaseHandler):
    def post(self):
        if self.guest():
            return
        loc_key = self.request.get('row')
        time_index = int(self.request.get('column')) 
#        self.redirect('/add_course') # this will not redirect values.
        form = CourseForm()
        self.doRender( 'add_course.html', \
                {'loc_key' : loc_key, 'time_index' : time_index, \
                'form': form} )

class AddCourseHandler(BaseHandler):
    '''
    Add both Course and CSession
    '''
    def get(self):
        pass # this method is not used now.
        form = CourseForm()
        self.doRender('add_course.html', {'form':form})

    def post(self):
        if self.guest():
            return
        # loc_key and time_index are hidden form attributes.
        # Those two attr is determined by the position in the table.
        loc_key = db.Key(self.request.get('loc_key'))
        time_index = int(self.request.get('time_index'))

        form = CourseForm(self.request.POST)

        if form.validate():
            t_cname = form.cname.data 
            t_snumber = int(form.snumber.data)
            t_csessions = form.csessions.data
            
            for i in  t_csessions: # this loop is to find conflict session 
                que_test = db.Query(CSession).filter('loc =', loc_key).filter('time =', time_index).filter('w_day =', i)
                result_test = que_test.fetch(limit = 1)
                if len(result_test) != 0:
                    self.doRender('add_course.html', \
                            {'msg': 'Session Conflict', \
                            'loc_key':loc_key, 'time_index':time_index})
                    return
            
            # Add Csessions instances.
            for i in t_csessions:
                new_csession = CSession(loc = loc_key, time = time_index, \
                    cname = t_cname, snumber = t_snumber, \
                    csessions = t_csessions, w_day = i)
                new_csession.put()
            # Add a Course instances, which is parent of previous sessions 
            new_course = Course(loc = loc_key, time = time_index, \
                    cname = t_cname, snumber = t_snumber, csessions = t_csessions )
            new_course.put()
            self.redirect('/setup')
        else:
            self.doRender( 'add_course.html', \
                {'loc_key' : loc_key, 'time_index' : time_index, \
                'form': form, 'msg':'form valid failed'} )

class TDSessionHandler(BaseHandler):
    def get(self):
        '''
        Disply 7 Sheet of data. Display Course_Sessions.
        '''
        if self.guest():
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
                        object_xy = Cell(x = location.rname, y = item)
                        row_list.append( object_xy ) #cell, operand: Object Cell()
                else:

                    for item in time_list:
                        que_cell = db.Query(CSession).filter('w_day =', day).filter('loc =', t_key).filter('time =', item)  
                        result = que_cell.fetch(limit = 1) # A Query for CSession Object, cs result
                        if len(result) != 0:
                            #location_name = result[0].loc.rname # result[0] is CSession Obj
                            cname = result[0].cname
                            object_xy = Cell(x = str(result[0].key()), z = cname)
                            row_list.append(object_xy) #cell, operand: Object Cell(), have z element 
                        else:
                            object_xy = Cell(x = location.rname, y = item)
                            row_list.append( object_xy ) #cell, oerand: Object Cell() 
                                                
                course_list.append(row_list)
                # end for location in location_list
            day_list.append(course_list) 
            # end for day in days
        
        self.doRender( 'td_session.html', {'day_list' : day_list})

class ListTDHandler(BaseHandler):
    def post(self):
        '''
        This may combined with TDSessionHandler
        When TD select a desired session, TD's key(current User key)
        will be added to this session's td_list.
        '''
        if self.guest():
            return
        self.session = Session()
        user_key = self.session['userkey'] 

        cs_key = db.Key(self.request.get('cs_key'))
        cs = db.get(cs_key) # Course Session Obj
        if user_key in cs.td_list:
            self.doRender( 'td_session.html', {'msg': \
                    'you have selected this session'})
            return

        cs.td_list.append(user_key)
        cs.put()

        self.redirect('/td_session')

class PreAssignTDHandler(BaseHandler):
    def get(self):
        '''
        Disply 7 sheets. Display Course_Sessions.
        '''
        if self.guest():
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
                        object_xy = Cell(x = ' ')
                        row_list.append( object_xy ) #cell, operand: Object Cell()
                else:

                    for item in time_list:
                        que_cell = db.Query(CSession).filter('w_day =', \
                                day).filter('loc =', t_key).filter('time =', item)  
                        result = que_cell.fetch(limit = 1) 
                        
                        if len(result) != 0:
                            if result[0].td != None:
                                row_list.append(' ')
                            else:
                                row_list.append(result[0]) # CS object 
                        else:
                            row_list.append(' ') # empty string
                course_list.append(row_list)
                # end for location in location_list
            day_list.append(course_list) 
            # end for day in days
        
        self.doRender( 'pre_assign_td.html', {'day_list' : day_list})

    def post(self):
        '''
        When Clicked, a td_list of that session will displayed.
        '''
        if self.guest():
            return
         
        cs_key = db.Key(self.request.get('cs_key'))
        cs = db.get(cs_key) # CSession obj
         
        td_list = []
        for key in cs.td_list:
            a_td = []
            user = db.get(key) # User Object
            td_list.append(user)

        self.doRender( 'show_td_list.html', {'td_list' : td_list, 'cs_key' : cs_key})

class AssignTDHandler(BaseHandler):
    def post(self):
        td_key = db.Key( self.request.get('td_key') )
        cs_key = db.Key( self.request.get('cs_key') )
        td = db.get(td_key)
        cs = db.get(cs_key)
       
        td.a_hours = td.a_hours + 1
        cs.td = td_key
        cs.td_list.remove(td_key)
        cs.put()
        td.put()
       
        self.doRender( 'assign_ok.html', {'td': td.name, 'cs': cs.cname, 'day': cs.w_day} ) 

class TDSettingHandler(BaseHandler):
    def get(self):
        if self.guest():
            return
        self.session = Session()
        key = self.session.get('userkey')
        user = db.get(key) 
        self.doRender( 'td_setting.html', {'u': user})

    def post(self):
        self.session = Session()
        pkey = self.session.get('userkey')
        user = db.get(pkey)
   
        cwid = self.request.get('cwid')
        major = self.request.get('major')
        email = db.Email(self.request.get('email'))
        phone = db.PhoneNumber(self.request.get('phone'))
        d_hours = int(self.request.get('d_hours'))
        
        user.cwid = cwid
        user.major = major
        user.email = email
        user.phone = phone
        user.d_hours = d_hours
        user.put()

        self.doRender( 'td_setting.html', {'msg' : 'info updated'} )

class UserInfoHandler(BaseHandler):
    def get(self):
        if self.guest():
            return
        self.session = Session()
        pkey = self.session.get('userkey')
        user = db.get(pkey)
        name = user.name
        
        que = db.Query(CSession).filter('td =', pkey) 
        session_list = que.fetch(limit = 100)
        self.doRender( 'user_info.html', {'sessions' : session_list, \
                'length': str(len(session_list)), \
                'name': name})
                
    def post(self):
        pass

class Jinja2Handler(BaseHandler):
    def get(self):
        self.doRender('Jinja2.html', {'name': 'ruoran', 'pet': 'nini'}) 
