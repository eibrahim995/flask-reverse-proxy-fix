from flask import Flask as App
# noinspection PyPackageRequirements
from werkzeug.contrib.fixers import ProxyFix


class ReverseProxyPrefixFix(object):
    """
    Flask middleware to ensure correct URLs are generated by Flask.url_for() where an application is under a reverse
    proxy. Specifically this middleware corrects URLs where a common prefix needs to be added to all URLs.

    For example: If client requests for an application are reverse proxied such that:
    `example.com/some-service/v1/foo` becomes `some-service-v1.internal/foo`, where `/foo` is a route within a Flask
    application `foo()`.

    Without this middleware, a call to `Flask.url_for('.foo')` would give: `/foo`. If returned to the client, as a
    'self' link for example, this would cause a request to `example.com/foo`, which would be invalid as the
    `/some-service/v1` prefix is missing.

    With this middleware, a call to `Flask.url_for('.foo')` would give: '/some-service/v1/foo', which will work if used
    by a client.

    This middleware is compatible with both relative and absolute URLs (i.e. `Flask.url_for('.foo')` and
    `Flask.url_for('.foo', _external=True)`.

    This middleware incorporates the `werkzeug.contrib.fixers.ProxyFix` middleware [1] and is based on the
    'Fixing SCRIPT_NAME/url_scheme when behind reverse proxy' Flask snippet [2].

    Note: Ensure the prefix value includes a preceding slash, but not a trailing slash (i.e. use `/foo` not `/foo/`).

    [1] http://werkzeug.pocoo.org/docs/0.14/contrib/fixers/#werkzeug.contrib.fixers.ProxyFix
    [2] http://flask.pocoo.org/snippets/35/
    """
    def __init__(self, app: App):
        """
        :type app: App
        :param app: Flask application
        """
        self.app = app.wsgi_app
        self.prefix = None

        if 'REVERSE_PROXY_PATH' in app.config:
            self.prefix = app.config['REVERSE_PROXY_PATH']

        self.app = ProxyFix(self.app)

        app.wsgi_app = self

    def __call__(self, environ, start_response):
        if self.prefix is not None:
            environ['SCRIPT_NAME'] = self.prefix
            path_info = environ['PATH_INFO']
            if path_info.startswith(self.prefix):
                environ['PATH_INFO'] = path_info[len(self.prefix):]

        return self.app(environ, start_response)
