import type {
    ImagesRoot,
    LastUpdated,
    PackageInfo,
    PackageRequirement,
    PackageRoot,
    Registry,
    SearchRoot,
    Stats
} from "#/logic/types.ts";
import {buildUrl} from "#/logic/utils.ts";
import type {UseQueryOptions} from "@tanstack/react-query";

export const fetchLastUpdatedOptions = (): UseQueryOptions<LastUpdated> => {
    return {
        queryKey: ['last-updated'],
        queryFn: () => fetchLastUpdated(),
        staleTime: 1 * 60 * 1000, // 5 minutes
    }
}

export const fetchLastUpdated = async (): Promise<LastUpdated> => {
    const response = await fetch(
        buildUrl(`/api/last-updated`)
    )

    if (!response.ok) {
        throw new Error(
            `Failed to fetch catalog: ${response.status} ${response.statusText}`
        )
    }

    return await response.json()
}

export const fetchRegistriesOptions = () => {
    return {
        queryKey: ['registries'],
        queryFn: () => fetchRegistries(),
        staleTime: 5 * 60 * 1000, // 5 minutes
    }
}

export const fetchRegistries = async (): Promise<Registry[]> => {
    const response = await fetch(
        buildUrl(`/api/registries`)
    )

    if (!response.ok) {
        throw new Error(
            `Failed to fetch catalog: ${response.status} ${response.statusText}`
        )
    }

    return await response.json()
}

export const fetchPackagesOptions = (limit: number, offset: number) => {
    return {
        queryKey: ['packages', limit, offset],
        queryFn: () => fetchPackages(limit, offset),
        staleTime: 5 * 60 * 1000, // 5 minutes
    }
}

export const fetchPackages = async (limit: number, offset: number): Promise<PackageRoot> => {
    const response = await fetch(
        buildUrl(`/api/package/`, {limit, offset})
    )

    if (!response.ok) {
        throw new Error(
            `Failed to fetch packages: ${response.status} ${response.statusText}`
        )
    }

    return await response.json()
}

export const fetchDepsOptions = (pack: string) => {
    return {
        queryKey: ['package', pack, "readme"],
        queryFn: () => fetchDeps(pack),
        staleTime: 5 * 60 * 1000, // 5 minutes
    }
}

export const fetchDeps = async (pack: string): Promise<PackageRequirement[]> => {
    const response = await fetch(
        buildUrl(`/api/package/${pack}/deps`)
    )

    if (!response.ok) {
        throw new Error(
            `Failed to fetch catalog: ${response.status} ${response.statusText}`
        )
    }

    return await response.json()
}

export const fetchPackageMarkdownOptions = (url: string, pack: string) => {
    return {
        queryKey: [url, 'package', pack, "readme"],
        queryFn: () => fetchPackageMarkdownImage(url, pack),
        staleTime: 5 * 60 * 1000, // 5 minutes
    }
}

export const fetchPackageMarkdownImage = async (url: string, pack: string): Promise<string> => {
    const response = await fetch(
        buildUrl(`/api/package/${pack}/readme`)
    )

    if (!response.ok) {
        if (response.status === 404) {
            throw new Error(`Package ${pack} not found`)
        }
        throw new Error(
            `Failed to fetch catalog: ${response.status} ${response.statusText}`
        )
    }

    return await response.json()
}

export const fetchPackageOptions = (url: string, pack: string) => {
    return {
        queryKey: [url, 'package', pack],
        queryFn: () => fetchPackageImage(url, pack),
        staleTime: 5 * 60 * 1000, // 5 minutes
    }
}

export const fetchPackageImage = async (url: string, pack: string): Promise<PackageInfo> => {
    const response = await fetch(
        buildUrl(`/api/package/${pack}`)
    )

    if (!response.ok) {
        if (response.status === 404) {
            throw new Error(`Package ${pack} not found`)
        }
        throw new Error(
            `Failed to fetch catalog: ${response.status} ${response.statusText}`
        )
    }

    return await response.json()
}

export const fetchImagesOptions = (url: string, limit: number, offset: number) => {
    return {
        queryKey: [url, 'images', limit, offset],
        // queryFn: () => fetchImages(url, limit, offset),
        staleTime: 5 * 60 * 1000, // 5 minutes
    }
}

export const fetchImages = async (url: string, limit: number, offset: number): Promise<ImagesRoot> => {
    const response = await fetch(
        buildUrl(`/api/images`, {url, limit, offset})
    )

    if (!response.ok) {
        throw new Error(
            `Failed to fetch catalog: ${response.status} ${response.statusText}`
        )
    }

    return await response.json()
}

export const fetchStatsOptions = (url: string) => {
    return {
        queryKey: [url, 'stats'],
        queryFn: () => fetchStats(url),
        staleTime: 5 * 60 * 1000, // 5 minutes
    }
}

export const fetchStats = async (url: string): Promise<Stats> => {
    const response = await fetch(
        buildUrl(`/api/stats/`)
    )

    if (!response.ok) {
        throw new Error(
            `Failed to fetch catalog: ${response.status} ${response.statusText}`
        )
    }

    return await response.json()
}

export const fetchSearchOptions = (url: string, q: string) => {
    return {
        queryKey: [url, 'search', q],
        queryFn: () => fetchSearch(url, q),
        staleTime: 1 * 60 * 1000,
    }
}

export const fetchSearch = async (url: string, q: string): Promise<SearchRoot> => {
    const response = await fetch(
        buildUrl(`/api/search/`, {url, q})
    )

    if (!response.ok) {
        throw new Error(
            `Failed to fetch catalog: ${response.status} ${response.statusText}`
        )
    }

    return await response.json()
}
