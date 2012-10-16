# -*- coding:utf-8 -*-

import os
import urllib2
import re
from flask import Flask, Response, request, redirect, url_for, render_template


KNOWN_ENCODINGS = ('utf-8', 'euc-jp', 'shift_jis', 'iso-2022-jp')

app = Flask(__name__)


class Replacements(object):
    def doReplace(self, data, base_url, received_url):
        base_tag = '<base href="%s">' % received_url
        received_root = '/'.join(received_url.split('/')[:3])

        head_exp = re.compile("<head(\s+([^>]|\"[^\"]*?\"|'[^']*?'))*?>", re.I)
        href_exp = re.compile("(<a.*?href=[\"'])([^\"']*?)([\"'].*?>)", re.I)
        base_exp = re.compile(("<base(\s|href=[\"'][^\"']+[\"']|"
                               "target=[\"'][^\"']*[\"'])+>"), re.I)

        rep_func_head = lambda x: "\n".join([x.group(0), base_tag])
        rep_func_href = lambda x: self.hrefToUnderApp(x, base_url,
                                                      received_url,
                                                      received_root)

        # add base tag if not using one
        if re.search(base_exp, data) is None:
            data = re.sub(head_exp, rep_func_head, data)

        # replace link to under app url
        data = re.sub(href_exp, rep_func_href, data)

        return data

    def hrefToUnderApp(self, match_obj, base_url, received, received_root):
        path = match_obj.group(2)
        if re.match(received_root, path):
            return "".join([match_obj.group(1), base_url, path,
                            match_obj.group(3)])
        elif not re.match("http(s)?://", path):
            return "".join([match_obj.group(1), base_url,
                            self.relPathToAbsPath(path, received),
                            match_obj.group(3)])
        return match_obj.group(0)

    def relPathToAbsPath(self, path, base_url):
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
    def basicErrorPage(self, title, message, status_code=500):
        return render_template('error.html', error_title=title,
                               error_message=message), status_code

    def invalidParameter(self):
        title = u"パラメータが不足しているか、または不正です"
        message = (u"選択されたエンコード、もしくは URL が間違っている"
                   u"可能性があります。")
        return self.basicErrorPage(title, message)

    def invalidUrl(self):
        title = u"ウェブページを取得できません"
        message = u"指定された URL からウェブページを取得できませんでした。"
        return self.basicErrorPage(title, message)

    def decodeFailed(self):
        title = u"デコードに失敗しました"
        message = (u"実際に使われている物とは異なるエンコードが"
                   u"選択されたようです。")
        return self.basicErrorPage(title, message)

    def multiply(self):
        title = u"不正な URL です"
        message = u"%s を含むページでは利用できません。" % request.url_root
        return self.basicErrorPage(title, message)


@app.route('/form')
def form():
    encoding = request.args.get('encoding')
    url = request.args.get('url')

    if encoding is None or url is None:
        return ErrorPages().invalidParameter()

    if encoding == 'Ja':
        return redirect(url_for('autoEncodeJa', url=url))

    return redirect(url_for('encodeJa', encoding=encoding, url=url))


@app.route('/unspecified/<path:url>')
def unspecified(url):
    return render_template('unspecified.html', root_url=request.url_root,
                           received_url=url, encodings=KNOWN_ENCODINGS)


@app.route('/ja/<path:url>')
def autoEncodeJa(url):
    if url.find(request.url_root) != -1:
        return ErrorPages().multiply()

    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', request.environ['HTTP_USER_AGENT'])]

    try:
        url_obj = opener.open(url)
    except IOError:
        return ErrorPages().invalidUrl()
    except ValueError:
        return ErrorPages().invalidUrl()

    data = url_obj.read()

    for encoding in KNOWN_ENCODINGS:
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
        return ErrorPages().multiply()

    base_url = "%s%s/" % (request.url_root, str(encoding))
    content_type = 'text/html; charset=%s' % encoding

    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', request.environ['HTTP_USER_AGENT'])]

    try:
        url_obj = opener.open(url)
    except IOError:
        return ErrorPages().invalidUrl()
    except ValueError:
        return ErrorPages().invalidUrl()

    data = url_obj.read()

    try:
        data = data.decode(encoding)
    except UnicodeDecodeError:
        return ErrorPages().decodeFailed()

    data = Replacements().doReplace(data, base_url, url)
    data = data.encode(encoding)

    output = data

    return Response(output, content_type=content_type)


@app.route('/')
def index():
    return render_template('index.html', root_url=request.url_root)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # app.debug = True
    app.run(host="0.0.0.0", port=port)
