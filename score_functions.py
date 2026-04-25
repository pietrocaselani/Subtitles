from typing import Any
from numpy import clip
from subliminal import Episode, Movie, Subtitle, Video, get_scores

def dexter_2006_compute_score(subtitle: Subtitle, video: Video, **kwargs: Any) -> int:
    if not subtitle_year_score(subtitle, 2006):
        return 1

    return hdtv_compute_score(subtitle, video, **kwargs)

def subtitle_year_score(subtitle: Subtitle, matching_year: int) -> bool:
    subtitle_year = getattr(subtitle, 'year', None)
    if not subtitle_year:
        subtitle_year = getattr(subtitle, 'movie_year', None)

    return subtitle_year and subtitle_year == matching_year

def hdtv_compute_score(subtitle: Subtitle, video: Video, **kwargs: Any) -> int:
    # First compute the base score using the original function
    base_score = subliminal_base_compute_score(subtitle, video, **kwargs)

    if not isinstance(video, Episode):
        return base_score

    scores = get_scores(video)
    max_score = scores['hash']

    subtitle_name = ""

    # Try to get filename from subtitle
    if hasattr(subtitle, 'filename') and subtitle.filename:
        subtitle_name = subtitle.filename.lower()
    elif hasattr(subtitle, 'release_info') and subtitle.release_info:
        subtitle_name = subtitle.release_info.lower()
    elif hasattr(subtitle, 'name') and subtitle.name:
        subtitle_name = subtitle.name.lower()

    # Check for HDTV patterns
    hdtv_patterns = ['hdtv']

    hd_video_patterns = ['720p', '1080p', 'dvdrip']

    for pattern in hdtv_patterns:
        if pattern in subtitle_name.lower():
            bonus = 55
            return min(base_score + bonus, max_score)

    for pattern in hd_video_patterns:
        if pattern in subtitle_name.lower():
            bonus = -55
            return min(base_score + bonus, max_score)

    return base_score


def subliminal_base_compute_score(subtitle: Subtitle, video: Video, **kwargs: Any) -> int:
    """Compute the score of the `subtitle` against the `video`.

    :func:`compute_score` uses the :meth:`Subtitle.get_matches <subliminal.subtitle.Subtitle.get_matches>` method and
    applies the scores (either from :data:`episode_scores` or :data:`movie_scores`) after some processing.

    :param subtitle: the subtitle to compute the score of.
    :type subtitle: :class:`~subliminal.subtitle.Subtitle`
    :param video: the video to compute the score against.
    :type video: :class:`~subliminal.video.Video`
    :return: score of the subtitle.
    :rtype: int

    """

    scores = get_scores(video)
    matches = subtitle.get_matches(video)

    if 'hash' in matches:
        matches &= {'hash'}

    if isinstance(video, Episode):
        if 'title' in matches:
            matches.add('episode')
        if 'series_imdb_id' in matches:
            matches |= {'series', 'year', 'country'}
        if 'imdb_id' in matches:
            matches |= {'series', 'year', 'country', 'season', 'episode'}
        if 'series_tmdb_id' in matches:
            matches |= {'series', 'year', 'country'}
        if 'tmdb_id' in matches:
            matches |= {'series', 'year', 'country', 'season', 'episode'}
        if 'series_tvdb_id' in matches:
            matches |= {'series', 'year', 'country'}
        if 'tvdb_id' in matches:
            matches |= {'series', 'year', 'country', 'season', 'episode'}
    elif isinstance(video, Movie):
        if 'imdb_id' in matches:
            matches |= {'title', 'year', 'country'}
        if 'tmdb_id' in matches:
            matches |= {'title', 'year', 'country'}

    score = int(sum(scores.get(match, 0) for match in matches))

    max_score = scores['hash']
    if not (0 <= score <= max_score):
        score = int(clip(score, 0, max_score))

    return score