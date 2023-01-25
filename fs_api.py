import ssl
import json
import pprint

import urllib.request
import urllib.error
import urllib.parse

no_verify = ssl.create_default_context()
no_verify.check_hostname = False
no_verify.verify_mode = ssl.CERT_NONE

if getattr(ssl, '_https_verify_certificates', None):
    ssl._https_verify_certificates(False)

class HostString(str):
    """
        Comment: Special subclass of string, for storing arbitrary host-related
                 attributes (such as auth tokens) without losing any string behavior
    """
    def __new__(cls, *args, **kwds):
        return super(HostString, cls).__new__(cls, *args, **kwds)

class RESTUtil(object):
    show_default=False
    default_headers = {}
    port = 80

    def __init__(self, show=None, catch=True):
        self.hosts = {}
        self.curr_host = None
        self.catch=catch
        self.show_default=show if show != None else self.show_default

    @property
    def host(self):
        return self.curr_host

    @host.setter
    def host(self, hostname):
        """
            Comment: Retrieve the HostString object of a known host from its
                     host name or string definition. Even if the host definition 
                     is provided, we still need to key into self.hosts in case the 
                     client classes are storing things on their HostString objects.
        """
        try:
            if hostname in self.hosts:
                self.curr_host = self.hosts[hostname]
            else:
                self.curr_host = [h for h in self.hosts.values() if h == hostname][0]
            return self.curr_host
        except IndexError:
            raise KeyError("Unrecognized host/name %s" % hostname)

    def add_host(self, hostdef, hostname=None):
        hostname = hostname if hostname is None else hostdef
        self.hosts[hostname] = HostString(hostdef)
        if self.curr_host == None:
            self.curr_host = self.hosts[hostname]
        return hostname

    def command(self, protocol, postfix, method='POST', headers=None, show=None, **cmd_kwds):
        """
            Comment: A fairly generic RESTful API request builder. 
                     See subclasses for examples of use.
        """
        if show == None:
            show = self.show_default
        headers = {} if headers == None else headers
        url = '%s://%s:%s/%s' % (
            protocol,
            self.curr_host,
            self.port,
            postfix
        )
        request = urllib.request.Request(
            url,
            headers =dict(self.default_headers, **headers),
            data=bytes(json.dumps(cmd_kwds), encoding="utf-8") if cmd_kwds else None)
        request.get_method = lambda: method
        if show:
            self.request_pprint(request)
        try:
            cmd_out = urllib.request.urlopen(request, context=no_verify).read().decode('utf-8')
        except urllib.error.HTTPError as e:
            self.exception_pprint(e)
            if not self.catch:
                raise Exception("RESTful API command failed.")
            return
        try:
            cmd_out = json.loads(cmd_out)
        except ValueError:
            pass
        if show:
            print("\nCommand Output:")
            pprint.pprint(cmd_out)
            print("")
        return cmd_out

    @staticmethod
    def request_pprint(request):
        """
            Comment: Request info print function 
                     (for self.command with show=True)
        """
        print(request.get_method(), request.get_full_url(), 'HTTP/1.1')
        print('Host:', request.host)
        for key, value in request.headers.items():
            print(key.upper() + ':', str(value))
        if request.data != None:
            print()
            pprint.pprint(request.data)

    @staticmethod
    def exception_pprint(http_error):
        """
            Comment: HTTPError info print function
        """
        print(http_error.code, '--', http_error.reason)
        print(http_error.fp.read())
        print("")

class SVCREST(RESTUtil):
    """
        Comment: RESTful wrapper for the SVC CLI
    """

    def __init__(self, host, *args, **kwds):
        self.debug = kwds.pop('debug', False)
        super().__init__(*args, **kwds)
        self.add_host(host)

    @property
    def default_headers(self):
        return {'X-Auth-Token': getattr(self.curr_host, 'token', 'badtoken'),
                'Content-Type': 'application/json'}

    @property
    def port(self):
        return getattr(self, '_port', None) or ('7665' if self.debug else '7443')

    @property
    def protocol(self):
        return getattr(self, '_protocol', None) or ('http' if self.debug else 'https')

    def command(self, cmd, *args, method="POST", headers=None, show=None, **cmd_kwds):
        postfix = '/'.join(
            ['rest'] + [cmd] + [urllib.parse.quote(str(a)) for a in args]
        )
        return super().command(
            self.protocol,
            postfix,
            method=method,
            headers=headers,
            show=show,
            **cmd_kwds
        )

    def authenticate(self, username='superuser', password='passw0rd', show=None):
        cmd_out = self.command(
            'auth', show=show, method="POST", headers={'X-Auth-Username': username, 'X-Auth-Password': password}
        )
        if cmd_out:
            self.curr_host.token = cmd_out['token']
    """
       Comment:  First, set your cluster ipaddress.  
          It's assumed superuser/passw0rd (6 lines above) is the crednetial.
          After the authenticate call, you can issue any command in 
                s.command('') that is an svcinfo or svctask cmmand)
   """
s = SVCREST('fs9200-cluster1.esilabs.com')
s.authenticate('rick', 'ESI00bpic')
s.command('chhost/-name/POLDEV/37')