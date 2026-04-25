import fs from "fs";
import { guessit } from "guessit-js";
import mi from "mediainfo-wrapper";
import fetch from "node-fetch";
import OS from "opensubtitles-api";
import path from "path";

// ================= CONFIG =================

const USER_AGENT = "Subtitles Uploader";

const VIDEO_EXTS = [".mkv", ".mp4", ".avi", ".mov"];

function createOSClient(config) {
  return new OS({
    useragent: USER_AGENT,
    username: config.opensubtitles.username,
    password: config.opensubtitles.password,
    ssl: true,
  });
}

function loadConfig(configPath) {
  if (!configPath) {
    console.error("Uso: node subtitles_uploader.js <directory> <config.json>");
    process.exit(1);
  }

  if (!fs.existsSync(configPath)) {
    console.error("Arquivo de config não encontrado:", configPath);
    process.exit(1);
  }

  const raw = fs.readFileSync(configPath, "utf-8");

  try {
    const config = JSON.parse(raw);

    if (!config.opensubtitles?.username || !config.opensubtitles?.password) {
      throw new Error("Missing OpenSubtitles credentials");
    }

    if (!config.tmdb_api) {
      throw new Error("Missing TMDB API key");
    }

    return config;
  } catch (e) {
    console.error("Erro ao ler config:", e.message);
    process.exit(1);
  }
}

function parseDuration(value) {
  if (value.includes(":")) {
    const parts = value.split(":").map(parseFloat);

    if (parts.length === 3) {
      return Math.floor(
        parts[0] * 3600000 + parts[1] * 60000 + parts[2] * 1000,
      );
    }
  }

  return Math.floor(parseFloat(value));
}

async function getMediaInfo(file) {
  try {
    const md = await mi(file);

    if (!md || !md[0]) return {};

    const general = md[0].general || {};
    const video = md[0].video?.[0] || {};

    let duration = null;
    let fps = null;
    let frameCount = null;

    if (general.duration?.[0]) {
      duration = parseDuration(general.duration[0]);
    } else if (video.duration?.[0]) {
      duration = parseDuration(video.duration[0]);
    }

    if (video.frame_rate?.[0]) {
      fps = parseFloat(video.frame_rate[0]);
    } else if (video.original_frame_rate?.[0]) {
      fps = parseFloat(video.original_frame_rate[0]);
    }

    if (video.frame_count?.[0]) {
      frameCount = parseInt(video.frame_count[0]);
    } else if (video.number_of_frames?.[0]) {
      frameCount = parseInt(video.number_of_frames[0]);
    }

    if (!frameCount && fps && duration) {
      frameCount = Math.round((duration / 1000) * fps);
    }

    const width = video.width?.[0] ? parseInt(video.width[0]) : null;
    const height = video.height?.[0] ? parseInt(video.height[0]) : null;

    return {
      movietimems: duration,
      moviefps: fps,
      movieframes: frameCount,
      width,
      height,
    };
  } catch (err) {
    console.error("MediaInfo falhou:", err.message);
    return {};
  }
}

function buildKey({ subtitle, data }) {
  const imdb = data?.IDMovieImdb || "null";
  const subName = path.basename(subtitle);
  return `${imdb}|${subName}`;
}

function loadCache(logFile) {
  const uploaded = new Set();

  if (!fs.existsSync(logFile)) return uploaded;

  const lines = fs.readFileSync(logFile, "utf-8").split("\n");

  for (const line of lines) {
    if (!line.trim()) continue;

    try {
      const data = JSON.parse(line);

      if (data.success) {
        uploaded.add(buildKey(data));
      }
    } catch {}
  }

  return uploaded;
}

function appendLog(entry, logFile) {
  fs.appendFileSync(logFile, JSON.stringify(entry) + "\n");
}

function appendFailure(entry, logFile) {
  fs.appendFileSync(logFile, JSON.stringify(entry) + "\n");
}

function findPairs(root) {
  const pairs = [];

  function walk(dir) {
    const files = fs.readdirSync(dir);

    for (const file of files) {
      const full = path.join(dir, file);
      const stat = fs.statSync(full);

      if (stat.isDirectory()) {
        walk(full);
        continue;
      }

      const ext = path.extname(file).toLowerCase();

      if (!VIDEO_EXTS.includes(ext)) continue;

      const stem = path.basename(file, ext);

      const subs = fs
        .readdirSync(dir)
        .filter((f) => f.startsWith(stem) && f.endsWith(".srt"));

      if (!subs.length) continue;

      let chosen =
        subs.find((s) => s.includes("pt-BR") || s.includes("pob")) || subs[0];

      pairs.push({
        video: full,
        subtitle: path.join(dir, chosen),
      });
    }
  }

  walk(root);
  return pairs;
}

// ---------- UPLOAD ----------

async function buildArgs(
  os,
  videoPath,
  subPath,
  parsed,
  releaseName,
  mediaDetails,
) {
  const hashData = await os.hash(videoPath);
  const media = await getMediaInfo(videoPath);

  const imdbid = fetchImdbId(mediaDetails);

  if (!imdbid) {
    console.log(
      `Could not fetch imdb id for ${videoPath}. Uploading without imdb id.`,
    );
  }

  return {
    sublanguageid: "pob",
    subpath: subPath,
    path: videoPath,

    imdbid: imdbid?.replace("tt", ""),

    moviehash: hashData.moviehash,
    moviebytesize: hashData.moviebytesize,

    movieaka: mediaDetails.title || mediaDetails.name,
    movietimems: media.movietimems,
    moviefps: media.moviefps,
    movieframes: media.movieframes,

    moviereleasename: releaseName,

    highdefinition: media.height >= 720,

    automatictranslation: "0",
    subauthorcomment: "Créditos mantidos",
    hearingimpaired: "0",
    subtranslator: "",
  };
}

async function fetchMovieDetails(apiKey, title, year) {
  const query = encodeURIComponent(title);

  const url = `https://api.themoviedb.org/3/search/movie?api_key=${apiKey}&query=${query}&year=${year}`;

  const res = await fetch(url);
  const data = await res.json();

  if (!data.results?.length) return null;

  const movie = data.results[0];

  const detailsUrl = `https://api.themoviedb.org/3/movie/${movie.id}?api_key=${apiKey}&append_to_response=external_ids`;

  const detailsRes = await fetch(detailsUrl);
  return await detailsRes.json();
}

async function fetchEpisodeDetails(apiKey, title, year, season, episode) {
  const query = encodeURIComponent(title);

  const url = `https://api.themoviedb.org/3/search/tv?api_key=${apiKey}&query=${query}&year=${year}`;

  const res = await fetch(url);
  const data = await res.json();

  if (!data.results?.length) return null;

  const show = data.results[0];

  const showId = show.id;

  const detailsUrl = `https://api.themoviedb.org/3/tv/${showId}/season/${season}/episode/${episode}?api_key=${apiKey}&append_to_response=external_ids`;

  const detailsResponse = await fetch(detailsUrl);
  const details = await detailsResponse.json();

  return details;
}

async function fetchTmdbDetails(apiKey, parsed) {
  const title = Array.isArray(parsed.title) ? parsed.title[0] : parsed.title;
  const year = parsed.year;

  const mediaType = parsed.type;

  if (mediaType === "movie") {
    return fetchMovieDetails(apiKey, title, year);
  } else if (mediaType === "episode") {
    return fetchEpisodeDetails(
      apiKey,
      title,
      year,
      parsed.season,
      parsed.episode,
    );
  }

  return null;
}

async function getMediaDetailsAndParsed(apiKey, videoPath) {
  const pathsToTry = [videoPath, path.dirname(videoPath)];

  for (const currentPath of pathsToTry) {
    const parsed = parseFilename(currentPath);
    const mediaDetails = await fetchTmdbDetails(apiKey, parsed);
    const imdbid = fetchImdbId(mediaDetails);

    if (mediaDetails && imdbid) {
      return { parsed, releaseNamePath: currentPath, mediaDetails };
    }
  }

  const parsed = parseFilename(videoPath);
  return { parsed, releaseNamePath: videoPath, mediaDetails: null };
}

async function upload(videoPath, subPath, os, config) {
  // In upload function:
  const {
    parsed: validParsed,
    releaseNamePath,
    mediaDetails,
  } = await getMediaDetailsAndParsed(config.tmdb_api, videoPath);

  if (!mediaDetails || !fetchImdbId(mediaDetails)) {
    console.log(
      `Skipping upload for ${videoPath}: Could not fetch media details or IMDB ID.`,
    );
    return {
      success: false,
      error: "Missing media details or IMDB ID",
    };
  }

  const releaseName = path.basename(releaseNamePath);

  const args = await buildArgs(
    os,
    videoPath,
    subPath,
    validParsed,
    releaseName,
    mediaDetails,
  );

  try {
    const result = await os.upload(args);

    return {
      success: true,
      ...result,
    };
  } catch (e) {
    return {
      success: false,
      error: e.message,
    };
  }
}

function classifyResult(result) {
  if (!result || result.success === false) {
    return {
      ok: false,
      uploaded: false,
      reason: result?.error || "unknown_error",
    };
  }

  if (result.alreadyindb === 1) {
    return {
      ok: true,
      uploaded: false,
      reason: "already_in_db",
    };
  }

  return {
    ok: true,
    uploaded: true,
    reason: "uploaded",
  };
}

function parseFilename(filePath) {
  const name = path.basename(filePath);
  return guessit(name);
}

function fetchImdbId(tmdbMedia) {
  if (tmdbMedia) {
    return tmdbMedia.external_ids?.imdb_id || tmdbMedia.imdb_id || null;
  }

  return null;
}

async function main(root, config) {
  const os = createOSClient(config);

  const logFile = config.upload_results_path;
  const logFileFails = config.upload_fails_path;

  const cache = loadCache(logFile);

  const pairs = findPairs(root);

  console.log(`Encontrados ${pairs.length} pares de vídeo e legenda.\n`);

  for (const { video, subtitle } of pairs) {
    console.log(`---\n${path.basename(video)}`);

    const subName = path.basename(subtitle);

    const alreadyUploaded = [...cache].some((k) => k.endsWith(`|${subName}`));

    if (alreadyUploaded) {
      console.log("Pulando (cache):", subtitle);
      continue;
    }

    const result = await upload(video, subtitle, os, config);

    console.log(JSON.stringify(result, null, 2));

    const entry = {
      video,
      subtitle,
      ...result,
      timestamp: Date.now(),
    };

    const status = classifyResult(result);
    entry.status = status.reason;

    if (status.ok) {
      appendLog(entry, logFile);

      const key = buildKey(entry);
      cache.add(key);
    } else {
      appendFailure(entry, logFileFails);
    }
  }

  console.log(`Fim do upload dos ${pairs.length} pares de vídeo e legenda.\n`);
}

function resolveConfigPath(inputPath) {
  if (inputPath) return inputPath;

  const home = process.env.HOME || process.env.USERPROFILE;

  if (!home) {
    console.error("Não foi possível determinar o diretório home do usuário");
    process.exit(1);
  }

  return path.join(home, ".config", "subtitles", "config.json");
}

const root = process.argv[2];
const configPathArg = process.argv[3];

const configPath = resolveConfigPath(configPathArg);

if (!root) {
  console.log("Uso: node subtitles_uploader.mjs <directory> [config.json]");
  process.exit(1);
}

const config = loadConfig(configPath);

await main(root, config);
