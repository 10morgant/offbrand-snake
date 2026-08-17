import {createFileRoute} from '@tanstack/react-router'
import {Container, NumberFormatter, SimpleGrid} from "@mantine/core";
import {Hero} from "#/components/core/Hero.tsx";
import {IconBox, IconFolder} from "@tabler/icons-react";
import {StatCard} from "#/components/core/StatsCards.tsx";
import {useRegistryContext} from "#/context/RegistryContext.tsx";
import {colourTheme} from "#/config/colours.ts";
import {useQuery} from "@tanstack/react-query";
import {fetchStatsOptions} from "#/logic/queries.ts";
import {PackagesView} from "#/components/python/PackagesView.tsx";

export const Route = createFileRoute('/')({component: Home})

function Home() {
    const {config} = useRegistryContext()

    const {data} = useQuery(fetchStatsOptions(config?.url ?? "http://example.com"))

    return (
        <>
            <Hero/>
            <div style={{backgroundColor: colourTheme.brand_dark}}>
                <Container size={1600} pt={40} pb={40}>
                    <SimpleGrid cols={3}>
                        <StatCard
                            icon={<IconFolder size={24}/>}
                            label="Total packages"
                            value={<NumberFormatter value={data?.packages} thousandSeparator/>}
                            loading={false}
                            color="yellow"
                        />
                        <StatCard
                            icon={<IconBox size={24}/>}
                            label="Total versions"
                            value={<NumberFormatter value={data?.versions} thousandSeparator/>}
                            loading={false}
                            color="blue"
                        />
                        <StatCard
                            icon={<IconBox size={24}/>}
                            label="Registry"
                            value={config?.url}
                            loading={false}
                            color="blue"
                        />
                    </SimpleGrid>
                </Container>
            </div>
            <div>
                <Container  pt={40} pb={40}>
                    <PackagesView/>
                </Container>
            </div>

        </>
    )
}
