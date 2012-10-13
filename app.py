import os
import urllib
import re
from flask import Flask, Response, request, redirect, url_for, render_template

app = Flask(__name__)


def repHref(base_url, domain, match_obj):
    url = match_obj.group(2)
    if re.match(domain, url):
        return "".join([match_obj.group(1), base_url, url, match_obj.group(3)])
    return match_obj.group(0)


def repUrl(url, match_obj):
    if not re.match("mailto:", match_obj.group(2)):
        return '%s="%s"' % (match_obj.group(1),
                            repRelPathToAbsPath(match_obj.group(2), url))
    return match_obj.group(0)


def repRelPathToAbsPath(path, base_url):
    if re.match("http(s)?://", path):
        return path
    else:
        upper_depth = upperDepth(path)
        upper_path = upperDirectory(base_url, upper_depth)
        lower_path = re.sub("(/)?[\./]+/", '', path)

        return "%s/%s" % (upper_path, lower_path)


def upperDepth(relative_path):
    cnt = 0
    for s in relative_path.split('/'):
        if re.match("\.{2,}", s):
            cnt += (len(s) - 1)
    return cnt


def upperDirectory(url, depth):
    return '/'.join(url.split('/')[:-(depth + 1)])


@app.route('/ja/<path:url>')
def autoEncodeJa(url):
    if url.find(request.url_root) != -1:
        return 'invalid request'
    
    lookup = ('utf-8', 'euc-jp', 'shift_jis', 'iso-2022-jp')

    data = urllib.urlopen(url).read()

    for encoding in lookup:
        try:
            data = data.decode(encoding)
            break
        except UnicodeDecodeError:
            pass
    else:
        encoding = 'ascii'

    return redirect(url_for('encodeJa', encoding=encoding, url=url))


@app.route('/<encoding>/<path:url>')
def encodeJa(encoding, url):
    if url.find(request.url_root) != -1:
        return 'invalid request'

    base_url = "%s%s/" % (request.url_root, str(encoding))
    domain = '/'.join(url.split('/')[:3])

    url_exp = re.compile(("(href|src|action)="
                          "[\"']((?:/)?(?:\.+/)*[^\"']*?)[\"']"), re.I)
    href_exp = re.compile("(<a.*?href=[\"'])([^\"']*?)([\"'].*?>)", re.I)
    rep_func_url = lambda x: repUrl(url=url, match_obj=x)
    rep_func_href = lambda x: repHref(base_url=base_url, domain=domain,
                                      match_obj=x)

    content_type = 'text/html; charset=%s' % encoding
    output = urllib.urlopen(url).read().decode(encoding)
    output = re.sub(url_exp, rep_func_url, output)
    output = re.sub(href_exp, rep_func_href, output)

    return Response(output.encode(encoding), content_type=content_type)


@app.route('/')
def index():
    url = "%s%s/" % (request.url_root, "ja")
    return render_template('index.html', url=url)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # app.debug = True
    app.run(host="0.0.0.0", port=port)
