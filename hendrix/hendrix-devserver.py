import os, sys
import imp
DEPLOYMENT_TYPE = "local"
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.local' #If the try block above did not cause exit, we know that this module exists.

from twisted.internet import reactor
from hendrix.deploy_functions import get_hendrix_resource
from hendrix.path_settings import * #Just to set the appropriate sys.path
from twisted.internet.error import CannotListenError

print "Here's your sys.path: %s" % sys.path

try:
    PORT = int(sys.argv[2])
    WSGI = imp.load_source('wsgi', sys.argv[1])
except IndexError:
    exit("usage: hendrix-devserver.py <wsgi_module> <PORT>")

wsgi_application = WSGI.application

resource, server = get_hendrix_resource(wsgi_application, DEPLOYMENT_TYPE, port=PORT)

try:
    server.startService()
    print ("Listening on port %s" % PORT)
    reactor.run()
except CannotListenError, e:
    thread_pool = server.services[0].pool
    thread_pool.stop()
    os.system( [ 'clear', 'cls' ][ os.name == 'nt' ] )
    exit("Looks like you already have devserver running on this machine.\
    \nPlease stop the other process before trying to launch a new one.")