#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request

from torrentinfo.lib.info import TorrentInfo

app = Flask(__name__)
app.config['DEBUG'] = False


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/info', methods=['get', 'post'])
def info():
    file_info = request.files['file']
    file_name = file_info.filename
    file_content = file_info.read()
    torrent_info = TorrentInfo(file_content)
    trackers_info = torrent_info.get_trackers_info()
    return render_template(
        'info.html',
        file_name=file_name,
        trackers_info=trackers_info
    )


if __name__ == '__main__':
    app.run('127.0.0.1', 8080)
