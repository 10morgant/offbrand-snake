import type {
    ImagesRoot,
    LastUpdated,
    Namespace,
    NamespacesRoot,
    PackageInfo,
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

export const fetchNamespacesOptions = (url: string, limit: number, offset: number) => {
    return {
        queryKey: [url, 'namespaces', limit, offset],
        // queryFn: () => fetchNamespaces(url, limit, offset),
        staleTime: 5 * 60 * 1000, // 5 minutes
    }
}

export const fetchNamespaces = async (url: string, limit: number, offset: number): Promise<NamespacesRoot> => {
    const response = await fetch(
        buildUrl(`/api/namespaces`, {url, limit, offset})
    )

    if (!response.ok) {
        throw new Error(
            `Failed to fetch catalog: ${response.status} ${response.statusText}`
        )
    }

    return await response.json()
}

export const fetchNamespaceOptions = (url: string, namespace: string) => {
    return {
        queryKey: [url, 'namespaces', namespace],
        // queryFn: () => fetchNamespace(url, namespace),
        staleTime: 5 * 60 * 1000, // 5 minutes
    }
}

export const fetchNamespace = async (url: string, namespace: string): Promise<Namespace> => {
    const response = await fetch(
        buildUrl(`/api/namespaces/${namespace}`, {url, namespace})
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
