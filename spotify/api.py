from base64 import b64encode
from typing import Any, Optional, Union
from urllib.parse import urlencode, urlunparse

import requests
import typedjson

from .models import Track, User, Playlist


class Spotify:
    def __init__(self, client_id: str, client_secret: str) -> None:
        self.host = "https://api.spotify.com"
        self.api_version = "v1"
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = requests.Session()

    def _get_token(self, client_id: str, client_secret: str) -> str:
        encoded_code = b64encode(f"{client_id}:{client_secret}".encode()).decode()
        headers = {"Authorization": f"Basic {encoded_code}"}
        params = {"grant_type": "client_credentials"}
        response = requests.post(
            "https://accounts.spotify.com/api/token", headers=headers, data=params
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._get_token(self.client_id, self.client_secret)}",
        }
        return headers

    def _get(self, session: requests.Session, url: str) -> Any:
        response = session.get(url)
        response.raise_for_status()
        return response.json()

    def update_token(self) -> None:
        self.session.headers.update(self._get_headers())

    def _make_params(self, **kwargs: Union[str, int]) -> dict[str, Union[str, int]]:
        params = {}
        for key, value in kwargs.items():
            if value is None:
                continue
            params[key] = value
        return params

    def _make_url(
        self,
        path: str,
        query: Optional[dict[str, Union[str, int]]] = None,
    ) -> str:
        scheme, netloc = self.host.split("://")
        query_str = "" if query is None else urlencode(query)
        url_parts = (scheme, netloc, path, "", query_str, "")
        return urlunparse(url_parts)

    def _get_tracks_from_playlist(
        self, url, items: Optional[tuple[str, str]] = None
    ) -> list[tuple[str, str]]:
        if items is None:
            items = []

        response_json = self._get(self.session, url)

        track_items = [
            (track["track"]["id"], track["added_by"]["id"])
            for track in response_json["items"]
        ]

        items.extend(track_items)
        next_url = response_json["next"]
        if next_url is None:
            return items
        return self._get_tracks_from_playlist(next_url, items)

    def get_tracks_from_playlist(
        self,
        playlist_id: str,
        fields: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        market: str = "JP",
        additional_types: Optional[str] = None,
    ) -> list[tuple[str, str]]:
        """
        Default Value
        limit: 100
        offset: 0
        additional_types: track
        """
        endpoint = f"/{self.api_version}/playlists/{playlist_id}/tracks"
        params = self._make_params(
            market=market,
            fields=fields,
            limit=limit,
            offset=offset,
            additional_types=additional_types,
        )

        url = self._make_url(endpoint, params)
        self.update_token()
        return self._get_tracks_from_playlist(url)

    def get_user(self, user_id: str) -> User:
        endpoint = f"/{self.api_version}/users/{user_id}"
        url = self._make_url(endpoint)
        response_json = self._get(self.session, url)
        return typedjson.decode(User, response_json)

    def get_track(self, track_id: str) -> Track:
        endpoint = f"/{self.api_version}/tracks/{track_id}"
        url = self._make_url(endpoint)
        response_json = self._get(self.session, url)
        return typedjson.decode(Track, response_json)

    def get_playlist(self, playlist_id: str) -> Playlist:
        endpoint = f"/{self.api_version}/playlists/{playlist_id}"
        url = self._make_url(endpoint)
        response_json = self._get(self.session, url)
        return typedjson.decode(Playlist, response_json)
