# -*- coding: utf-8 -*-

import json
import logging
import typing
import requests
from http import HTTPStatus

# https://developer.spotify.com/console/get-search-item/
# https://developer.spotify.com/documentation/web-api/reference/#/operations/add-tracks-to-playlist


def _prepare_header(h: dict[str, str], /, *, jwt: str = ""):
    if jwt:
        h['Authorization'] = f'Bearer {jwt}'
    h['Content-Type'] = 'application/json'


def create_playlist(
    name: str,
    user_id: str,
    jwt: str,
    *,
    description: str = "playlist generated"
) -> str | None:
    """
    Search or create a new playlist and return its id
    """
    p = playlists(jwt=jwt)

    playlist_id: str = ""
    if p:
        for i in p:
            if i["name"] == name:
                return i["id"]

    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"

    headers = {}
    _prepare_header(headers, jwt=jwt)

    data = {
        "name": name,
        "description": description,
        "public": "False",
    }

    response = requests.post(url=url, json=data, headers=headers)

    if response.status_code != HTTPStatus.CREATED:
        logging.error(f"Status {response.status_code}: {response.text}")
        return None

    return json.loads(response.text)["id"]


def search_track(name: str, jwt: str) -> str | None:
    """
    Should return the track id if there's some track that seems to be equal this one.
    It also returns the proximity between the original name and the searched one.
    """

    url = "https://api.spotify.com/v1/search"

    headers = {}
    _prepare_header(headers, jwt=jwt)

    params = {
        "q": name,
        "type": "track",
        "market": "ES",
        "limit": 1,
        "offset": 0,
    }
    response = requests.get(url=url, params=params, headers=headers)

    if response.status_code != HTTPStatus.OK:
        logging.error(f"Status {response.status_code}: {response.text}")
        return None

    tracks: dict[str, typing.Any] = json.loads(
        response.text).get("tracks", None)

    if not tracks:
        logging.error("fail to find tracks")
        return None

    items: list[typing.Any] = tracks.get("items", [])
    if not items:
        logging.error(f"didn't find track {name}")
        return None

    return items[0]["id"]


def add_track_playlist(playlist_id: str, tracks_ids: list[str], jwt: str) -> bool:
    """
    Add a given track into a playlist

    See https://developer.spotify.com/documentation/web-api/reference/#/operations/add-tracks-to-playlist
    """

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

    headers = {}
    _prepare_header(headers, jwt=jwt)

    tracks = [f"spotify:track:{t}" for t in tracks_ids]
    data = {
        "uris": ",".join(tracks)
    }
    response = requests.post(url=url, params=data, headers=headers)

    if response.status_code != HTTPStatus.CREATED:
        logging.error(f"Status {response.status_code}: {response.text}")
        return False

    return True


def playlists(jwt: str) -> list[typing.Any] | None:
    """
    Get all user's playlists
    """

    url = "https://api.spotify.com/v1/me/playlists"

    headers = {}
    _prepare_header(headers, jwt=jwt)

    params = {
        "limit": 50,
        "offset": 0,
    }
    response = requests.get(url=url, params=params, headers=headers)
    if response.status_code != HTTPStatus.OK:
        logging.error(f"Status {response.status_code}: {response.text}")
        return None

    r = json.loads(response.text)
    n = r.get("next", None)

    items: list[typing.Any] = r.get("items", [])

    while n:
        response = requests.get(url=n, headers=headers)
        if response.status_code != HTTPStatus.OK:
            logging.error(f"Status {response.status_code}: {response.text}")
            return None
        r = json.loads(response.text)
        n = r.get("next", None)
        items.extend(r.get("items", []))

    return [{"id": p["id"], "name": p["name"]} for p in items]


def user_id(jwt: str) -> str | None:
    """
    Should return the user's id
    """

    url = "https://api.spotify.com/v1/me"

    headers = {}
    _prepare_header(headers, jwt=jwt)

    response = requests.get(url=url, headers=headers)

    if response.status_code != HTTPStatus.OK:
        logging.error("fail to get user's info")
        return None

    return json.loads(response.text)["id"]
