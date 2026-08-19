export interface ArtworkMap {
  poster?: string | null;
  banner?: string | null;
  thumbnail?: string | null;
}

export interface CatalogueEpisodeVariant {
  episode_title: string;
  custom_id?: string | null;
  duration_seconds?: number | null;
}

export interface CatalogueEpisodeGroup {
  content_group: string;
  episode_number: number;
  duration_seconds: number | null;
  artwork: ArtworkMap;
  available_languages: string[];
  variants: Record<string, CatalogueEpisodeVariant>;
}

export interface CatalogueSeason {
  season_number: number;
  title: string | null;
  episodes: CatalogueEpisodeGroup[];
}

export interface CatalogueShow {
  id: string;
  title: string;
  slug: string;
  synopsis: string | null;
  section: string | null;
  categories: string[];
  artwork: ArtworkMap;
  available_languages: string[];
  seasons: CatalogueSeason[];
  trailers: CatalogueEpisodeGroup[];
}

export interface PublishedCatalogue {
  catalogue_version: number;
  generated_at: string;
  total_shows: number;
  total_episodes: number;
  sections: Record<string, CatalogueShow[]>;
  shows: CatalogueShow[];
}

export interface SearchResultItem {
  id: string;
  title: string;
  slug: string;
  section: string | null;
  categories: string[];
  synopsis: string | null;
  languages: string[];
  episode_count: number;
  artwork: ArtworkMap;
  matched_episodes?: string[];
}

export interface SearchResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: SearchResultItem[];
}

export const REFERENCE_CATEGORIES = [
  "adventure", "folk", "friendship", "india", "language",
  "learning", "maths", "music", "nature", "reading",
  "science", "singalong", "stories", "travel", "values"
] as const;

export const REFERENCE_SECTIONS = [
  { key: "featured", title: "Featured Specials" },
  { key: "series", title: "Original Series" },
  { key: "minisodes", title: "Fun Minisodes" },
  { key: "songs", title: "Songs & Rhymes" }
] as const;
