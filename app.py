import os
from flask import Flask
from flask import request
from flask import Response
import urllib
import re

app = Flask(__name__)

def repHref(base_url, match_obj):
    return "".join([match_obj.group(1), base_url,
                    match_obj.group(2), match_obj.group(3)])

def repUrl(url, match_obj):
    if not re.match("mailto:", match_obj.group(2)):
        return '%s="%s"' % (match_obj.group(1),
                            repRelPathToAbsPath(match_obj.group(2), url))
    return match_obj.group(0)

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
    url_exp = re.compile("(href|src|action)=[\"']((?:/)?(?:\.+/)*[^\"']*?)[\"']", re.I)
    href_exp = re.compile("(<a.*?href=[\"'])([^\"']*?)([\"'].*?>)", re.I)
    rep_func_url = lambda x: repUrl(url=url, match_obj=x)
    rep_func_href = lambda x: repHref(base_url=base_url, match_obj=x)
    base_url = "%s%s/" % (request.url_root, str(encode))

    content_type = 'text/html; charset=%s' % encode
    output = urllib.urlopen(url).read()
    output = re.sub(url_exp, rep_func_url, output)
    output = re.sub(href_exp, rep_func_href, output)

    return Response(output, content_type=content_type)

@app.route('/')
def hello():
    return "hello"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
