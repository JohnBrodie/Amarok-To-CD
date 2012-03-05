#!/usr/bin/env python

import dbus
import os
import shutil
import sys

from urlparse import urlparse
from urllib import unquote
from subprocess import call, check_call, CalledProcessError

def main():
    # Connect to Amarok.
    try:
        bus = dbus.SessionBus()
    except:
        print "dbus connection failed."
        sys.exit(1)
    try:
        player = dbus.Interface(bus.get_object('org.mpris.amarok', '/Player'),
                                dbus_interface='org.freedesktop.MediaPlayer')
    except:
        print 'Amarok connection failed.'
        sys.exit(1)

    # Get file info from Amarok.
    meta_data = player.GetMetadata()
    track_url = meta_data['location']
    track_name = meta_data['title']
    track_artist = meta_data['artist']

    track_path = urlparse(track_url).path
    track_path = unquote(track_path)

    # Read/create playlist.
    file_path = os.path.expanduser('~/currentCD.m3u')
    f = open(file_path, 'a+')
    music = [line.strip() for line in f]

    # Calculate current playlist size.
    playlist_size = 0
    file_not_found = 0
    for track in music:
        try:
            playlist_size += os.path.getsize(track)/(1024*1024)
        except OSError, e:
            # A file from our playlist was deleted/moved.
            file_not_found += 1

    # Calculate new track's size, determine if we have space remaining.
    track_size = os.path.getsize(track_path)/(1024*1024)
    total_size = playlist_size + track_size
    if total_size >= 700:
        call('notify-send "Playlist Full" "Burning CD with %sMB of mp3s!"'\
                                                            % playlist_size, shell=True)
        f.close()
        f = open(file_path, 'w')
        f.write('%s\n' % track_path)
        f.close()
        burn_cd(music) 
        sys.exit()

    # Write new track to playlist.
    if track_path not in music:
        music.append(track_path)
        f.write('%s\n' % track_path)
        call('notify-send "Playlist Addition" "%s - %s added to playlist.\n Total of %sMB in %s tracks."'\
                        % (track_artist, track_name, total_size, len(music)), shell=True)
        f.close()
    else:
        call('notify-send "Playlist Duplicate" "%s - %s already exists in playlist."'\
                                                    % (track_artist, track_name), shell=True)

def burn_cd(music):
    tmp_dir = os.path.expanduser('~/currentCD/')

    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)

    # Copy all tracks to tmp dir.
    for f in music:
        if os.path.exists(f):
            os.symlink(f, tmp_dir+os.path.basename(f))

    try:
        check_call('genisoimage -f -o ~/currentCD.iso %s' % (tmp_dir), shell=True)
    except CalledProcessError:
        exit(1)
    shutil.rmtree(tmp_dir)

    try:
        check_call('wodim ~/currentCD.iso', shell=True)
    except CalledProcessError:
        call('notify-send "Playlist Error" "Error burning currentCD.iso. Please attempt manually.\n Playlist reset."', shell=True)
        exit(1)
    os.remove(os.path.expanduser('~/currentCD.iso'))

if __name__ == "__main__":
    main()
