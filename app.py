import os

from flask import Flask, abort, render_template, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import exists

import models
from models import Base

DATABASE_URL = os.environ['DATABASE_URL']

# engine = create_engine("postgresql://postgres:postgres@localhost:5432/chinook")
engine = create_engine(DATABASE_URL)

db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

Base.query = db_session.query_property()

app = Flask(__name__)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route("/artists", methods=["GET", "PATCH"])
def artists():
    if request.method == "GET":
        return get_artists()
    elif request.method == "PATCH":
        return patch_artist()
    abort(405)


def get_artists():
    artists = db_session.query(models.Artist).order_by(models.Artist.name)
    return "<br>".join(
        f"{idx}. {artist.name}" for idx, artist in enumerate(artists)
    )


# Aaron Goldberg , 202
def patch_artist():
    data = request.json
    artist_id = data.get("artist_id")
    new_name = data.get("name")
    if artist_id is None:
        abort(404)
    artist = (
        db_session.query(models.Artist)
        .filter(models.Artist.artist_id == artist_id)
        .with_for_update()
        .one()
    )
    artist.name = new_name
    db_session.add(artist)
    db_session.commit()
    return "OK"


@app.route("/albums")
def get_albums():
    albums = db_session.query(models.Album).order_by(models.Album.title)
    return render_template("albums.html", albums=albums)


@app.route("/playlists")
def get_playlists():
    playlists = db_session.query(models.Playlist).order_by(
        models.Playlist.name
    )
    return render_template("playlists.html", playlists=playlists)

@app.route("/counter")
def counter():
    c = db_session.query(models.Counter).one()
    c.count += 1
    db_session.commit()
    return str(c.count)

@app.route("/longest_tracks")
def longest_tracks():
    lt = db_session.query(models.Track).order_by(models.Track.milliseconds.desc()).limit(10)
    tracks = []
    for l in lt:
        thisdict =	{
            "album_id": str(l.album_id),
            "bytes": str(l.bytes),
            "composer": str(l.composer),
            "genre_id": str(l.genre_id),
            "media_type_id": str(l.media_type_id),
            "milliseconds": str(l.milliseconds),
            "name": str(l.name),
            "track_id": str(l.track_id),
            "unit_price": str(l.unit_price)
        }
        tracks.append(thisdict)
    return jsonify(tracks)

@app.route("/longest_tracks_by_artist")
def longest_tracks_by_artist():
    artist = request.args.get('artist')
    lt_byartist = db_session.query(models.Track).join(models.Album).join(models.Artist).filter(models.Artist.name == artist).order_by(models.Track.milliseconds.desc()).limit(10)
    tracks = []
    for l in lt_byartist:
        thisdict =	{
            "album_id": str(l.album_id),
            "bytes": str(l.bytes),
            "composer": str(l.composer),
            "genre_id": str(l.genre_id),
            "media_type_id": str(l.media_type_id),
            "milliseconds": str(l.milliseconds),
            "name": str(l.name),
            "track_id": str(l.track_id),
            "unit_price": str(l.unit_price)
        }
        tracks.append(thisdict)
    if tracks == []:
        abort(404)
    return jsonify(tracks)

@app.route("/artists", methods=['POST', 'GET'])
def artistss():
    if request.method != 'POST':
        abort(400)
    if not request.is_json:
        abort(400)

    content = request.json
    newName = content.get("name")
    if newName is None:
        abort(400)
    (ret, ), = db_session.query(exists().where(models.Artist.name==newName))
    if(ret == True):
        abort(400)

    newArtist = models.Artist(name = newName)
    db_session.add(newArtist)
    db_session.commit()

    added = db_session.query(models.Artist).order_by(models.Artist.artist_id.desc()).first()
    result_dict = []
    result_dict.append(added.__dict__)
    print(result_dict)
    for i in result_dict:
        del i['_sa_instance_state']
        dic = list(i.keys())
        for di in dic:
            i[di] = str(i[di])
    if result_dict[0] is None:
        abort(400)
    return jsonify(result_dict[0])

if __name__ == "__main__":
    app.run(debug=False)
