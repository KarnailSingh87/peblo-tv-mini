export interface ArtworkMap {
  poster?: string | null;
  banner?: string | null;
  thumbnail?: string | null;
  [key: string]: string | null | undefined;
}

export interface CatalogueEpisodeVariant {
  language: string;
  episode_id?: string | null;
  episode_title: string;
  duration_seconds?: number | null;
}

export interface CatalogueEpisodeGroup {
  content_group: string;
  episode_number: number;
  title?: string;
  duration_seconds: number | null;
  artwork: ArtworkMap;
  languages?: string[];
  available_languages?: string[];
  variants: CatalogueEpisodeVariant[] | Record<string, CatalogueEpisodeVariant>;
}

export interface CatalogueSeason {
  season_number: number;
  title: string | null;
  episodes: CatalogueEpisodeGroup[];
}

export interface CatalogueShow {
  id: string | number;
  title: string;
  slug: string;
  synopsis: string | null;
  section: string | null;
  categories: string[];
  artwork: ArtworkMap;
  available_languages: string[];
  total_episodes?: number;
  seasons: CatalogueSeason[];
  trailers: CatalogueEpisodeGroup[];
}

export interface CatalogueSectionItem {
  section: string;
  title: string;
  shows: CatalogueShow[];
}

export interface PublishedCatalogue {
  version?: number;
  catalogue_version?: number;
  published_at?: string;
  generated_at?: string;
  total_shows: number;
  total_episodes: number;
  featured?: CatalogueShow | null;
  sections: CatalogueSectionItem[] | Record<string, CatalogueShow[]>;
  shows?: CatalogueShow[];
}

export interface SearchResultItem {
  id: string | number;
  title: string;
  slug: string;
  section: string | null;
  categories: string[];
  synopsis: string | null;
  languages?: string[];
  available_languages?: string[];
  episode_count?: number;
  total_episodes?: number;
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
