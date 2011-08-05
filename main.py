#!/usr/bin/env python
# Ruoran Wang IITVs

import wsgiref.handlers
from google.appengine.ext import webapp
from views import *


def main():
    logging.getLogger().setLevel(logging.DEBUG)
    application = webapp.WSGIApplication([
        ('/login', LoginHandler),
        ('/logout', LogoutHandler),
        ('/register', RegisterHandler),
        ('/main', MainHandler), 
        ('/show_user', ShowUserHandler),
        ('/delete_user', DeleteUserHandler),
        ('/setup', SetupHandler),
        ('/add_location', AddLocationHandler),
        ('/pre_course', PreCourseHandler),
        ('/add_course', AddCourseHandler),
        ('/td_session', TDSessionHandler),
        ('/list_td', ListTDHandler),
        ('/pre_assign_td', PreAssignTDHandler),
        ('/assign_td', AssignTDHandler),
        ('/td_setting', TDSettingHandler),
        ('/user_info', UserInfoHandler),
        ('/.*', IndexHandler)],
        debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()

