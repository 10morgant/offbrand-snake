import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {Group, Stack, Text} from '@mantine/core';
import {useDebouncedValue} from '@mantine/hooks';
import {IconPackage} from '@tabler/icons-react';
import {useNavigate} from '@tanstack/react-router';
import {SearchCombobox, type SearchGroup} from '../../core/SearchCombobox';
import {useRegistryContext} from "#/context/RegistryContext.tsx";
import {fetchSearchOptions} from "#/logic/queries.ts";


type PackageInfo = {
    name: string;
    version: string;
    desc: string;
};


export function SearchServer() {
    const [search, setSearch] = useState('');
    const [debouncedSearch] = useDebouncedValue(search, 300);
    const navigate = useNavigate();
    const {config} = useRegistryContext();
    const trimmed = search.trim();
    const debouncedTrimmed = debouncedSearch.trim();

    const searchQuery = useQuery({
        ...fetchSearchOptions(config?.url ?? "http://example.com", debouncedTrimmed),
        enabled: Boolean(config && debouncedTrimmed.length > 0),
    })

    const packages: PackageInfo[] = (searchQuery.data?.packages ?? []).map((pack) => {
        const version = "-"
        const desc = pack.summary
        const name = pack.name
        return {name, version, desc};
    });

    const isLoading = search !== debouncedSearch || searchQuery.isFetching;
    const isError = searchQuery.isError;


    // This is the only place that knows Docker has two kinds of results.
    // A packages-only use case would just emit a single group here.
    const groups: SearchGroup[] = [
        {
            label: "Packages",
            options: packages.map((pkg, i) => ({
                value: `${pkg.name}`,
                content: (
                    <Stack key={`im_${i}`} gap={3}>
                        <Group gap={6}>
                            <IconPackage color={"#2560FF"}/>
                            {/*<Highlight highlight={trimmed} size="sm" c="#2496ED">*/}
                            <Text fw={600} c="#e8edf1">{pkg.name}</Text>
                            {/*</Highlight>*/}
                            {/*<Text size="sm" c="#2496ED">{pkg.version}</Text>*/}
                        </Group>
                        <Text size="sm" c="#5a6672">{pkg.desc}</Text>
                    </Stack>
                ),
            })),
        },

    ];

    const handleSubmit = (value: string) => {
        setSearch(value);
        navigate({to: '/project/$pack', params: {pack: value}});
    };

    return (
        <SearchCombobox
            search={search}
            onSearchChange={setSearch}
            onSubmit={handleSubmit}
            groups={groups}
            allowFreeTextSubmit={true}
            isLoading={isLoading}
            isError={isError}
            errorMessage="Couldn't reach server"
            emptyMessage={trimmed ? "No matching images" : "Type to search"}
            placeholder={config ? 'Search pypi packages' : 'Configure registry to search…'}
            disabled={!config}
        />
    );
}