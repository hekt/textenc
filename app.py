import os
from flask import Flask
from flask import request
from flask import Response
import urllib
import re

app = Flask(__name__)

def repHref(base_url, url, match_obj):
    for p in match_obj.groups():
        if p:
            return 'href="%s%s"' % (base_url, repRelPathToAbsPath(p, base_url))
    else:
        return None

def repRelPathToAbsPath(path, base_url):
    if re.match("(/)?\.+/", path):
        upper_depth = upperDepth(path)
        upper_path = upperDirectory(base_url, upper_depth)
        lower_path = re.sub("(/)?[\./]+/", '', path)
        
        return "%s/%s" % (upper_path, lower_path)
    else:
        return path

def upperDepth(relative_path):
    cnt = 0
    for s in relative_path.split('/'):
        if re.match("\.{2,}", s):
            cnt += (len(s) - 1)
    return cnt

def upperDirectory(url, depth):
    return '/'.join(url.split('/')[:-(depth + 1)])

@app.route('/<encode>/<path:url>')
def application(encode, url):
    p = re.compile("href=(?:\"([^\"]*?)\"|'([^']*?)')", re.I)
    base_url = "%s%s/" % (request.url_root, str(encode))
    repFunc = lambda x: repHref(base_url=base_url, url=url, match_obj=x)

    content_type = 'text/html; charset=%s' % encode
    output = re.sub(p, repFunc, urllib.urlopen(url).read())

    return Response(output, content_type=content_type)

@app.route('/')
def hello():
    return "hello"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
