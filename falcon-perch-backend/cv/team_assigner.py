import numpy as np
from sklearn.cluster import KMeans
import cv2


class ImprovedTeamAssigner:
    """Jersey colour teams from several frames. No clip-specific ID hacks."""

    def __init__(self):
        self.team_colors = {}
        self.player_team_dict = {}
        self.kmeans = None

    def get_clustering_model(self, image):
        image_2d = image.reshape(-1, 3)
        if len(image_2d) < 2:
            return None
        kmeans = KMeans(n_clusters=2, init="k-means++", n_init=5, random_state=0)
        kmeans.fit(image_2d)
        return kmeans

    def get_player_color(self, frame, bbox):
        x1, y1, x2, y2 = [int(v) for v in bbox]
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 <= x1 or y2 <= y1:
            return None

        image = frame[y1:y2, x1:x2]
        if image.size == 0:
            return None

        # Shirt is usually in the upper-middle of the box, not the head strip
        h_img = image.shape[0]
        top = image[int(h_img * 0.15) : int(h_img * 0.55), :]
        if top.size == 0:
            top = image[0 : max(1, h_img // 2), :]

        lab = cv2.cvtColor(top, cv2.COLOR_BGR2LAB)
        kmeans = self.get_clustering_model(lab)
        if kmeans is None:
            return lab.reshape(-1, 3).mean(axis=0)

        labels = kmeans.labels_.reshape(top.shape[0], top.shape[1])
        corners = [
            labels[0, 0],
            labels[0, -1],
            labels[-1, 0],
            labels[-1, -1],
        ]
        non_player = max(set(corners), key=corners.count)
        player_cluster = 1 - non_player
        return kmeans.cluster_centers_[player_cluster]

    def assign_team_color(self, frames, player_tracks, max_frames=40):
        colors = []
        n = min(len(frames), len(player_tracks), max_frames)
        for frame_num in range(n):
            for _, player in player_tracks[frame_num].items():
                color = self.get_player_color(frames[frame_num], player["bbox"])
                if color is not None:
                    colors.append(color)

        if len(colors) < 4:
            self.team_colors = {1: np.array([0, 0, 255]), 2: np.array([255, 255, 255])}
            self.kmeans = None
            return

        kmeans = KMeans(n_clusters=2, init="k-means++", n_init=10, random_state=0)
        kmeans.fit(np.array(colors))
        self.kmeans = kmeans
        self.team_colors[1] = kmeans.cluster_centers_[0]
        self.team_colors[2] = kmeans.cluster_centers_[1]

    def _bgr_team_color(self, team):
        color = self.team_colors.get(team)
        if color is None:
            return (0, 0, 255) if team == 1 else (255, 255, 255)
        if self.kmeans is None:
            return tuple(int(c) for c in color)
        pixel = np.uint8([[color]])
        bgr = cv2.cvtColor(pixel, cv2.COLOR_LAB2BGR)[0, 0]
        return (int(bgr[0]), int(bgr[1]), int(bgr[2]))

    def _predict_team(self, color):
        if self.kmeans is None or color is None:
            return 1
        team_id = int(self.kmeans.predict(color.reshape(1, -1))[0]) + 1
        return team_id

    def assign_all_players(self, frames, tracks, samples_per_id=6):
        """Majority vote over several appearances per track ID, then freeze."""
        samples = {}
        for key in ("players", "goalkeepers"):
            object_tracks = tracks.get(key, [])
            for frame_num, frame_tracks in enumerate(object_tracks):
                if frame_num >= len(frames):
                    break
                for track_id, info in frame_tracks.items():
                    bucket = samples.setdefault(track_id, [])
                    if len(bucket) >= samples_per_id:
                        continue
                    bbox = info.get("bbox")
                    if not bbox:
                        continue
                    color = self.get_player_color(frames[frame_num], bbox)
                    if color is not None:
                        bucket.append(color)

        for track_id, colors in samples.items():
            if not colors:
                continue
            median = np.median(np.stack(colors), axis=0)
            self.player_team_dict[track_id] = self._predict_team(median)

        for key in ("players", "goalkeepers"):
            for frame_num, frame_tracks in enumerate(tracks.get(key, [])):
                for track_id, info in frame_tracks.items():
                    team = self.player_team_dict.get(track_id)
                    if team is None:
                        bbox = info.get("bbox")
                        color = self.get_player_color(frames[frame_num], bbox) if bbox else None
                        team = self._predict_team(color)
                        self.player_team_dict[track_id] = team
                    info["team"] = team
                    info["team_color"] = self._bgr_team_color(team)
