from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Image:
    height: Optional[int]
    width: Optional[int]
    url: str


@dataclass(frozen=True)
class Artist:
    external_urls: dict[str, str]
    href: str
    id: str
    name: str
    type: str
    uri: str


@dataclass(frozen=True)
class Album:
    album_type: str
    artists: list[Artist]
    available_markets: list[str]
    external_urls: dict[str, str]
    href: str
    id: str
    images: list[Image]
    name: str
    release_date: str
    release_date_precision: str
    total_tracks: int
    type: str
    uri: str


@dataclass(frozen=True)
class Track:
    album: Album
    artists: list[Artist]
    available_markets: list[str]
    disc_number: int
    duration_ms: int
    explicit: bool
    external_ids: dict[str, str]
    external_urls: dict[str, str]
    href: str
    id: str
    is_local: bool
    name: str
    popularity: int
    preview_url: str
    track_number: int
    type: str
    uri: str


@dataclass(frozen=True)
class Followers:
    href: Optional[str]
    total: int


@dataclass(frozen=True)
class User:
    display_name: str
    external_urls: dict[str, str]
    followers: Followers
    href: str
    id: str
    images: list[Image]
    type: str
    uri: str
