import {
    ActionIcon,
    Badge,
    Center,
    Code,
    CopyButton,
    EmptyState,
    Flex,
    Group,
    Loader,
    Pagination,
    Paper,
    Select,
    Stack,
    Table,
    Text,
    TextInput,
    Tooltip,
} from "@mantine/core";
import {modals} from "@mantine/modals";
import {useEffect, useMemo, useState} from "react";
import {compareItems, rankings, rankItem} from "@tanstack/match-sorter-utils";
import type {PackageInfo, Version} from "#/logic/types.ts";
import {
    IconAlertSquareRounded,
    IconArrowDown,
    IconArrowUp,
    IconCheck,
    IconCopy,
    IconDownload,
    IconFlask,
    IconInfoCircle,
    IconPackage,
    IconSearch,
    IconTerminal,
} from "@tabler/icons-react";
import {colourTheme} from "#/config/colours.ts";
import {formatBytes, formatDate} from "#/logic/utils.ts";
import {isPreRelease} from "#/logic/version.ts";

const DEFAULT_PAGE_SIZE = 100;
const PAGE_SIZE_OPTIONS = [25, 50, DEFAULT_PAGE_SIZE, 150, 200, 300, 500, 1000];
type SortKey = 'version' | 'variant' | 'created';
type SortDirection = 'asc' | 'desc';

interface Props {
    data?: PackageInfo;
    loading?: boolean
}

const getPageSizeFromUrl = () => {
    if (typeof window === 'undefined') {
        return DEFAULT_PAGE_SIZE;
    }

    const params = new URLSearchParams(window.location.search);
    const rawValue = params.get('page_size');
    const parsed = rawValue === null ? NaN : Number.parseInt(rawValue, 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_PAGE_SIZE;
};

const getSortIcon = (isActive: boolean, direction: SortDirection) => {
    if (!isActive) return null;
    return direction === 'asc' ? <IconArrowUp size={14}/> : <IconArrowDown size={14}/>;
};

const compareVersions = (left: string, right: string): number => {
    return left.localeCompare(right, undefined, {numeric: true, sensitivity: 'base'});
};

const handleDownload = (url?: string) => {
    if (!url || typeof window === 'undefined') {
        return;
    }

    const link = document.createElement('a');
    link.href = url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.download = '';
    document.body.appendChild(link);
    link.click();
    link.remove();
};

const getTotalSize = (version: Version): number => {
    return (version.files ?? []).reduce((total, file) => total + file.size, 0);
};

function VersionDetailsModal({version}: { version: Version }) {
    const sortedFiles = useMemo(
        () => [...(version.files ?? [])].sort((a, b) => a.filename.localeCompare(b.filename)),
        [version.files]
    );
    const pre = isPreRelease(version.version ?? "");

    return (
        <Stack gap="md" >
            <Group gap="xs">
                {pre && (
                    <Badge color="gray" variant="light" leftSection={<IconFlask size={12}/>}>
                        Pre-release
                    </Badge>
                )}
                {version.yanked && (
                    <Badge color="red" variant="light" leftSection={<IconAlertSquareRounded size={12}/>}>
                        Yanked
                    </Badge>
                )}
            </Group>
            {version.yanked && (
                <Text size="sm" c="dimmed">
                    Yanked due to: {version.yanked_reason ?? "unknown"}
                </Text>
            )}
            <Group gap="xl">
                <div>
                    <Text size="xs" c="dimmed">Requires Python</Text>
                    <Code>{version.requires_python || '—'}</Code>
                </div>
                <div>
                    <Text size="xs" c="dimmed">Created</Text>
                    <Text size="sm">{formatDate(version.created_at)}</Text>
                </div>
                <div>
                    <Text size="xs" c="dimmed">Total size</Text>
                    <Text size="sm">{formatBytes(getTotalSize(version))}</Text>
                </div>
                <div>
                    <Text size="xs" c="dimmed">Files</Text>
                    <Text size="sm">{sortedFiles.length}</Text>
                </div>
            </Group>

            <Table striped highlightOnHover>
                <Table.Thead>
                    <Table.Tr>
                        <Table.Th>File</Table.Th>
                        <Table.Th>Type</Table.Th>
                        <Table.Th>Size</Table.Th>
                        <Table.Th>Uploaded</Table.Th>
                        <Table.Th w={70}>Download</Table.Th>
                    </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                    {sortedFiles.map((file) => (
                        <Table.Tr
                            key={file.digest}
                            bg={file.yanked ? "rgba(255, 0, 0, 0.2)" : undefined}
                        >
                            <Table.Td>
                                <Tooltip label={file.filename} withArrow>
                                    <Text ff="monospace" size="sm" truncate="end" maw={540}>
                                        {file.filename}
                                    </Text>
                                </Tooltip>
                            </Table.Td>
                            <Table.Td>
                                <Code>{file.packagetype || '—'}</Code>
                            </Table.Td>
                            <Table.Td>
                                <Text size="sm">{formatBytes(file.size)}</Text>
                            </Table.Td>
                            <Table.Td>
                                <Text size="xs" c="dimmed">{formatDate(file.created_at)}</Text>
                            </Table.Td>
                            <Table.Td>
                                <Tooltip
                                    label={file.url ? 'Download file' : 'No download URL available'}
                                    withArrow
                                    position="top"
                                >
                                    <ActionIcon
                                        color="gray"
                                        variant="subtle"
                                        onClick={() => handleDownload(file.url)}
                                        size="sm"
                                        disabled={!file.url}
                                    >
                                        <IconDownload size={16}/>
                                    </ActionIcon>
                                </Tooltip>
                            </Table.Td>
                        </Table.Tr>
                    ))}
                </Table.Tbody>
            </Table>
        </Stack>
    );
}

export function VersionView({data, loading = false}: Props) {
    const [search, setSearch] = useState('');
    const [pageSize, setPageSize] = useState<number>(() => getPageSizeFromUrl());
    const [page, setPage] = useState(1);
    const [sort, setSort] = useState<{ key: SortKey; direction: SortDirection }>({key: 'version', direction: 'desc'});
    const trimmed = search.trim();

    useEffect(() => {
        if (typeof window === 'undefined') {
            return;
        }

        const nextUrl = new URL(window.location.href);
        if (pageSize === DEFAULT_PAGE_SIZE) {
            nextUrl.searchParams.delete('page_size');
        } else {
            nextUrl.searchParams.set('page_size', pageSize.toString());
        }

        const nextSearch = `${nextUrl.pathname}${nextUrl.search}`;
        if (window.location.pathname + window.location.search !== nextSearch) {
            window.history.replaceState({}, '', nextSearch);
        }
    }, [pageSize]);

    const filteredversions = useMemo(() => {
        if (!data || !data.versions) {
            return []
        }

        const scored = data.versions
            .map((version) => ({
                pkg: version,
                itemRank: rankItem(version.version, trimmed, {threshold: rankings.WORD_STARTS_WITH})
            }))
            .filter((x) => x.itemRank.passed);
        scored.sort((a, b) => compareItems(a.itemRank, b.itemRank));
        return scored.map((x) => x.pkg);
    }, [trimmed, data]);

    const sortedversions = useMemo(() => {
        const items = [...filteredversions];

        items.sort((left, right) => {
            const directionMultiplier = sort.direction === 'asc' ? 1 : -1;

            switch (sort.key) {
                // case 'version':
                //     return compareVersions(left., right.) * directionMultiplier;
                case 'version': {
                    const leftVersion = left.version ?? '';
                    const rightVersion = right.version ?? '';
                    return compareVersions(leftVersion, rightVersion) * directionMultiplier;
                }
                // case 'variant': {
                //     const leftVariant = (left.variants ?? []).join(', ').toLowerCase();
                //     const rightVariant = (right.variants ?? []).join(', ').toLowerCase();
                //     return leftVariant.localeCompare(rightVariant) * directionMultiplier;
                // }
                case 'created': {
                    const leftDate = new Date(left.created_at).getTime();
                    const rightDate = new Date(right.created_at).getTime();
                    return (leftDate - rightDate) * directionMultiplier;
                }
                default:
                    return 0;
            }
        });

        return items;
    }, [filteredversions, sort.direction, sort.key]);

    const totalPages = Math.max(1, Math.ceil(sortedversions.length / pageSize));
    const safePage = Math.min(Math.max(page, 1), totalPages);

    useEffect(() => {
        setPage((current) => Math.min(current, totalPages));
    }, [totalPages]);

    const paginatedversions = useMemo(() => {
        const startIndex = (safePage - 1) * pageSize;
        return sortedversions.slice(startIndex, startIndex + pageSize);
    }, [pageSize, safePage, sortedversions]);

    const handleSort = (key: SortKey) => {
        setSort((current) => {
            if (current.key === key) {
                return {
                    key,
                    direction: current.direction === 'asc' ? 'desc' : 'asc',
                };
            }

            return {
                key,
                direction: key === 'created' ? 'desc' : 'asc',
            };
        });
    };


    const handlePageSizeChange = (value: string | null) => {
        if (!value) {
            return;
        }

        const parsed = Number.parseInt(value, 10);
        if (!Number.isFinite(parsed) || parsed <= 0) {
            return;
        }

        setPageSize(parsed);
        setPage(1);
    };

    const openVersionModal = (version: Version) => {
        modals.open({
            title: (
                <Text fw={600} ff="monospace">
                    {data?.name} {version.version}
                </Text>
            ),
            size: "1200px",
            children: <VersionDetailsModal version={version}/>,
        });
    };

    return (
        <Paper p="md" radius="md" withBorder style={{overflowX: 'auto'}}>
            <Flex justify={"space-between"} align="flex-end" gap="md" pb={10}>
                <Flex gap="md" align="flex-end" wrap="wrap" style={{flex: 1}}>
                    <TextInput
                        value={search}
                        onChange={(event) => {
                            setSearch(event.currentTarget.value);
                            setPage(1);
                        }}
                        leftSection={loading ? <Loader size={14} color="#2496ED"/> :
                            <IconSearch size={16} color={colourTheme.brand}/>}
                        placeholder={"Search..."}
                        disabled={loading}
                    />

                </Flex>
                <Text> {filteredversions.length}/{data?.versions.length ?? 0} versions</Text>
            </Flex>

            <Group justify="space-between" align="center" mt="xs" mb="md">
                <Text size="sm" c="dimmed">
                    Showing {paginatedversions.length > 0 ? (safePage - 1) * pageSize + 1 : 0}-{Math.min(safePage * pageSize, sortedversions.length)} of {sortedversions.length} versions
                </Text>
                <Select
                    value={pageSize.toString()}
                    onChange={handlePageSizeChange}
                    data={PAGE_SIZE_OPTIONS.map((size) => ({value: size.toString(), label: `${size} per page`}))}
                    placeholder="Page size"
                    allowDeselect={false}
                    w={150}
                />
            </Group>

            {sortedversions.length > 1 && (
                <Group justify="center" mb="md">
                    <Pagination total={totalPages} value={safePage} onChange={setPage} size="sm"/>
                </Group>
            )}

            <Table striped highlightOnHover>
                <Table.Thead>
                    <Table.Tr>
                        <Table.Th w={350} onClick={() => handleSort('version')} style={{cursor: 'pointer'}}>
                            <Flex align="center" gap={4}>
                                <Text>version</Text>
                                {getSortIcon(sort.key === 'version', sort.direction)}
                            </Flex>
                        </Table.Th>
                        <Table.Th
                            w={150}
                            // onClick={() => handleSort('version')}
                            style={{cursor: 'pointer'}}
                        >
                            <Flex align="center" gap={4}>
                                <Text>Python version</Text>
                                {/*{getSortIcon(sort.key === 'version', sort.direction)}*/}
                            </Flex>
                        </Table.Th>
                        {/*{SHOW_VARIANTS && (
                            <Table.Th w={100} onClick={() => handleSort('variant')} style={{cursor: 'pointer'}}>
                                <Flex align="center" gap={4}>
                                    <Text>Variant</Text>
                                    {getSortIcon(sort.key === 'variant', sort.direction)}
                                </Flex>
                            </Table.Th>)}*/}
                        {/*<Table.Th>Digest</Table.Th>*/}
                        {/*<Table.Th>Platform(s)</Table.Th>*/}
                        <Table.Th>Files</Table.Th>
                        <Table.Th onClick={() => handleSort('created')} style={{cursor: 'pointer'}}>
                            <Flex align="center" gap={4}>
                                <Text>Created</Text>
                                {getSortIcon(sort.key === 'created', sort.direction)}
                            </Flex>
                        </Table.Th>
                        <Table.Th w={120}>
                            Actions
                        </Table.Th>
                    </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                    {paginatedversions.map((version) => {
                        const pre = isPreRelease(version.version ?? "")
                        const yanked = version.yanked ?? false
                        return (
                            <Table.Tr
                                key={version.id}
                                bg={yanked ? "rgba(255, 0, 0, 0.5)" : undefined}
                            >
                                <Table.Td>
                                    <Group>
                                        <Tooltip label={version.version}>
                                            <Text ff={"monospace"} truncate={"end"}>
                                                {version.version}
                                            </Text>
                                        </Tooltip>
                                        <Tooltip label={"Pre-release version"} withArrow>
                                            <div>
                                                {pre && <IconFlask size={18} color={"gray"}/>}
                                            </div>
                                        </Tooltip>

                                        {yanked && (
                                            <Tooltip label={`Package "yanked" due to: ${version.yanked_reason?? "unknown"}`} withArrow>
                                                <IconAlertSquareRounded />
                                            </Tooltip>
                                        )}
                                    </Group>
                                </Table.Td>
                                <Table.Td>
                                    <Code>{version.requires_python ?? '—'}</Code>
                                </Table.Td>
                                {/*{SHOW_VARIANTS && (<Table.Td>
                                    <VariantBadges variants={version.variants ?? []}
                                                   onclick={(val) => handleVariantversionClick(val)}/>
                                </Table.Td>)}*/}
                                {/*<Table.Td>
                                <Tooltip label={version.digest} withArrow>
                                    <Text size="xs" c="dimmed" ff="monospace" style={{cursor: 'default'}}>
                                        {version.digest !== 'unknown'
                                            ? version.digest.replace('sha256:', 'sha256:').substring(0, 19) + '…'
                                            : '—'}
                                    </Text>
                                </Tooltip>
                            </Table.Td>*/}
                                {/*<Table.Td>
                                    <PlatformBadges platforms={version.platforms}/>
                                </Table.Td>*/}
                                <Table.Td>
                                    <Text size="sm">{version.files.length}</Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="xs" c="dimmed">
                                        {formatDate(version.created_at)}
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Tooltip label="View files" withArrow position="top">
                                        <ActionIcon
                                            color="gray"
                                            variant="subtle"
                                            onClick={() => openVersionModal(version)}
                                            size="sm"
                                        >
                                            <IconInfoCircle size={16}/>
                                        </ActionIcon>
                                    </Tooltip>
                                    <CopyButton value={`${data?.name}==${version.version}`} timeout={2000}>
                                        {({copied, copy}) => (
                                            <Tooltip
                                                label={copied ? 'Copied!' : 'Copy name and version'}
                                                withArrow
                                                position="top"
                                            >
                                                <ActionIcon
                                                    color={copied ? 'teal' : 'gray'}
                                                    variant="subtle"
                                                    onClick={copy}
                                                    size="sm"
                                                >
                                                    {copied ? <IconCheck size={16}/> : <IconCopy size={16}/>}
                                                </ActionIcon>
                                            </Tooltip>
                                        )}
                                    </CopyButton>
                                    <CopyButton
                                        value={`pip install ${data?.name}==${version.version}`}
                                        timeout={2000}
                                    >
                                        {({copied, copy}) => (
                                            <Tooltip
                                                label={copied ? 'Copied!' : 'Copy command'}
                                                withArrow
                                                position="top"
                                            >
                                                <ActionIcon
                                                    color={copied ? 'teal' : 'gray'}
                                                    variant="subtle"
                                                    onClick={copy}
                                                    size="sm"
                                                >
                                                    {copied ? <IconCheck size={16}/> : <IconTerminal size={16}/>}
                                                </ActionIcon>
                                            </Tooltip>
                                        )}
                                    </CopyButton>
                                </Table.Td>
                            </Table.Tr>
                        )
                    })}
                </Table.Tbody>

            </Table>
            {loading && (
                <Center p={40}>
                    <Stack align={"center"}>
                        <Loader color="#2496ED"/>
                        <Text>Loading...</Text>
                    </Stack>
                </Center>
            )}
            {sortedversions.length < 1 && !loading && (
                <EmptyState
                    withIndicatorBackground
                    icon={<IconPackage/>}
                    title="No versions found"
                    pt={40}
                    pb={40}
                >
                    <EmptyState.Description>
                        There are no versions for this image available right now.

                    </EmptyState.Description>
                    <EmptyState.Actions>
                        {/*<Button variant="default">Refresh</Button>*/}
                    </EmptyState.Actions>
                </EmptyState>
            )}

            {sortedversions.length > 1 && (
                <Group justify="center" mt="md">
                    <Pagination total={totalPages} value={safePage} onChange={setPage} size="sm"/>
                </Group>
            )}

        </Paper>
    )
}