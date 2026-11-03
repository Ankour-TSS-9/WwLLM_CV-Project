import cv2

def get_video_fps(video_path, default=24.0):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    if fps is None or fps != fps or fps < 1:
        return default
    return float(fps)


def get_video_frame_count(video_path):
    """Return total frame count without loading frames into memory."""
    cap = cv2.VideoCapture(video_path)
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return count


def get_video_resolution(video_path):
    """Return (width, height) of the video."""
    cap = cv2.VideoCapture(video_path)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return w, h


def read_video(video_path):
    """
    Load entire video into memory as a list of frames.
    Only use this for short clips (< ~5 minutes at 1080p).
    For longer videos use VideoStreamReader instead.
    """
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames


def read_video_batched(video_path, batch_size=500):
    """
    Generator that yields frames in batches without loading the full video.

    Usage:
        for batch_frames, batch_start in read_video_batched(path, batch_size=500):
            # batch_frames : list of frames
            # batch_start  : absolute frame index of batch_frames[0]
            process(batch_frames)

    This keeps memory usage bounded to batch_size frames at a time regardless
    of total video length.
    """
    cap = cv2.VideoCapture(video_path)
    batch = []
    batch_start = 0
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        batch.append(frame)
        idx += 1
        if len(batch) == batch_size:
            yield batch, batch_start
            batch_start = idx
            batch = []
    if batch:
        yield batch, batch_start
    cap.release()


def estimate_ram_gb(video_path):
    """Estimate RAM needed to load the full video into memory (gigabytes)."""
    cap = cv2.VideoCapture(video_path)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w      = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h      = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    bytes_needed = frames * h * w * 3          # BGR uint8
    return round(bytes_needed / (1024 ** 3), 2)


def save_video(ouput_video_frames, output_video_path, fps=24):
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    if not fps or fps < 1:
        fps = 24
    out = cv2.VideoWriter(
        output_video_path,
        fourcc,
        float(fps),
        (ouput_video_frames[0].shape[1], ouput_video_frames[0].shape[0]),
    )
    for frame in ouput_video_frames:
        out.write(frame)
    out.release()

