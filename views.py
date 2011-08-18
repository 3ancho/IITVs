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
 
#    def get_current_user(self):
#        logging.error('get_current_user')
#        pkey = self.session['userkey']
#        return db.get(pkey)

    def admin(self, current_user = None):
        if current_user == None:
            self.session = Session()
            pkey = self.session['userkey']
            current_user = db.get(pkey)

        '''check if current user is admin, if not direct to main.html''' 
        if current_user.admin == False:
            self.doRender( 'main.html', {'msg' : 'Require admin previlege!'})
            return False
        else:
            return True
           
# End Basehandler

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
        titles = ['Mon', 'Tue', 'Wed', 'Thr', 'Fri', 'Sat', 'Sun']

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
                        row_list.append(object_xy) #cell, operand: Object Cell()
                else:
                    for item in time_list:
                        que_cell = db.Query(CSession).filter('w_day =', day).filter('loc =', t_key).filter('time =', item)  
                        result = que_cell.fetch(limit = 1) 
                        if len(result) != 0: #Result is session obj, and it exists
                            session = result[0]
                            td = session.td
                            info = Compact(info1 = session, info2 = td) 
                            row_list.append( info )
                        else:
                            #object_xy = Cell(x = location.rname, y = item)
                            row_list.append('') #cell, oerand: Object Cell() 
                                                
                course_list.append(row_list)
            # end for location in location_list

            tab_view = Compact(info1 = course_list, \
                    info2 = titles[days.index(day)])
            day_list.append(tab_view) 
        # end for day in days
        
        self.doRender('main.html', {'day_list' : day_list})

class ShowUserHandler(BaseHandler):
    def get(self):
        if self.guest():
            return
        self.session = Session() 
        pkey = self.session['userkey']
        current_user = db.get(pkey)
        if current_user.admin:
            self.doRender( 'show_user.html', { })
        else:
            self.doRender( 'main.html', {'msg' : 'Require admin previlege!'})

    def post(self):
        if self.guest():
            return
        self.session = Session() 
        pkey = self.session['userkey']
        current_user = db.get(pkey)
        
        self.admin(current_user)

        que = db.Query(User)
        
        # Bellow 'True' is String value, that's correct!
        show_admin = self.request.get('show_admin')
        if show_admin == 'True': # if action is to show admin
            admin_list = que.filter('admin =', True).fetch(limit = 100)

            self.doRender( 'show_user.html', {'user_list' : admin_list, 'show_admin': 'cur_admin'  } )
            return

        else: # if action is to show normal user
            user_list = que.filter('admin =', False).fetch(limit = 500)
            que = db.Query(CSession) 
            
            self.doRender( 'show_user.html', {'user_list' : user_list, 'show_user': 'cur_user' } )
            return

class DeleteUserHandler(BaseHandler):
    def post(self):
        if self.guest():
            return
        self.session = Session()
        pkey = self.session['userkey']
        current_user = db.get(pkey)
        if not self.admin():
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
        if self.guest() or not self.admin():
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
        snumber = t_course.snumber
        
        que = db.Query(CSession)
        session_list = que.filter('cname =', name).filter('snumber =', snumber).fetch(limit = 100)
        for session in session_list:
            session.delete()
       
        t_course.delete()

        self.doRender('setup.html', {'msg': 'deleted course: ' + name})
        

class AddLocationHandler(BaseHandler):
    def get(self):
        if not self.admin():
            return
        form = LocationForm()
        self.doRender('add_location.html', {'form': form})
        

    def post(self):
        if self.guest():
            return
        pkey = self.session['userkey']
        current_user = db.get(pkey)
        
        form = LocationForm(self.request.POST) 
        if form.validate():
            result = db.Query(Location).filter('rname =', form.rname.data).fetch(limit = 1)
            if len(result) > 0:
                self.doRender('add_location.html', {'form': form, \
                        'msg': 'Error: Location(room) name conflict'})
                return
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
          
            # following code is checking conflict cname and snumber
            que = db.Query(Course).filter('cname =', t_cname).filter('t_snumber =', t_snumber)
            if len(que.fetch(limit = 1)) > 0:
               self.doRender('add_course.html', \
                       {'msg': 'Course Conflict', \
                        'loc_key':loc_key, 'time_index':time_index})
               return
            
            # following code is checking coflick sessions 
            for i in  t_csessions: 
                que_test = db.Query(CSession).filter('loc =', loc_key).filter('time =', time_index).filter('w_day =', i)
                result_test = que_test.fetch(limit = 1)
                if len(result_test) != 0:
                    self.doRender('add_course.html', \
                            {'msg': 'Session Conflict', \
                            'loc_key':loc_key, 'time_index':time_index})
                    return
            
            # Add Csessions instances.
            key_list = []
            for i in t_csessions:
                new_csession = CSession(loc = loc_key, time = time_index, \
                    cname = t_cname, snumber = t_snumber, \
                    csessions = t_csessions, w_day = i)
                key_list.append(new_csession.put())
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
        titles = ['Mon', 'Tue', 'Wed', 'Thr', 'Fri', 'Sat', 'Sun']
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
                        result = que_cell.fetch(limit = 1) 
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
            tab_view = Compact(info1 = course_list, \
                    info2 = titles[days.index(day)])
            day_list.append(tab_view) 
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

        self.doRender('td_session.html', {'msg': 'Add Success'})

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
        titles = ['Mon', 'Tue', 'Wed', 'Thr', 'Fri', 'Sat', 'Sun']
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
            tab_view = Compact(info1 = course_list, \
                    info2 = titles[days.index(day)])
            day_list.append(tab_view) 
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
        form = UserForm()
        self.doRender( 'td_setting.html', {'form': form, 'u': user, \
                'info': ', please update your profile'})

    def post(self):
        self.session = Session()
        pkey = self.session.get('userkey')
        user = db.get(pkey)
  
        form = UserForm(self.request.POST)
        if form.validate():
        
#            cwid = self.request.get('cwid')
#            major = self.request.get('major')
#            email = db.Email(self.request.get('email'))
#            phone = db.PhoneNumber(self.request.get('phone'))
#            d_hours = int(self.request.get('d_hours'))
            
            user.cwid = form.cwid.data 
            user.major = form.major.data 
            user.email = form.email.data 
            user.phone = form.phone.data 
            user.d_hours = form.d_hours.data
            user.put()

            self.doRender( 'td_setting.html', {'msg' : ', profile updated', 'u': user} )
        else: # form validation failed
            self.doRender('td_setting.html', {'form': form})

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
