import os
import urllib2
import re
from flask import Flask, Response, request, redirect, url_for, render_template

app = Flask(__name__)


class Replacements(object):
    def repHrefToUnderApp(self, base_url, received_root, match_obj):
        url = match_obj.group(2)
        if re.match(received_root, url):
            return "".join([match_obj.group(1), base_url, url,
                            match_obj.group(3)])
        return match_obj.group(0)

    def repUrlToAbs(self, url, match_obj):
        if not re.match("mailto:", match_obj.group(2)):
            return '%s="%s"' % (match_obj.group(1),
                                self.repRelPathToAbsPath(match_obj.group(2),
                                                         url))
        return match_obj.group(0)

    def repRelPathToAbsPath(self, path, base_url):
        if re.match("http(s)?://", path):
            return path
        else:
            upper_depth = self.upperDepth(path)
            upper_path = self.upperDirectory(base_url, upper_depth)
            lower_path = re.sub("(/)?[\./]+/", '', path)

            return "%s/%s" % (upper_path, lower_path)

    def upperDepth(self, relative_path):
        cnt = 0
        for s in relative_path.split('/'):
            if re.match("\.{2,}", s):
                cnt += (len(s) - 1)
        return cnt

    def upperDirectory(self, url, depth):
        return '/'.join(url.split('/')[:-(depth + 1)])


class ErrorPages(object):
    def decodeError(self):
        return render_template('decode-error.html',
                               root_url=request.url_root), 500

    def multiplyError(self):
        return render_template('multiply-error.html',
                               root_url=request.url_root), 500

    def invalidUrlError(self):
        return render_template('invalid-url-error.html',
                               root_url=request.url_root), 500


@app.route('/debug')
def debugPage():
    return request.environ['HTTP_USER_AGENT']

@app.route('/unspecified/<path:url>')
def unspecified(url):
    encodings = ('utf-8', 'euc-jp', 'shift_jis', 'iso-2022-jp')
    return render_template('unspecified.html', root_url=request.url_root,
                           received_url=url, encodings=encodings)


@app.route('/ja/<path:url>')
def autoEncodeJa(url):
    if url.find(request.url_root) != -1:
        return ErrorPages().multiplyError()

    encodings = ('utf-8', 'euc-jp', 'shift_jis', 'iso-2022-jp')

    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', request.environ['HTTP_USER_AGENT'])]
    
    try:
        url_obj = opener.open(url)
    except IOError:
        return ErrorPages().invalidUrlError()

    data = url_obj.read()

    for encoding in encodings:
        try:
            data = data.decode(encoding)
            break
        except UnicodeDecodeError:
            pass
    else:
        return redirect(url_for('unspecified', url=url))

    return redirect(url_for('encodeJa', encoding=encoding, url=url))


@app.route('/<encoding>/<path:url>')
def encodeJa(encoding, url):
    if url.find(request.url_root) != -1:
        return ErrorPages().multiplyError()

    base_url = "%s%s/" % (request.url_root, str(encoding))
    received_root = '/'.join(url.split('/')[:3])

    url_exp = re.compile(("(href|src|action)="
                          "[\"']((?:/)?(?:\.+/)*[^\"']*?)[\"']"), re.I)
    href_exp = re.compile("(<a.*?href=[\"'])([^\"']*?)([\"'].*?>)", re.I)
    R = Replacements()
    rep_func_url = lambda x: R.repUrlToAbs(url=url, match_obj=x)
    rep_func_href = lambda x: R.repHrefToUnderApp(base_url=base_url,
                                                  received_root=received_root,
                                                  match_obj=x)

    content_type = 'text/html; charset=%s' % encoding

    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', request.environ['HTTP_USER_AGENT'])]

    try:
        url_obj = opener.open(url)
    except IOError:
        return ErrorPages().invalidUrlError()

    data = url_obj.read()

    try:
        data = data.decode(encoding)
    except UnicodeDecodeError:
        return ErrorPages().decodeError()

    data = re.sub(url_exp, rep_func_url, data)
    data = re.sub(href_exp, rep_func_href, data)
    data = data.encode(encoding)

    output = data

    return Response(output, content_type=content_type)


@app.route('/')
def index():
    return render_template('index.html', root_url=request.url_root)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.debug = True
    app.run(host="0.0.0.0", port=port)
