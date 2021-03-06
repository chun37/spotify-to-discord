import logging
import os
import time
from argparse import ArgumentParser
from dataclasses import asdict
from enum import Enum

from discord_webhook import DiscordEmbed, DiscordWebhook
from dotenv import load_dotenv

from spotify import Spotify, Track, User

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s][%(asctime)s] %(module)s:%(lineno)d: %(message)s",
)
logger = logging.getLogger(__name__)


class NotifyType(Enum):
    ADD = "added new song"
    REMOVE = "removed the song"


class SpotifyToDiscord:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        webhook_url: str,
        playlist_id: str,
        interval: int = 60,
    ):
        self.spotify_api = Spotify(client_id, client_secret)
        self.webhook_url = webhook_url
        self.playlist_id = playlist_id
        self.interval = interval

    def _create_embed(
        self, track: Track, user: User, notify_type: NotifyType
    ) -> DiscordEmbed:
        embed = DiscordEmbed(title=notify_type.value.capitalize())

        artist_names = ", ".join(artist.name for artist in track.artists)

        user_link = f"https://open.spotify.com/user/{user.id}"
        user_hyperlink = f"[{user.display_name}]({user_link})"

        track_link = f"https://open.spotify.com/track/{track.id}"
        track_hyperlink = f"[{track.name}]({track_link})"

        playlist_link = f"https://open.spotify.com/playlist/{self.playlist_id}"
        description = f"__{track_hyperlink}__ - {artist_names}\n{notify_type.value.split()[0]} by {user_hyperlink}\n{playlist_link}"

        embed.set_description(description)
        if track.album.images:
            embed.set_thumbnail(url=track.album.images[0].url)

        return embed

    def _send_webhook(self, track: Track, user: User, notify_type: NotifyType) -> None:
        webhook = DiscordWebhook(url=self.webhook_url)
        embed = self._create_embed(track, user, notify_type)
        webhook.add_embed(embed)
        webhook.execute()

    def _get_tracks_data(self) -> list[tuple[str, str]]:
        return self.spotify_api.get_tracks_from_playlist(
            self.playlist_id,
            fields="items(added_by.id,track.id),next",
        )

    def start(self) -> None:
        before_tracks = None
        loop_count = 0
        while True:
            # 1時間しかトークンが持たない><
            # 30分に1回くらい更新しとけばえかろ
            if loop_count % (self.interval // 2) == 0:
                self.spotify_api.update_token()

            if before_tracks is None:
                before_tracks = set(self._get_tracks_data())
                time.sleep(self.interval)

            after_tracks = set(self._get_tracks_data())

            added_tracks = after_tracks - before_tracks
            for track_id, user_id in added_tracks:
                track = self.spotify_api.get_track(track_id)
                user = self.spotify_api.get_user(user_id)
                logger.info('added "%s" from %s', asdict(track), asdict(user))
                self._send_webhook(track, user, NotifyType.ADD)

            deleted_tracks = before_tracks - after_tracks
            for track_id, user_id in deleted_tracks:
                track = self.spotify_api.get_track(track_id)
                user = self.spotify_api.get_user(user_id)
                logger.info('deleted "%s" from %s', asdict(track), asdict(user))
                self._send_webhook(track, user, NotifyType.REMOVE)

            before_tracks = after_tracks
            time.sleep(self.interval)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Notify Discord when a song is added or removed from your Spotify playlist."
    )
    parser.add_argument("playlist_id", help="The Playlist ID you want to monitor")
    args = parser.parse_args()

    s = SpotifyToDiscord(
        os.environ["SPOTIFY_CLIENT_ID"],
        os.environ["SPOTIFY_CLIENT_SECRET"],
        os.environ["DISCORD_WEBHOOK_URL"],
        args.playlist_id,
    )
    s.start()
