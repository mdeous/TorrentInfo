#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from flask import Flask, flash, redirect, render_template, request, url_for

from torrentinfo import settings
from torrentinfo.lib.info import TorrentInfo

app = Flask(__name__)
app.config.from_object(settings)


@app.route('/')
def index():
    return render_template(
        'index.html',
        max_files=app.config['MAX_FILES']
    )


@app.route('/info', methods=['post'])
def info():
    torrents_info = {}
    files_info = request.files.getlist('file')

    # errors handling
    if len(files_info) == 1 and not files_info[0].filename:
        flash('No file(s) selected')
        return redirect(url_for('index'))
    elif len(files_info) > app.config['MAX_FILES']:
        flash('More than %d files selected (%d)' % (app.config['MAX_FILES'], len(files_info)))
        return redirect(url_for('index'))

    # gather information
    for file_info in files_info:
        file_name = file_info.filename
        file_content = file_info.read()
        torrent_info = TorrentInfo(file_content)
        trackers_info = torrent_info.get_trackers_info()
        torrents_info[file_name] = trackers_info

    return render_template(
        'info.html',
        torrents_info=torrents_info
    )


if __name__ == '__main__':
    app.run('127.0.0.1', 8080)
