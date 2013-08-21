import sys, os, logging

#from raven.contrib.django.raven_compat.middleware.wsgi import Sentry

from twisted.web.wsgi import WSGIResource
from twisted.python.threadpool import ThreadPool
from twisted.internet import reactor
from twisted.application import internet, service
from twisted.web import server, resource, static
from twisted.web.resource import ForbiddenResource

from path_settings import DEVELOPMENT_ADMIN_MEDIA, PRODUCTION_STATIC

# Only used if no logger is passed from plugin.
DEFAULT_LOGGER = logging.getLogger(__name__)


class ThreadPoolService(service.Service):
    '''
    A simple class that defines a threadpool on init
    and provides for starting and stopping it.
    '''
    def __init__(self, pool):
        self.pool = pool

    def startService(self):
        service.Service.startService(self)
        self.pool.start()

    def stopService(self):
        service.Service.stopService(self)
        self.pool.stop()


class Root(resource.Resource):
    '''
    A dumb wrapper over Resource that we use to assist in serving static media.
    '''
    def __init__(self, wsgi_resource):
        resource.Resource.__init__(self)
        self.wsgi_resource = wsgi_resource

    def getChild(self, path, request):
        path0 = request.prepath.pop(0)
        request.postpath.insert(0, path0)
        return self.wsgi_resource


class MediaService(static.File):
    '''
    A simple static service with directory listing disabled
    (gives the client a 403 instead of letting them browse
    a static directory).
    '''
    def directoryListing(self):
        # Override to forbid directory listing
        return ForbiddenResource()


def get_hendrix_resource(wsgi_application, deployment_type, port, logger=DEFAULT_LOGGER):
    '''
    Pseudo factory that returns the proper Resource object.
    Takes a deployment type and (for development) a port number.
    Returns a tuple (Twisted Resource, Twisted Application, Twisted Server)
    '''
    
    logger.info("Hendrix will deploy %s on port:%s" % (deployment_type, port))

    # Create and start a thread pool,
    wsgiThreadPool = ThreadPool()

    # The pool will stop when the reactor shuts down
    reactor.addSystemEventTrigger('after', 'shutdown', wsgiThreadPool.stop)

    hendrix_server = service.MultiService()
    tps = ThreadPoolService(wsgiThreadPool)
    tps.setServiceParent(hendrix_server)    

    # Use django's WSGIHandler to create the resource.
    hendrix_django_resource = WSGIResource(
        reactor, tps.pool,
        wsgi_application,
    )
    root = Root(hendrix_django_resource)

    # Now we need to handle static media.
    # Servce Django media files off of /media:
    '''
    if deployment_type == "local":
        admin_static = MediaService(os.path.join(os.path.abspath("."), DEVELOPMENT_ADMIN_MEDIA))
        staticrsrc = MediaService(os.path.abspath(".")
    else:
         Maybe we want to hardcode production and staging paths.  Maybe we don't.
        admin_static = MediaService(os.path.join(os.path.abspath("."), DEVELOPMENT_ADMIN_MEDIA))
        staticrsrc = MediaService(os.path.abspath(".")

    logger.debug("Adding admin static path: %s" % admin_static)
     Now that we have the static media locations, add them to the root.
    root.putChild("static_admin", admin_static)
    
    logger.debug("Adding static path: %s" % staticrsrc)
    root.putChild("static", staticrsrc)
    '''
    main_site = server.Site(root)
    internet.TCPServer(port, main_site).setServiceParent(hendrix_server)

    return hendrix_django_resource, hendrix_server
