#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import socket
import struct
import sys
from random import randrange
from urllib import urlopen
from urlparse import urlparse

from torrentinfo.lib import libtorrent as lt

CONNECTION_ID = 0x41727101980
ACTION_CONNECT = 0x0
ACTION_SCRAPE = 0x2
ACTION_ERROR = 0x3


class TorrentInfo(object):
    def __init__(self, torrent_file):
        # parse .torrent file
        if isinstance(torrent_file, file):
            data = lt.bdecode(torrent_file.read())
            torrent_file.close()
        else:
            data = lt.bdecode(torrent_file)
        info_obj = lt.torrent_info(data)
        self.trackers = data['announce-list'][0]  # use only IPv4 trackers

        # add torrent to session
        # noinspection PyArgumentList
        session = lt.session()
        self.torrent_handle = session.add_torrent({
            'save_path': '/tmp',
            'storage_mode': lt.storage_mode_t.storage_mode_sparse,
            'paused': True,
            'ti': info_obj
        })
        self.torrent_hash = self.torrent_handle.info_hash().to_bytes()

        # create UDP socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(8)

    def get_trackers_info(self):
        info = {}
        for tracker in self.trackers:
            tracker_info = {}
            parsed_url = urlparse(tracker)
            if parsed_url.scheme == 'udp':
                tracker_info.update(self._get_udp_info(parsed_url.hostname, parsed_url.port))
            elif parsed_url.scheme in ('http', 'https'):
                tracker_info.update(self._get_http_info(tracker.replace('announce', 'scrape')))
            else:
                # TODO: issue warning here
                continue
            info[tracker] = tracker_info
        print info
        return info

    def _get_udp_info(self, host, port):
        host = socket.gethostbyname(host)
        connection_id = self._get_udp_connection(host, port)
        if connection_id is None:
            return {}
        data = self._get_udp_scrape_data(host, port, connection_id)
        if data is None:
            return {}

        seeds, complete, leeches = data
        return {'seeds': seeds, 'leeches': leeches, 'complete': complete}

    def _get_http_info(self, url):
        url += '?info_hash=' + ''.join('%' + c.encode('hex') for c in self.torrent_hash)
        resp = urlopen(url)
        if resp.getcode() != 200:
            # TODO: issue warning here
            print resp.getcode()
            print resp.read()
            return {}
        data = lt.bdecode(resp.read())
        stats = data['files'][self.torrent_hash]
        info = {'seeds': stats['complete'], 'leeches': stats['incomplete'], 'complete': stats['downloaded']}
        return info

    def _get_udp_connection(self, host, port):
        # build connection request payload
        transaction_id = int(randrange(0, 255))
        buff = struct.pack('!q', CONNECTION_ID)
        buff += struct.pack('!i', ACTION_CONNECT)
        buff += struct.pack('!i', transaction_id)

        # send payload and get response
        self._socket.sendto(buff, (host, port))
        try:
            response = self._socket.recv(2048)
        except socket.timeout:
            # TODO: issue warning here
            print "tracker down: %s" % host
            return None
        if len(response) < 16:
            # TODO: issue warning here
            print "wrong response length"
            return None

        # extract response information
        resp_action, resp_transaction_id = struct.unpack_from('!ii', response, 0)
        if transaction_id != resp_transaction_id:
            # TODO: issue warning instead
            raise ValueError('Transaction IDs do not match (req=%d resp=%d)' % (transaction_id, resp_transaction_id))
        if resp_action == ACTION_ERROR:
            error = struct.unpack_from('!s', response, 8)[0]
            # TODO: issue warning instead
            raise RuntimeError('Unable to setup a connection: %s' % error)

        elif resp_action == ACTION_CONNECT:
            connection_id = struct.unpack_from('!q', response, 8)[0]
            return connection_id
        return None

    def _get_udp_scrape_data(self, host, port, connection_id):
        # build scrape request payload
        transaction_id = int(randrange(0, 255))
        buff = struct.pack('!q', connection_id)
        buff += struct.pack('!i', ACTION_SCRAPE)
        buff += struct.pack('!i', transaction_id)
        buff += struct.pack('!20s', self.torrent_hash)

        # send payload and get response
        self._socket.sendto(buff, (host, port))
        try:
            response = self._socket.recv(2048)
        except socket.timeout:
            return None
        if len(response) < 20:
            # TODO: issue warning here
            print "wrong response length"
            return None

        # extract response information
        resp_action, resp_transaction_id = struct.unpack_from('!ii', response, 0)
        if transaction_id != resp_transaction_id:
            # TODO: issue warning instead
            raise ValueError('Transaction IDs do not match (req=%d resp=%d)' % (transaction_id, resp_transaction_id))
        if resp_action == ACTION_ERROR:
            error = struct.unpack_from('!s', response, 8)[0]
            # TODO: issue warning instead
            raise RuntimeError('Unable to get scrape data: %s' % error)

        elif resp_action == ACTION_SCRAPE:
            seeds, complete, leeches = struct.unpack_from('!iii', response, 8)
            return seeds, complete, leeches


if __name__ == '__main__':
    info = TorrentInfo(sys.argv[1])
    print info.get_trackers_info()
