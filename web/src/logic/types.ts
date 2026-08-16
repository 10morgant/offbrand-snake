export type ViewType = "grid" | "list"

export interface ImagesRoot {
    total: number
    limit: number
    offset: number
    items: PackageInfo[]
}

export interface SearchRoot {
    packages: PackageInfo[]
}


export type RootProjecturls = Record<string, string>

export interface Version {
    id: number;
    package_id: number;
    version: string;
    digest: string;
    size: number;
    created_at: string;
    requires_python: string;
    packagetype: string;
    filename: string;
    yanked: boolean;
    yanked_reason?: string;
}

export interface PackageInfo {
    author: string;
    author_email: string;
    bugtrack_url: string | null;
    classifiers: string[];
    description: string;
    description_content_type: string;
    docs_url: string | null;
    download_url: string | null;
    dynamic: string | null;
    home_page: string | null;
    keywords: string | null;
    license: string;
    license_expression: string | null;
    license_files: string[];
    maintainer: string | null;
    maintainer_email: string | null;
    name: string;
    package_url: string;
    platform: string | null;
    project_url: string;
    project_urls: RootProjecturls;
    provides_extra: string[];
    release_url: string;
    requires_dist: string[];
    requires_python: string;
    summary: string;
    version: string;
    versions: Version[];
    yanked: boolean;
}

export interface Stats {
    packages: number
    versions: number
}

export interface Registry {
    display_name: string
    url: string
    self_hosted: boolean
}

export interface LastUpdated {
    timestamp: string
}
